# Thechnical details

# Table of Contents
1. [NISQ device simulation](#Simulation)
2. [Definition of Expected Execution Time](#execution_time)



# NISQ device simulation <a id="Simulation"></a>

Here we explain about the **quantum circuit simulation that models a real NISQ device (NISQ device simulation)** which is performed during algorithm execution.
The NISQ device simulation is executed as follows:

1. ### **Decomposition of input circuit**
    The input circuit is decomposed based on the circuit executed on a real NISQ device.

2. ### **Adding noise**
    Noise is added to each gate based on the real NISQ device.

After these procedure, the sampling is performed using the obtained noisy circuit.

In QAGC, two types of NISQ device simulations that model real NISQ devices are provided:
- **SC (Superconducting) type simulation**
    - Qubits are arranged in an $8\times8$ square lattice. The index of the qubit is $8x+y$, where $x$ and $y$ are the indices of the rows and columns of the lattice, respectively ( $0 \leq x,y \leq 7$ ). The coupling between qubits is only between adjacent qubits on a square lattice. The gate speed is relatively fast, but the accuracy is relatively low.
- **IT (Ion Trap) type simulation**
     - The coupling between qubits is fully connected. The gate speed is slow, but the accuracy is high.

Below, we will explain each procedure while comparing the differences between these two devices.

## 1. Decomposition of input circuit
In a real NISQ device, each gate is decomposed into a native gate set when a quantum circuit is received. To reproduce this feature, the input circuit is transpiled as follows when sampling is performed in QAGC:

- First, 2-qubit gates in the given quantum circuit are transformed according to the qubit configuration of each device.
    1. SC type:
    
        64 quantum bits are arranged on a square lattice, and 2-qubit basis gates can only be applied to adjacent quantum bits. Therefore, all 2-qubit basis gates are transformed to be applied between adjacent quantum bits using SWAP gates.
    2. IT type:

        2-qubit basis gates can be applied to all quantum bits. Therefore, 2-qubit basis gate transformation is not performed.


- Next, each gate is decomposed into "basis gates". The basis gates for each hardware are as follows:
    1. SC type: SX, X, RZ ($\theta$), CNOT
    2. IT type: U1q, ZZ, RZZ
    Please refer to the [QUANTINUUM official page](https://www.quantinuum.com/hardware/h1) for the definitions of these three gates. It is assumed that only the gates implemented in quri_parts can be used in the input circuit, and the compilation of unitary gates is not implemented in QAGC.

## 2.Adding noise
Finally, noise is added to each gate. The noise model used in QAGC is represented by four parameters $(t_1,t_2, p_\mathrm{dep}, p_\mathrm{meas})$. The specific contents are as follows:

- **T1, T2 noise**: Each time a gate is applied to each quantum bit, an amplitude damping channel and a phase damping channel due to thermal relaxation are applied to that quantum bit. Each channel is characterized by the relaxation time constant $t_1, t_2$, and these values are determined by referring to the values on the actual device.
    - SC type:
        -  $t_1=t_2= 1.5\times 10^{-4}$ sec.
    - IT type:
        - $t_1=10$ sec.
        - $t_2=1$ sec. 

- **Depolarizing noise**: Each time a 1-qubit gate or a 2-qubit gate is applied, a 1-qubit depolarizing channel with a probability of $p_\mathrm{dep}$ is applied to the quantum bit on which it acted. In QAGC, $p_\mathrm{dep}$ is set for each SC and IT device as follows:
    - SC type:
        - single qubit gate: $p_\mathrm{dep}= 10^{-3}$.
        - double qubit gate: $p_\mathrm{dep}= 10^{-2}$.
    - IT type:
        - single qubit gate: $p_\mathrm{dep}= 10^{-5}$.
        - double qubit gate: $p_\mathrm{dep}= 10^{-3}$.
- **Measurement noise**: The measurement result in the Z basis for each quantum bit has an error. This error is due to a 1-qubit bitflip channel with a probability of $p_\mathrm{meas}$. In QAGC, $p_\mathrm{meas}$ is set for each SC and IT device as follows:
    - SC type:
        - $p_\mathrm{meas} = 10^{-2}$.
    - IT type:
        -  $p_\mathrm{meas} = 10^{-3}$.


# Definition of Expected Execution Time <a id="execution_time"></a>
When a quantum circuit is given, the expected execution time per 1-shot $T_\mathrm{\text{1-shot}}$ is defined as follows:

$$
T_\mathrm{\text{1-shot}} = T_\mathrm{init} + T_\mathrm{gate} \times d.
$$

Here, $d$ is the depth of the circuit, $T_\mathrm{init}$ is the time required for initializing the quantum bit, and $T_\mathrm{gate}$ is the time required per one gate. The values for SC and IT types are as follows:
- SC type:
    - $T_\mathrm{init}=T_\mathrm{gate}=10^{-6}$ sec.
- IT type: 
    - $T_\mathrm{init}=T_\mathrm{gate}=10^{-4}$ sec.

The **quantum computer execution time** $T_1$ for sampling with $n_{\text{shot}}$ shots is calculated as follows:

$$
T_1 = n_{\text{shot}}\times T_\mathrm{\text{1-shot}}
$$

When decomposing the terms that can be simultaneously diagonalized and measuring them (grouping), the execution time for each measurement circuit and the allocated number of shots are calculated by adding them up for all groups.
