# Optimal Control Theory 

This repository contais the studied topics in my Scientific Initiation in the
topic. It's based on the book written by Suzanne Lenhart and John T. Workman
called Optimal Control Applied to Biological Models. So it was written notes
in `notes` using this reference in portuguese so as to be a initial reference in the
language. It was also developed in `notebooks` all the laboratories studied in
these notes. 

A class in `optimal_control_class.py` file was developed to deal with all
laboratories, no need to worry with the code, initially. This code contains
the famous method in the area called *forward-backward sweep*. 

In order to use this to your problem, you need to specify: 

- Differential equations of the state variables.
- Differential equations of the adjoint functions, calculated by the necessary
  conditions. 
- A characterization of the optimal control calculation. 

You can also specify bounds if necessary and when the payoff term is linear,
one can pass it as a function. The parameters of the model are dealt as a
dictionary, except the final time and initial condition of the states, that
are separated. These last two parameters are necessary. The notebooks 2, 3, 7,
12 and 13 can be a good reference to start its usage. 