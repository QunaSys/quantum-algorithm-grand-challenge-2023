import sys
from typing import Any

import numpy as np
from openfermion.transforms import jordan_wigner
from openfermion.utils import load_operator

from quri_parts.algo.ansatz import HardwareEfficientReal
from quri_parts.algo.optimizer import Adam, OptimizerStatus
from quri_parts.circuit import LinearMappedUnboundParametricQuantumCircuit
from quri_parts.core.estimator.gradient import parameter_shift_gradient_estimates
from quri_parts.core.measurement import bitwise_commuting_pauli_measurement
from quri_parts.core.sampling.shots_allocator import (
    create_equipartition_shots_allocator,
)
from quri_parts.core.state import ParametricCircuitQuantumState, ComputationalBasisState
from quri_parts.openfermion.operator import operator_from_openfermion_op

sys.path.append("../")
from utils.challenge_2023 import ChallengeSampling, TimeExceededError


"""
It will take about 6-7 hours to run this code on 8 qubits.
"""

challenge_sampling = ChallengeSampling(noise=True)


def cost_fn(hamiltonian, parametric_state, param_values, estimator):
    estimate = estimator(hamiltonian, parametric_state, [param_values])
    return estimate[0].value.real


def vqe(hamiltonian, parametric_state, estimator, init_params, optimizer):
    opt_state = optimizer.get_init_state(init_params)

    def c_fn(param_values):
        return cost_fn(hamiltonian, parametric_state, param_values, estimator)

    def g_fn(param_values):
        grad = parameter_shift_gradient_estimates(
            hamiltonian, parametric_state, param_values, estimator
        )
        return np.asarray([i.real for i in grad.values])

    while True:
        try:
            opt_state = optimizer.step(opt_state, c_fn, g_fn)
            print(f"iteration {opt_state.niter}")
            print(opt_state.cost)
        except TimeExceededError as e:
            print(str(e))
            return opt_state

        if opt_state.status == OptimizerStatus.FAILED:
            print("Optimizer failed")
            break
        if opt_state.status == OptimizerStatus.CONVERGED:
            print("Optimizer converged")
            break
    return opt_state


class RunAlgorithm:
    def __init__(self) -> None:
        challenge_sampling.reset()

    def result_for_evaluation(self) -> tuple[Any, float]:
        energy_final = self.get_result()
        qc_time_final = challenge_sampling.total_quantum_circuit_time

        return energy_final, qc_time_final

    def get_result(self) -> Any:
        n_site = 4
        n_qubits = 2 * n_site
        ham = load_operator(
            file_name=f"{n_qubits}_qubits_H",
            data_directory="../hamiltonian",
            plain_text=False,
        )
        jw_hamiltonian = jordan_wigner(ham)
        hamiltonian = operator_from_openfermion_op(jw_hamiltonian)

        # make hf + HEreal ansatz
        hf_gates = ComputationalBasisState(n_qubits, bits=0b00001111).circuit.gates
        hf_circuit = LinearMappedUnboundParametricQuantumCircuit(n_qubits).combine(hf_gates)
        hw_ansatz = HardwareEfficientReal(qubit_count=n_qubits, reps=1)
        hf_circuit.extend(hw_ansatz)

        parametric_state = ParametricCircuitQuantumState(n_qubits, hf_circuit)

        hardware_type = "it"
        shots_allocator = create_equipartition_shots_allocator()
        measurement_factory = bitwise_commuting_pauli_measurement
        n_shots = 10**4

        sampling_estimator = (
            challenge_sampling.create_concurrent_parametric_sampling_estimator(
                n_shots, measurement_factory, shots_allocator, hardware_type
            )
        )

        adam_optimizer = Adam(ftol=10e-5)

        init_param = np.random.rand(hw_ansatz.parameter_count) * 2 * np.pi * 0.001

        result = vqe(
            hamiltonian,
            parametric_state,
            sampling_estimator,
            init_param,
            adam_optimizer,
        )
        print(f"iteration used: {result.niter}")
        return result.cost


if __name__ == "__main__":
    run_algorithm = RunAlgorithm()
    print(run_algorithm.get_result())
