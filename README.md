# Quantum Algorithm Grand Challenge

# Table of Contents
1. [Overview of Quantum Algorithm Grand Challenge](#Overview)
2. [Introduction](#Introduction)
    - [Background](#Introduction_1)
    - [Model description](#Introduction_2)
    - [NISQ device simulation](#Introduction_3)
3. [Problem description](#problem)
    - [Fermi-Hubbard Model](#problem_1)
    - [Problem statement](#problem_2)
4. [Evaluation](#Evaluation)
5. [Implementation](#Implementation)
6. [How to submit](#Submission)
7. [Description of the Provided Program](#program)
8. [Available Packages](#Packages)
9. [Notes and Prohibited Items](#forbidden)
    - [Notes on Evaluation](#forbidden_1)
    - [Prohibited Items](#forbidden_2)
10. [Terms](#Terms)


# Overview of Quantum Algorithm Grand Challenge <a id="Overview"></a>
Quantum Algorithm Grand Challenge (QAGC) is a global online contest for students, researchers, and others who learn quantum computation and quantum chemistry around the world.

From May 3 to July 31, 2023, participants will solve a problem that focus on the industrial application of the NISQ algorithms.

QAGC web-site:  https://www.qagc.org/

## Awards
- 1st Place - $10,000 + presentation at IEEE Quantum week
- 2nd Place - $5,000 + presentation at IEEE Quantum week
- 3rd Place - $3,000 + presentation at IEEE Quantum week
- 4th Place - presentation at IEEE Quantum week

The top four (teams) will present their algorithms at the workshop hosted by QunaSys at IEEE Quantum Week 2023. It will be held as an in-person event with virtual participation in Bellevue, Washington, USA at the Hyatt Regency Bellevue on Seattle’s Eastside on Sep 17–22, 2023. 

For more information, please visit the IEEE website https://qce.quantum.ieee.org/2023.


# Introduction <a id="Introduction"></a>

As Quantum Computing technology evolves with qubit capacity regularly duplicating, we need to understand how to make better use of Noisy Intermediate-Scale Quantum (NISQ) devices and create algorithms that will enable industrial applications. To identify how to shape the direction for promoting the NISQ algorithm for practical industrial application, it is important to clarify the evaluation criteria to compare the algorithm's performance and define the key factors to take into account. 

We hold a global online contest, the QAGC, to explore practical uses for NISQ devices, visualize bottlenecks in NISQ device utilization, and create a metric for benchmarking the NISQ algorithms.



## Background <a id="Introduction_1"></a>

The materials around us are constructed from molecules and the microscopic behavior is dominated by quantum mechanics. Quantum chemistry is widely used to understand the chemical behavior of these materials in not only academic studies but also material design in industries.

Quantum chemistry is considered one of the most promising fields for considering practical industrial applications of NISQ devices and algorithms.  However, although various NISQ algorithms have been proposed in recent years, it is still far from practical industrial applications. 

For practical industrial applications of NISQ algorithms, it is important to develop new useful NISQ algorithms and define evaluation criteria for accurately comparing the performance of various algorithms and define the key factors to take into account.

Based on these situations, the focuses of QAGC are on the industrial application and defining evaluation criteria for appropriate performance comparison of NISQ algorithms. We have prepared a simulator that reflect the features of NISQ devices and suitable model for the problem to achieve these goals. Below, we will explain each of them.

## Model description <a id="Introduction_2"></a> 

The ground state energy of a molecule is an important quantity for understanding its properties and behavior, and many quantum chemistry studies focus on the ground state energy of individual atoms or molecules. 

In QAGC, the task of participants is to calculate the ground state energy of a model (Hamiltonian) which we have prepared. From the focus of QAGC, the Hamiltonian should have some properties as follows:

- Has similar properties as the molecular Hamiltonian used in quantum chemistry.

  - The number of terms of the Hamiltonian is $O(N^4)$, which is the same as the molecular Hamiltonian. Then we can compare the performance of grouping methods that reduce the number of measurements.
  - This Hamiltonian has the same order of operator norm as the molecular Hamiltonian. Therefore, the resulting ground state energy scale is similar to the scale in quantum chemistry.


- The exact value of ground state energy of this Hamiltonian can be calculated classically for the arbitrary size of the system.
  
  - Our aim through QAGC is also to create a common metric that can evaluate various NISQ algorithms. For evaluating algorithms in large qubit systems that cannot be simulated in classical computers, it will be necessary to know the exact value of the quantity to be measured as a reference value for evaluating NISQ algorithms. 

We have prepared a Hamiltonian that satisfies all of these properties. The detail of the Hamiltonian and the problem statement in QAGC is written in [Problem](#problem).

## NISQ device simulation <a id="Introduction_3"></a>
To explore the practical applications of NISQ devices and visualize bottlenecks in their utilization, it is necessary to use simulators that reflect the features of NISQ devices.

In QAGC, the participants need to use a sampling simulator we have provided. This simulator automatically performs sampling that reflects the functioning of NISQ devices and calculates an expected execution time. 
When sampling within an algorithm, it is restricted to not exceed *1000s* of the expected execution time. We will explain this limitation in [Evaluation Criteria](#EvaluationCriteria). And more detail of these NISQ device simulation and the expected execution time are written in `technical_details.md`.

# Problem description <a id="problem"></a>

## Fermi-Hubbard Model <a id="problem_1"></a>
The Fermi-Hubbard model is a model used to describe the properties of strongly correlated electron systems, which are solids with strong electron correlation effects. It is used to explain important physical phenomena such as magnetism, Mott insulators, and high-temperature superconductors. 


In QAGC, we deal with a one-dimensional orbital rotated Fermi-Hubbard model with **periodic boundary conditions**. The Hamiltonian of one-dimensional Fermi-Hubbard model is as follows:

$$
    H = - t \sum_{i=0}^{N-1} \sum_{\sigma=\uparrow, \downarrow} (a^\dagger_{i, \sigma}  a_{i+1, \sigma} +  a^\dagger_{i+1, \sigma}  a_{i, \sigma})  - \mu \sum_{i=0}^{N-1} \sum_{\sigma=\uparrow, \downarrow}  a^\dagger_{i, \sigma} a_{i, \sigma} + U \sum_{i=0}^{N-1} a^\dagger_{i, \uparrow}  a_{i, \uparrow}  a^\dagger_{i, \downarrow} a_{i, \downarrow},
$$

where $t$ is the tunneling amplitude, $\mu$ is the chemical potential, and $U$ is the Coulomb potential. For the case of half-filling, i.e. the number of electrons is equal to the number of sites, the exact value of the ground-state energy for this Hamiltonian can be calculated by using Bethe Ansatz method. 

This time we consider the orbital rotated one-dimensional Fermi-Hubbard model. The orbital rotation means linear transformation of the creation operator $a_i^\dagger$ and annihilation operator $a_i$ by using unitary matrices

$$
    \tilde c_i^\dagger = \sum_{k=0}^{2N-1} u_{ik} c_k^\dagger, \quad 
    \tilde c_i = \sum_{k=0}^{2N-1} u_{ik}^* c_k.
$$

where we label the creation operator $a_{i, \sigma}^\dagger$ as follows:

$$
    a_{i, \uparrow}^\dagger = c_{2i}^\dagger, \quad 
    a_{i, \downarrow}^\dagger = c_{2i + 1}^\dagger.
$$

The annihilator operator is labeled in the same way.

By performing orbital rotation in this way, without changing the energy eigenvalues, we can increase the number of terms to $O(N^4)$ which is the same as the molecular Hamiltonian. 

After performing orbital rotation, the Hartree-Fock calculation can be performed similar to the molecular Hamiltonian. The resulting Hartree-Fock state become:

$$
    |HF\rangle = |00001111\rangle
$$

where electrons are filled from the bottom up for a number of sites.

## Problem statement <a id="problem_2"></a>

Find the energy of the ground state of the one-dimensional orbital rotated Fermi-Hubbard model.

$$
    H = - t \sum_{i=0}^{2N-1}(\tilde c^\dagger_i \tilde c_{i+1} + \tilde c^\dagger_{i+1} \tilde c_i)  - \mu \sum_{i=0}^{2N-1}  \tilde c^\dagger_i \tilde c_i + U \sum_{i=0}^{N-1} \tilde c^\dagger_{2i} \tilde c_{2i} \tilde c^\dagger_{2i + 1} \tilde c_{2i + 1} 
$$

The value of each parameter is $N = 4,\ t=1, \mu=1.5,\ U=3$. 

For QAGC, we prepared an orbital rotated Hamiltonian with the random unitary matrix $u$ and performed Hartree-Fock calculation. Hamiltonians for 4 and 8 qubits are provided in the `hamiltonian` folder in `.data` format. Participants can use this Hamiltonian to implement their algorithm.

During the evaluation, we will use an orbital rotated Hamiltonian by using a unitary matrix different from the one used to construct the Hamiltonian in the `hamiltonian` folder. 


# Evaluation<a id="Evaluation"></a>

First, the submitted answers are checked for compliance with the prohibited items. Then, we calculates the score based on the answers, and the ranking is determined. 

## Score

The score $S$ is calculated as the inverse of the average precision of 3 runs of the algorithm rounded to the nearest $10^{-8}$ using the following evaluation formula. 

$$
    S = \frac{1}{e}
$$

Here $e$ is the average precision.

$$
    e = \frac{1}{3}\sum_{i=1}^{3}e_i
$$

$e_i$ is the precision of the output result of the $i$ th algorithm and is defined by the following equation
using the output result of the $i$ th algorithm $E_i$ and the exact value of the Hamiltonian ground state $E_{exact}$.

$$
    e_i = |E_i - E_{exact}|
$$

## Limitation by Expected Execution Time

Reducing execution time is crucial for considering the industrial application of NISQ algorithms. Additionally, the available time to use real NISQ devices is limited. To reflect this, participants will be imposed a limit based on the expected execution time obtained from the input circuit and the number of shots. The definition of the expected execution time is explained in `technical_details.md`. 

For QAGC, sampling is restricted to ensure that the expected execution time does not exceed *1000s*.

## Limitation by Run Time During the Evaluation

During the evaluation period by the management, if the evaluation period exceeds one week ($6*10^5$ sec) and is not completed, it will be forcibly stopped and the score at that time will be the final score.

# Implementation <a id="Implementation"></a>

Here, we will explain the necessary items for participants to implement their answer code.

Participants need to write their algorithms in `answer.py`.
- Participants should write their code in `get_result()` in `RunAlgorithm`. 
- It is also possible to add functions outside of RunAlgorithm as needed.
- The only codes that participants can modify are those in the problem folder. Do not modify the codes in the utils folder.

We have prepared an answer example in `example.py`, so please refer to it. 

Below, we will explain the sampling function and how to use the Hamiltonian of the problem.

-  ## Sampling Function

    In QAGC, all participants need to use the sampling function we have provided. Please refer to the `sampling.ipynb` in the `tutorials` folder for instructions on how to use it.

    This sampling function has the following properties:
    - Transpile the input circuit to the gates implemented on the real device for both superconducting and ion trap types and add the equivalent noise to measure it.
    - Calculate the expected execution time automatically.
    - When the expected execution time limit is reached, the error **QuantumCircuitTimeExceededError** will be output.

The details of this transpile, noise and the expected execution time are written in `technical_details.md`.
-  ## Hamiltonian

    The orbital rotated Fermi-Hubbard Hamiltonian is stored in the `hamiltonian` folder in `.data` format. To load it, use `openfermion.utils.load_operator()` as follows:
    ``` python
    from openfermion.utils import load_operator

    ham = load_operator(
            file_name= 8_qubits_H", data_directory="../hamiltonian", plain_text=False
        )
    ```
    In addition to the 8-qubit Hamiltonian used for the problem, there are also 4 and 8-qubit Hamiltonians in this folder that can be freely used to verify the implemented algorithm. 

    The important point is that during the evaluation, we will use an orbital rotated Hamiltonian by using a unitary matrix different from the one used to construct the Hamiltonian in the `hamiltonian` folder.

Participants can calculate the score by running `evaluator.py`.
  - **num_exec**: The number of times the algorithm is executed during evaluation.
  - **ref_value**: The reference value (exact value of the ground state energy) for each Hamiltonian is listed. The score is evaluated based on this value.

Since we are dealing with a large qubits system such as 8 qubits, running evaluator.py using the code in example.py takes *6-7* hours for a single execution.

# How to submit <a id="Submission"></a>

The participants's code will be submitted as an issue using this template summarizing your project. Specifically, this issue should contain:

1. Team name: Your team's name
2. Team members: Listup all members name
3. Project Description: A brief description of your project (1-2 paragraphs).
4. Presentation: A link of presentation of your team’s hackathon project (e.g., video, jupyter notebook, slideshow, etc.).
5. Source code: A link to the final source code for your team's hackathon project (e.g., a GitHub repo).

The score will be calculated by the management side, and the rankings will be determined and published in the [QAGC web site](https://www.qagc.org/).

- Participants can submit their work as many times as they want during the period of QAGC.

- Participants can form teams with members.

- Submitted code is evaluated once a week and rankings are presented along with scores.

Here are some points to note when submitting.

- The participants's code can be viewed by other participants.

- If you do not want it to be public, you can send the code directly to the management qagc@qunasys.com. Even in that case, the score will be calculated and the ranking will be determined, but the code will not be made public.

# Description of the Provided Program <a id="program"></a>

We have provided some codes for QAGC. The descriptions of each code are as follows.

  - `README.md`:
  
    This is the explanation of the QAGC.

  - `technical_details.md`:

    The details about the NISQ device simulation and the expected execution time.

  - `tutorials`:

    This contains some tutorials.

  - `hamiltonian`:
  
    The Hamiltonian to be used in the problem is stored in this folder in `.data` format.

The code in `problem` is structured as follows

  - `answer.py`:

    This is the file for implementing the participants's code. See [How to Submit an Algorithm](#evaluation0) for details.

  - `evaluator.py`:
    
    This is the code to evaluate the answer and calculate the score.
  - `examples.py`:
    
    This is an example of an answer prepared by QunaSys.

The code in `utils` is structured as follows.

  - `challenge_2023.py`:
    
    This contains the sampling function used in QAGC. 

  - `challenge_transpiler.py`:
    
    This is the code that transpiles the input circuit into both superconducting and ion trap types.

  - `sampling_estimator.py`:
    
    This contains the sampling function used in QAGC.


# Available Packages <a id="Packages"></a>

The following Python software library can be used in QAGC.

- [QURI Parts](https://quri-parts.qunasys.com/)

- [Qiskit](https://qiskit.org/)

- [Cirq](https://quantumai.google/cirq)

**QURI Parts** is an open-source quantum computing library that is modular, efficient, and platform-independent, developed by QunaSys.

- Platform-independent: Run one algorithm code on various simulators and platforms.

- Modularity and Scalability: Combine parts to create your own algorithm, and easily create and use your own parts.

- High-speed: Classical processing and simulator calls associated with quantum computing are efficient. It is the fastest platform-independent library using Qulacs.

- Open source: Released under Apache License 2.0.

All codes we have prepared are written by using **QURI Parts**.

In QAGC, it is also possible to use **Qiskit** as an input of the sampling function. When you input a Qiskit circuit or operator, it is automatically converted into QURI Parts one and sampled. We have provided an example of how to use the sampler and sampling estimator with qiskit circuits and operators in `tutorials.qiskit_sampling.ipynb`.

In QURI Parts, there are codes to convert **Cirq** circuits and operators to **QURI Parts**. When implementing with **Cirq**, you can use these codes to use the provided sampling function with cirq circuits and operators.

```python
from quri_parts.cirq.circuit import circuit_from_cirq
from quri_parts.cirq.operator import operator_from_cirq_op

quri_parts_circuit = circuit_from_cirq(cirq_circuit)
quri_parts_operator = operator_from_cirq_op(cirq_operator)
```

## Version

The version of the main package used in the challenge for participants will be fixed as follows:

```
quri-parts == 0.11.0
qiskit == 0.39.5
cirq == 1.1.0
openfermion == 1.5.1
qulacs == 0.5.6
numpy == 1.23.5
```

If you use a version other than the specified one, or use other packages, please specify the name of that package and its version in the issue to be registered when submitting.

# Notes and Prohibited Items <a id="forbidden"></a>

## Notes on Evaluation <a id="forbidden_1"></a>

The validity of the final answer will be judged by the judge based on whether it falls under the prohibited answers below. If it is deemed valid, a score will be calculated. The final decision on the validity of the answer and the score will be made by the operator.

## Prohibited Items <a id="forbidden_2"></a>

- Answers that do not essentially use quantum computers.
  
  Unfortunately, the fastest and most accurate way to solve the problem may be to use only classical computers. Therefore, in QAGC, we prohibit answers that do not essentially use quantum computers, such as the following examples.

  - Example 1: Pushing the exponentially time-consuming parts onto classical computation
    - Calculate the wave function classically and only calculate the final expectation value with the quantum algorithm.
  - Example 2: Not using the quantum algorithm at all.

- Algorithms that use explicitly obtained values from classical computation.

  Depending on the Hamiltonian of the problem, exact values may be obtained by classical computation (diagonalization of the Hamiltonian, etc.). In this case, you cannot use this value to construct the algorithm.

  - For example, an algorithm that prepares an exact value in advance and measures it multiple times to adopt the value closest to it.

- The implemented algorithm must be scalable with respect to the number of qubits.
  
  - For example, if you consider to diagonalizing truncated Hamiltonian, the truncation must be selected to be scalable.

- Hard-coded *good* parameter sets.

    - The selection of initial parameters must be done in a scalable manner. You cannot hard-code a *good* parameter set into the answer code.

- Answers that output values that are not calculated using the algorithm.

- Modifying code that is not allowed to be modified.

  - The only codes that participants can modify are those in the `problem` folder. Do not modify the codes in the utils folder.

# Terms <a id="Terms"></a>

I, or our company (the participant), agree to the following conditions of participation (the "Terms") and will participate in the Quantum Algorithm Grand Challenge (QAGC) conducted or operated by QunaSys Co., Ltd. (QunaSys). If any of our employees participate in the QAGC, they will also comply with these Terms.

1.	The purpose of the QAGC is to engage participants in practical problem-solving learning by collaborating with themselves or other participants and utilizing the challenges, programs, or data (referred to as "challenge data," etc.) provided by QunaSys.

2.	Participants are expected to analyze the challenge data, create responses to the challenges, and develop or modify programs.

3.	All intellectual property rights arising from the challenge data provided by QunaSys belong exclusively to QunaSys.

4.	The intellectual property rights to the results created or generated by participants using the challenge data (referred to as "the Results") belong to the respective participants. The Results include but are not limited to new ideas, responses to challenges, and programs.

5.	Participants are required to submit the Results to QunaSys by the end of the QAGC.

6.	QunaSys will not use, exploit, or implement the Results beyond the scope of considering awards in the QAGC or the purpose of operating this challenge.

7.	Unless participants explicitly refuse in advance, the Results will be made publicly available via Github.

8.	QunaSys will award a prize to participants who have been selected as winners based on the evaluation of the Results.

9.	Participants must comply with all laws, regulations, and public order and morals and must not infringe upon any third-party intellectual property rights or any other rights in participating in the QAGC.

10.	Participants shall resolve any disputes arising from the QAGC on their own and shall not seek compensation or indemnification from QunaSys.

11.	If a participant violates any provisions of these Terms and causes damage to QunaSys or other participants, they shall be liable to compensate for such damages.

12.	If a participant is a legal entity, the responsibility for any violations of these Terms by employees who actually participate in the project will be borne by that legal entity.
