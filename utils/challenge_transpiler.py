from typing import Callable, cast

import numpy as np
from qulacs.gate import DenseMatrix
from quri_parts.circuit import QuantumCircuit, QuantumGate, UnitaryMatrix
from quri_parts.circuit.topology import (
    SquareLattice,
    SquareLatticeSWAPInsertionTranspiler,
)
from quri_parts.circuit.transpile import (
    CircuitTranspiler,
    CZ2CNOTHTranspiler,
    H2RZSqrtXTranspiler,
    ParallelDecomposer,
    RZSetTranspiler,
    SequentialTranspiler,
    SWAP2CNOTTranspiler,
)
from quri_parts.qulacs.circuit import convert_gate

SCSquareLatticeTranspiler: Callable[
    [], CircuitTranspiler
] = lambda: SequentialTranspiler(
    [
        RZSetTranspiler(),
        SquareLatticeSWAPInsertionTranspiler(SquareLattice(xsize=8, ysize=8)),
        ParallelDecomposer(
            [CZ2CNOTHTranspiler(), SWAP2CNOTTranspiler(), H2RZSqrtXTranspiler()]
        ),
    ]
)


def complex_exp(angle: float) -> complex:
    return cast(complex, np.cos(angle) + 1j * np.sin(angle))


def iontrap_native_gate_representation(gate: QuantumGate) -> list[list[complex]]:
    if gate.name == "U1q":
        theta, phi = gate.params
        gate_list = [
            [np.cos(theta / 2), -1j * complex_exp(-phi) * np.sin(theta / 2)],
            [-1j * complex_exp(phi) * np.sin(theta / 2), np.cos(theta / 2)],
        ]
    elif gate.name == "ZZ":
        gate_list = [[1, 0, 0, 0], [0, 1j, 0, 0], [0, 0, 1j, 0], [0, 0, 0, 1]]
    elif gate.name == "RZZ":
        theta = gate.params[0]
        gate_list = [
            [1, 0, 0, 0],
            [0, complex_exp(theta), 0, 0],
            [0, 0, complex_exp(theta), 0],
            [0, 0, 0, 1],
        ]
    else:
        raise
    return gate_list


def quri_parts_iontrap_native_gate(gate: QuantumGate) -> QuantumGate:
    if gate.name == "U1q" or gate.name == "ZZ" or gate.name == "RZZ":
        unitary_matrix = UnitaryMatrix(
            gate.target_indices, unitary_matrix=iontrap_native_gate_representation(gate)
        )
    else:
        if gate.name == "RZ":
            unitary_matrix = gate
        else:
            raise ValueError(f"Invalid native gate name: {gate.name}")
    return unitary_matrix


def quri_parts_iontrap_native_circuit(circuit: QuantumCircuit) -> QuantumCircuit:
    qc = QuantumCircuit(circuit.qubit_count)
    for gate in circuit.gates:
        qc.add_gate(gate=quri_parts_iontrap_native_gate(gate))
    return qc


def convert_iontrap_native_gate(gate: QuantumGate) -> DenseMatrix:
    if gate.name == "U1q" or gate.name == "ZZ" or gate.name == "RZZ":
        return DenseMatrix(
            index_list=gate.target_indices,
            matrix=iontrap_native_gate_representation(gate),
        )
    elif gate.name == "UnitaryMatrix":
        return convert_gate(gate)
    else:
        if gate.name == "RZ":
            return convert_gate(gate)
        raise ValueError(f"Invalid native gate name: {gate.name}")


if __name__ == "__main__":
    pass
