#!/usr/bin/env python 

# modules 
import numpy as np
from matplotlib import pyplot as plt
import sympy as sp

class OptimalControl:
    
    def __init__(self, diff_state, diff_lambda, update_u, diff_phi = lambda x,par: 0, 
                 h_u = False, conv_comb_u = 0.5):
        '''Resolve o problema de controle ótimo simples, com condição inicial
           do estado e termo payoff. 
           - diff_state: função com argumentos (t,x,u,params) que representa a
           derivada do estado x. 
           - diff_lambda: função com argumentos (t,x,u,lambda, params) que representa a
           derivada da função adjunta lambda.
           - update_u: função que atualiza u através de H_u = 0 
           - diff_phi: função que determina a condição de transversalidade. 
           - h_u: Valor booleano. Se verdadeiro, resolve a equação H_u = 0 de
             forma implícita. 
           - conv_comb_u: valor da combinação convexa para atualização de u
        '''
        self.dx = diff_state 
        self.dadj = diff_lambda 
        self.update_u = update_u
        # Lida com a condição de transversalidade. 
        self.dphi = diff_phi
        self.coef_u = conv_comb_u

    def forward(self,t,x,u,params,h): 
        '''A função realiza o processo forward que integra a equação de x' = g
        g: função (t,x,u) 
        u: controle do último passo. vetor de tamanho N + 1
        h: passo a ser dado pelo método de Runge-Kutta 
        '''
        for i in range(len(t)-1):
            k1 = self.dx(i,x[i],u[i], params)
            k2 = self.dx(i+h/2,x[i] + 0.5*h*k1, 0.5*(u[i] + u[i+1]), params)
            k3 = self.dx(i+h/2,x[i] + 0.5*h*k2, 0.5*(u[i] + u[i+1]), params)
            k4 = self.dx(i+h,x[i] + h*k3, u[i+1], params)
            x[i+1] = x[i] + (h/6)*(k1 + 2*k2 + 2*k3 + k4)
        return x 

    def backward(self, t, x, u, lambda_, params,h): 
        '''A função realiza o processo backward que integra a equação de lambda' = -H_x
        dadj: função (t,x,u) com a derivada de lambda. 
        x: estado calculado. Vetor de tamanho N + 1.
        u: controle do último passo. Vetor de tamanho N + 1.
        lambda_: função adjunta do último passo. Vetor de tamanho N + 1. 
        h: passo a ser dado pelo método de Runge-Kutta. 
        '''
        for i in range(len(t)-1,0,-1):
            k1 = self.dadj(i,x[i],u[i],lambda_[i], params)
            k2 = self.dadj(i-h/2,0.5*(x[i] + x[i-1]), 0.5*(u[i] + u[i-1]),lambda_[i] - 0.5*h*k1, params)
            k3 = self.dadj(i-h/2,0.5*(x[i] + x[i-1]), 0.5*(u[i] + u[i-1]),lambda_[i] - 0.5*h*k2, params)
            k4 = self.dadj(i-h,x[i-1], u[i-1], lambda_[i] - h*k3, params)
            lambda_[i-1] = lambda_[i] - (h/6)*(k1 + 2*k2 + 2*k3 + k4)
        return lambda_


    def solve(self, x0, T, params, h = 1e-3, tol = 1e-4): 
        '''
        Retorna o controle ótimo, o estado associado e a função adjunta. 
        x0: valor inicial do estado 
        T: tempo final da integração 
        params: dicionário com os parâmetros do modelo e seus valores. 
        h: passo no Runge-Kutta
        tol: tolerância para o erro relativo. 
        '''
        condition = -1 

        N = int(np.round(T/h)) 
        t = np.linspace(0,T,N+1)
        u = np.random.normal(scale=0.01, size=N+1)
        x = np.zeros(N+1)
        lambda_ = np.zeros(N+1)

        x[0] = x0

        while condition < 0: 

            u_old = u.copy()
            x_old = x.copy()
            lambda_old = lambda_.copy()

            x = self.forward(t, x, u, params, h)
            # Condição de transversalidade.
            lambda_[-1] = self.dphi(x, params)
            lambda_ = self.backward(t, x, u, lambda_, params, h)

            # Update u 
            u = self.coef_u*self.update_u(t, x, lambda_, params) + (1 - self.coef_u)*u

            cond1 = tol*sum(abs(u)) - sum(abs(u_old - u))
            cond2 = tol*sum(abs(x)) - sum(abs(x_old - x))
            cond3 = tol*sum(abs(lambda_)) - sum(abs(lambda_old - lambda_))

            condition = min(cond1, cond2, cond3) 

        return t,x,u,lambda_

    def plotting(self,t,x,u,lambda_):
        '''Função simples desenvolvida para plot. '''
        variables = {'Estado': x, 'Controle Ótimo': u, 'Função Adjunta': lambda_}

        _, ax = plt.subplots(3,1,figsize = (15,15)) 

        for i, key in enumerate(variables):
            ax[i].plot(t,variables[key])
            ax[i].set_title(key, fontsize = 15)
            ax[i].grid(linestyle = '-', linewidth = 1, alpha = 0.5)

