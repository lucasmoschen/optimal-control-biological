#!/usr/bin/env python 

# modules 
import numpy as np
from matplotlib import pyplot as plt
import sympy as sp

class OptimalControl:
    
    def __init__(self, diff_state, diff_lambda, update_u, conv_comb_u = 0.5, 
                 n_controls = 1, n_states = 1, **kwargs):
        '''Resolve o problema de controle ótimo simples, com condição inicial
           do estado e termo payoff linear. Os parâmetros do modelo devem ser
           escritos como params['nome_do_parametro'], pois params deve ser um dicionário.
           - diff_state: função com argumentos (t,x,u,params) que representa a
           derivada do estado x. 
           - diff_lambda: função com argumentos (t,x,u,lambda, params) que representa a
           derivada da função adjunta lambda.
           - update_u: função com argumentos (t,x,lambda,params) que atualiza u através de H_u = 0.
           - conv_comb_u: valor da combinação convexa para atualização de u,
             0.5 por padrão. 
           - n_controls: número de controles, 1 por padrão. 
           - n_states: número de estados, 1 por padrão. 
           - kwargs: parâmetros adicionais 
                - diff_phi: função que determina a condição de transversalidade.
                - bounds: limites sobre o controle.  Deve ser uma lista de
                  tuplas, cada tupla para cada controle. Se são
                  parametrizados, devem ser passados na função solve. 
                - free_adj_final: estados com condições necessárias adicionais,
                  em que o lambda final deve ser estimado. 
        '''
        self.dx = diff_state 
        self.dadj = diff_lambda 
        self.update_u = update_u
        self.coef_u = conv_comb_u

        self.n_states = n_states
        self.n_controls = n_controls

        self.dphi = kwargs.get('diff_phi', lambda x, par: np.zeros(shape = (1, n_states)))
        self.bounds = kwargs.get('bounds', [(-np.inf, np.inf) for i in range(n_controls)]) 
        for b in self.bounds: 
            if b[0] >= b[1]: 
                raise Exception('O formato dos bounds deve ser (a,b), a < b') 
        self.free_adj_final = kwargs.get('free_adj_final', [])

    def _forward(self,t,x,u,params,h): 
        '''A função realiza o processo forward que integra a equação de x' = g
        g: função (t,x,u) 
        u: controle do último passo. vetor de tamanho N + 1
        h: passo a ser dado pelo método de Runge-Kutta 
        '''
        for i in range(len(t)-1):
            k1 = self.dx(t[i],x[i],u[i], params)
            k2 = self.dx(t[i]+h/2,x[i] + 0.5*h*k1, 0.5*(u[i] + u[i+1]), params)
            k3 = self.dx(t[i]+h/2,x[i] + 0.5*h*k2, 0.5*(u[i] + u[i+1]), params)
            k4 = self.dx(t[i]+h,x[i] + h*k3, u[i+1], params)
            x[i+1] = x[i] + (h/6)*(k1 + 2*k2 + 2*k3 + k4)
        return x 

    def _backward(self, t, x, u, lambda_, params,h): 
        '''A função realiza o processo backward que integra a equação de lambda' = -H_x
        dadj: função (t,x,u) com a derivada de lambda. 
        x: estado calculado. Vetor de tamanho N + 1.
        u: controle do último passo. Vetor de tamanho N + 1.
        lambda_: função adjunta do último passo. Vetor de tamanho N + 1. 
        h: passo a ser dado pelo método de Runge-Kutta. 
        '''
        for i in range(len(t)-1,0,-1):
            k1 = self.dadj(t[i],x[i],u[i],lambda_[i], params)
            k2 = self.dadj(t[i]-h/2,0.5*(x[i] + x[i-1]), 0.5*(u[i] + u[i-1]),lambda_[i] - 0.5*h*k1, params)
            k3 = self.dadj(t[i]-h/2,0.5*(x[i] + x[i-1]), 0.5*(u[i] + u[i-1]),lambda_[i] - 0.5*h*k2, params)
            k4 = self.dadj(t[i]-h,x[i-1], u[i-1], lambda_[i] - h*k3, params)
            lambda_[i-1] = lambda_[i] - (h/6)*(k1 + 2*k2 + 2*k3 + k4)
        return lambda_

    def solve(self, x0, T, params, h = 1e-3, tol = 1e-4, bounds = None, theta_list = []): 
        '''
        Retorna o controle ótimo, o estado associado e a função adjunta. 
        - x0: valor inicial do estado 
        - T: tempo final da integração 
        - params: dicionário com os parâmetros do modelo e seus valores. 
        - h: passo no Runge-Kutta
        - tol: tolerância para o erro relativo. 
        - bounds: se os limites são parametrizados, então devem ser passados
          aqui. 
        - theta_list: valores finais da adjunta a ser estimados. O seu uso deve
            ser combinado com um algoritmo de encontrar raízes.  
        '''
        if bounds: 
            self.bounds = bounds
        if len(self.bounds) != self.n_controls: 
            raise Exception('O número de controles deve concordar com o tamanho da lista dos bounds.')
        
        condition = -1 

        N = int(np.round(T/h)) 
        t = np.linspace(0,T,N+1)
        
        # Chute para condição inicial
        u = np.random.beta(a=1000,b=1000, size=(N+1, self.n_controls))
        for k, b in enumerate(self.bounds):   
            if b[0] > -np.inf: 
                if b[1] < np.inf: 
                    u[:,k] = (b[1] - b[0])*u[:,k] + b[0] 
                else: 
                    u[:,k] = u[:,k] + b[0] 
            else: 
                if b[1] < np.inf: 
                    u[:,k] = b[1]*u[:,k] 

        x = np.zeros(shape = (N+1, self.n_states))
        lambda_ = np.zeros(shape = (N+1, self.n_states))

        x[0] = x0

        while condition < 0: 

            u_old = u.copy()
            x_old = x.copy()
            lambda_old = lambda_.copy()

            x = self._forward(t, x, u, params, h)    
            # Condição de transversalidade.None
            lambda_[-1] = self.dphi(x, params)
            lambda_[-1][self.free_adj_final] = theta_list
            lambda_ = self._backward(t, x, u, lambda_, params, h)

            # Update u 
            for i, _ in enumerate(t): 
                tmp = self.update_u(t[i], x[i], lambda_[i], params)
                u[i] = self.coef_u*tmp + (1 - self.coef_u)*u[i]

            cond1 = min(tol*np.sum(abs(u), axis=0) - np.sum(abs(u_old - u), axis=0))
            cond2 = min(tol*np.sum(abs(x), axis=0) - np.sum(abs(x_old - x), axis=0))
            cond3 = min(tol*np.sum(abs(lambda_), axis=0) - np.sum(abs(lambda_old - lambda_), axis=0))

            condition = min(cond1, cond2, cond3) 

        return t,x,u,lambda_

    def plotting(self,t,x,u,lambda_):
        '''Função simples desenvolvida para plot. É um procedimento padrão.'''
        variables = {'x': x, 'u': u, 'lambda': lambda_}
        names = {'x': 'Estado', 'u': 'Controle Ótimo', 'lambda': 'Função Adjunta'}

        _, ax = plt.subplots(3,1,figsize = (10,12)) 

        for i, key in enumerate(variables):
            for k in range(np.shape(variables[key])[1]): 
                ax[i].plot(t,variables[key][:,k], label = key + str(k))
            ax[i].set_title(names[key], fontsize = 15)
            ax[i].grid(linestyle = '-', linewidth = 1, alpha = 0.5)

        return ax       
        
if __name__ == "__main__":

        pass