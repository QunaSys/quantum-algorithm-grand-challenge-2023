from typing import Iterable

from quri_parts.circuit import NonParametricQuantumCircuit
from quri_parts.core.estimator import Estimatable, Estimate
from quri_parts.core.estimator.sampling.estimator import _ConstEstimate, _Estimate
from quri_parts.core.measurement import CommutablePauliSetMeasurementFactory
from quri_parts.core.operator import PAULI_IDENTITY, Operator
from quri_parts.core.sampling import ConcurrentSampler, PauliSamplingShotsAllocator
from quri_parts.core.state import CircuitQuantumState
from quri_parts.quantinuum.circuit.transpile import QuantinuumSetTranspiler

from utils.challenge_transpiler import (
    SCSquareLatticeTranspiler,
    quri_parts_iontrap_native_circuit,
)


def sampling_estimate_gc(
    op: Estimatable,
    state: CircuitQuantumState,
    total_shots: int,
    sampler: ConcurrentSampler,
    hardware_type: str,
    measurement_factory: CommutablePauliSetMeasurementFactory,
    shots_allocator: PauliSamplingShotsAllocator,
) -> tuple[Estimate[complex], Iterable[tuple[NonParametricQuantumCircuit, int]]]:
    """Estimate expectation value of a given operator with a given state by
    sampling measurement.

    The sampling measurements are configured with arguments as follows.

    Args:
        op: An operator of which expectation value is estimated.
        state: A quantum state on which the operator expectation is evaluated.
        total_shots: Total number of shots available for sampling measurements.
        sampler: a :class:`~ConcurrentSampler` that actually performs the sampling.
        hardware_type: "sc" for super conducting, "it" for iontrap type hardware.
        measurement_factory: A function that performs Pauli grouping and returns
            a measurement scheme for Pauli operators constituting the original operator.
        shots_allocator: A function that allocates the total shots to Pauli groups to
            be measured.

    Returns:
        The estimated value (can be accessed with :attr:`.value`) with standard error
        of estimation (can be accessed with :attr:`.error`) and grouped circuit and shots.
    """
    if hardware_type == "sc":
        transpiler = SCSquareLatticeTranspiler()
    elif hardware_type == "it":
        transpiler = QuantinuumSetTranspiler()
    else:
        raise

    if not isinstance(op, Operator):
        op = Operator({op: 1.0})

    if len(op) == 0:
        circuit_shots = [(state.circuit, total_shots)]
        return _ConstEstimate(0.0), circuit_shots

    const: complex = 0.0
    if PAULI_IDENTITY in op:
        const = op[PAULI_IDENTITY]
        if len(op) == 1:
            circuit_shots = [(state.circuit, total_shots)]
            return _ConstEstimate(const), circuit_shots

    measurements = measurement_factory(op)
    measurements = [m for m in measurements if m.pauli_set != {PAULI_IDENTITY}]

    pauli_sets = tuple(m.pauli_set for m in measurements)
    shot_allocs = shots_allocator(op, pauli_sets, total_shots)
    shots_map = {pauli_set: n_shots for pauli_set, n_shots in shot_allocs}

    # Eliminate pauli sets which are allocated no shots
    measurement_circuit_shots = [
        (m, state.circuit + m.measurement_circuit, shots_map[m.pauli_set])
        for m in measurements
        if shots_map[m.pauli_set] > 0
    ]

    circuit_and_shots = []
    for _, circuit, shots in measurement_circuit_shots:
        circuit = transpiler(circuit)
        circuit_and_shots.append((circuit, shots))
    if hardware_type == "sc":
        sampling_counts = sampler(circuit_and_shots)
    else:
        circuit_and_shots_for_it_sampling = [
            (quri_parts_iontrap_native_circuit(circuit), shots) for (circuit, shots) in circuit_and_shots
        ]
        sampling_counts = sampler(circuit_and_shots_for_it_sampling)

    pauli_sets = tuple(m.pauli_set for m, _, _ in measurement_circuit_shots)
    pauli_recs = tuple(
        m.pauli_reconstructor_factory for m, _, _ in measurement_circuit_shots
    )
    return (
        _Estimate(op, const, pauli_sets, pauli_recs, tuple(sampling_counts)),
        circuit_and_shots,
    )
