from collections.abc import Collection, Iterable
from typing import Mapping, Sequence, Union

from qiskit.circuit import QuantumCircuit as QiskitQuantumCircuit
from qiskit.opflow import PauliOp, PauliSumOp
from quri_parts.circuit import NonParametricQuantumCircuit

from quri_parts.circuit.noise import (
    BitFlipNoise,
    DepolarizingNoise,
    MeasurementNoise,
    NoiseModel,
    ThermalRelaxationNoise,
)
from quri_parts.core.estimator import (
    ConcurrentParametricQuantumEstimator,
    ConcurrentQuantumEstimator,
    Estimatable,
    Estimate,
    ParametricQuantumEstimator,
    QuantumEstimator,
    create_parametric_estimator,
)
from quri_parts.core.measurement import CommutablePauliSetMeasurementFactory
from quri_parts.core.operator import PAULI_IDENTITY, Operator
from quri_parts.core.sampling import (
    ConcurrentSampler,
    MeasurementCounts,
    PauliSamplingShotsAllocator,
    Sampler,
)
from quri_parts.core.state import (
    CircuitQuantumState,
    GeneralCircuitQuantumState,
    ParametricCircuitQuantumState,
)
from quri_parts.qiskit.circuit import circuit_from_qiskit
from quri_parts.qiskit.operator import operator_from_qiskit_op
from quri_parts.quantinuum.circuit.transpile import QuantinuumSetTranspiler
from quri_parts.qulacs.sampler import (
    create_qulacs_noisesimulator_concurrent_sampler,
    create_qulacs_vector_concurrent_sampler,
)

from utils.challenge_transpiler import (
    SCSquareLatticeTranspiler,
    quri_parts_iontrap_native_circuit,
)
from utils.sampling_estimator import sampling_estimate_gc
from time import time

max_qc_time = 1000
max_run_time = 6 * 10 ** 5
QPQiskitCircuit = Union[NonParametricQuantumCircuit, QiskitQuantumCircuit]
QPQiskitOperator = Union[Operator, Union[PauliSumOp, PauliOp]]


class ChallengeSampling:
    def __init__(self, noise: bool) -> None:
        self.total_shots: int = 0
        self.total_jobs: int = 0
        self.total_quantum_circuit_time: float = 0.0
        self._noise = noise
        self.transpiler = None
        self.transpiled_circuit = None
        self.gate_time: float = 0
        self.initializing_time: float = 0
        self.init_time: float = time()

    def sampler(
        self,
        circuit: QPQiskitCircuit,
        n_shots: int,
        hardware_type: str,
    ) -> Iterable[Mapping[int, Union[int, float]]]:
        """Sampling by using a given circuit with a given number of shots and hartware type.

        Args:
            circuit: A sampling circuit.
            n_shots: Number of shots for sampling.
            hardware_type: "sc" for super conducting, "it" for iontrap type hardware.

        Returns:
            Counts of sampling.
        """
        if isinstance(circuit, QiskitQuantumCircuit):
            circuit = circuit_from_qiskit(circuit)

        noise_model, transpiled_circuit = self._noise_model_with_transpiled_circuit(
            circuit, hardware_type
        )
        concurrent_sampler = self._concurrent_sampler(noise_model)
        if hardware_type == "it":
            transpiled_circuit = quri_parts_iontrap_native_circuit(transpiled_circuit)
        counts = concurrent_sampler([(transpiled_circuit, n_shots)])[0]

        self.total_jobs += 1
        self.total_shots += n_shots
        tot_gate_time = transpiled_circuit.depth * self.gate_time * n_shots
        tot_initializing_time = self.initializing_time * n_shots
        tot_time = tot_gate_time + tot_initializing_time
        self.total_quantum_circuit_time += tot_time

        now_time = time()
        run_time = now_time - self.init_time
        if self.total_quantum_circuit_time > max_qc_time or run_time > max_run_time:
            raise TimeExceededError(self.total_quantum_circuit_time, run_time)

        return counts

    def create_sampler(self, hardware_type: str) -> Sampler:
        """Returns a :class:`~Sampler`."""

        def sampling(circuit: QPQiskitCircuit, n_shots: int) -> MeasurementCounts:
            count = self.sampler(circuit, n_shots, hardware_type)
            return count

        return sampling

    def create_concurrent_sampler(self, hardware_type: str) -> ConcurrentSampler:
        """Returns a :class:`~ConcurrentSampler`."""

        def sampling(
            shot_circuit_pairs: Iterable[tuple[QPQiskitCircuit, int]]
        ) -> Iterable[MeasurementCounts]:
            counts = []
            for circuit, n_shots in shot_circuit_pairs:
                counts.append(self.sampler(circuit, n_shots, hardware_type))
            return counts

        return sampling

    def sampling_estimator(
        self,
        operator: QPQiskitOperator,
        state_or_circuit: Union[CircuitQuantumState, QiskitQuantumCircuit],
        n_shots: int,
        measurement_factory: CommutablePauliSetMeasurementFactory,
        shots_allocator: PauliSamplingShotsAllocator,
        hardware_type: str,
    ) -> Estimate[complex]:
        """Estimate expectation value of a given operator with a given state or qiskit circuit by
        sampling measurement.

        The sampling measurements are configured with arguments as follows.

        Args:
            operator: An operator of which expectation value is estimated.
            state_or_circuit: A quantum state on which the operator expectation is evaluated.
            n_shots: Total number of shots available for sampling measurements.
            measurement_factory: A function that performs Pauli grouping and returns
                a measurement scheme for Pauli operators constituting the original operator.
            shots_allocator: A function that allocates the total shots to Pauli groups to
                be measured.
            hardware_type: "sc" for super conducting, "it" for iontrap type hardware.

        Returns:
            The estimated value (can be accessed with :attr:`.value`) with standard error
                of estimation (can be accessed with :attr:`.error`).
        """

        if isinstance(operator, PauliSumOp) or isinstance(operator, PauliOp):
            operator = operator_from_qiskit_op(operator)

        if isinstance(state_or_circuit, QiskitQuantumCircuit):
            circuit = circuit_from_qiskit(state_or_circuit)
        else:
            circuit = state_or_circuit.circuit

        noise_model, transpiled_circuit = self._noise_model_with_transpiled_circuit(
            circuit=circuit, hardware_type=hardware_type
        )

        state = GeneralCircuitQuantumState(
            transpiled_circuit.qubit_count, transpiled_circuit
        )

        concurrent_sampler = self._concurrent_sampler(noise_model)

        estimated_value, circuit_and_shots = sampling_estimate_gc(
            op=operator,
            state=state,
            total_shots=n_shots,
            sampler=concurrent_sampler,
            hardware_type=hardware_type,
            measurement_factory=measurement_factory,
            shots_allocator=shots_allocator,
        )
        if len(operator) == 0:
            return estimated_value.value.real

        if PAULI_IDENTITY in operator:
            if len(operator) == 1:
                return estimated_value.value.real

        self.total_jobs += 1
        self.total_shots += n_shots
        tot_gate_time, tot_initializing_time = 0.0, 0.0
        for circuit_shots in circuit_and_shots:
            circuit_depth = self.transpiler(circuit_shots[0]).depth
            tot_gate_time += float(self.gate_time * circuit_depth * circuit_shots[1])
            tot_initializing_time += self.initializing_time * circuit_shots[1]
        tot_time = tot_gate_time + tot_initializing_time
        self.total_quantum_circuit_time += tot_time

        now_time = time()
        run_time = now_time - self.init_time
        if self.total_quantum_circuit_time > max_qc_time or run_time > max_run_time:
            raise TimeExceededError(self.total_quantum_circuit_time, run_time)

        return estimated_value

    def concurrent_sampling_estimator(
        self,
        operators: Collection[Estimatable],
        states: Collection[CircuitQuantumState],
        total_shots: int,
        measurement_factory: CommutablePauliSetMeasurementFactory,
        shots_allocator: PauliSamplingShotsAllocator,
        hardware_type: str,
    ) -> Iterable[Estimate[complex]]:
        """Estimate expectation value of given operators with given states by
        sampling measurement.

        The sampling measurements are configured with arguments as follows.

        Args:
            operators: Operators of which expectation value is estimated.
            states: Quantum states on which the operator expectation is evaluated.
            total_shots: Total number of shots available for sampling measurements.
            measurement_factory: A function that performs Pauli grouping and returns
                a measurement scheme for Pauli operators constituting the original operator.
            shots_allocator: A function that allocates the total shots to Pauli groups to
                be measured.
                hardware_type: "sc" for super conducting, "it" for iontrap type hardware.

        Returns:
            The estimated values (can be accessed with :attr:`.value`) with standard errors
                of estimation (can be accessed with :attr:`.error`).
        """

        num_ops = len(operators)
        num_states = len(states)

        if num_ops == 0:
            raise ValueError("No operator specified.")

        if num_states == 0:
            raise ValueError("No state specified.")

        if num_ops > 1 and num_states > 1 and num_ops != num_states:
            raise ValueError(
                f"Number of operators ({num_ops}) does not match"
                f"number of states ({num_states})."
            )

        if num_states == 1:
            states = [next(iter(states))] * num_ops
        if num_ops == 1:
            operators = [next(iter(operators))] * num_states
        return [
            self.sampling_estimator(
                op,
                state,
                total_shots,
                measurement_factory,
                shots_allocator,
                hardware_type,
            )
            for op, state in zip(operators, states)
        ]

    def create_sampling_estimator(
        self,
        total_shots: int,
        measurement_factory: CommutablePauliSetMeasurementFactory,
        shots_allocator: PauliSamplingShotsAllocator,
        hardware_type: str,
    ) -> QuantumEstimator[CircuitQuantumState]:
        """Create a :class:`QuantumEstimator` that estimates operator expectation
        value by sampling measurement.

        The sampling measurements are configured with arguments as follows.

        Args:
            total_shots: Total number of shots available for sampling measurements.
            measurement_factory: A function that performs Pauli grouping and returns
                a measurement scheme for Pauli operators constituting the original operator.
            shots_allocator: A function that allocates the total shots to Pauli groups to
                be measured.
            hardware_type: "sc" for super conducting, "it" for iontrap type hardware.
        """

        def sampling_estimate(
            operators: Operator, states: CircuitQuantumState
        ) -> Estimate[complex]:
            estimator = self.sampling_estimator(
                operators,
                states,
                total_shots,
                measurement_factory,
                shots_allocator,
                hardware_type,
            )
            return estimator

        return sampling_estimate

    def create_concurrent_sampling_estimator(
        self,
        total_shots: int,
        measurement_factory: CommutablePauliSetMeasurementFactory,
        shots_allocator: PauliSamplingShotsAllocator,
        hardware_type: str,
    ) -> ConcurrentQuantumEstimator[CircuitQuantumState]:
        """Create a :class:`ConcurrentQuantumEstimator` that estimates operator
        expectation value by sampling measurement.

        The sampling measurements are configured with arguments as follows.

        Args:
            total_shots: Total number of shots available for sampling measurements.
            measurement_factory: A function that performs Pauli grouping and returns
                a measurement scheme for Pauli operators constituting the original operator.
            shots_allocator: A function that allocates the total shots to Pauli groups to
                be measured.
            hardware_type: "sc" for super conducting, "it" for iontrap type hardware.
        """

        def sampling_estimate(
            operators: Sequence[Operator], states: Sequence[CircuitQuantumState]
        ) -> Iterable[Estimate[complex]]:
            estimator = self.concurrent_sampling_estimator(
                operators,
                states,
                total_shots,
                measurement_factory,
                shots_allocator,
                hardware_type,
            )
            return estimator

        return sampling_estimate

    def create_parametric_sampling_estimator(
        self,
        total_shots: int,
        measurement_factory: CommutablePauliSetMeasurementFactory,
        shots_allocator: PauliSamplingShotsAllocator,
        hardware_type: str,
    ) -> ParametricQuantumEstimator[ParametricCircuitQuantumState]:
        """Create a :class:`QuantumEstimator` that estimates operator expectation
        value by sampling measurement.

        The sampling measurements are configured with arguments as follows.

        Args:
            total_shots: Total number of shots available for sampling measurements.
            measurement_factory: A function that performs Pauli grouping and returns
                a measurement scheme for Pauli operators constituting the original operator.
            shots_allocator: A function that allocates the total shots to Pauli groups to
                be measured.
            hardware_type: "sc" for super conducting, "it" for iontrap type hardware.
        """
        sampling_estimator = self.create_sampling_estimator(
            total_shots,
            measurement_factory,
            shots_allocator,
            hardware_type,
        )
        return create_parametric_estimator(sampling_estimator)

    def create_concurrent_parametric_sampling_estimator(
        self,
        total_shots: int,
        measurement_factory: CommutablePauliSetMeasurementFactory,
        shots_allocator: PauliSamplingShotsAllocator,
        hardware_type: str,
    ) -> ConcurrentParametricQuantumEstimator[ParametricCircuitQuantumState]:
        """Create a :class:`ConcurrentParametricQuantumEstimator` that estimates operator
        expectation value by sampling measurement.

        The sampling measurements are configured with arguments as follows.

        Args:
            total_shots: Total number of shots available for sampling measurements.
            measurement_factory: A function that performs Pauli grouping and returns
                a measurement scheme for Pauli operators constituting the original operator.
            shots_allocator: A function that allocates the total shots to Pauli groups to
                be measured.
            hardware_type: "sc" for super conducting, "it" for iontrap type hardware.
        """

        def concurrent_parametric_sampling_estimater(
            operator: Operator,
            state: ParametricCircuitQuantumState,
            params: Sequence[Sequence[float]],
        ) -> Iterable[Estimate[complex]]:
            bind_states = [state.bind_parameters(param) for param in params]
            concurrent_estimator = self.concurrent_sampling_estimator(
                [operator],
                bind_states,
                total_shots,
                measurement_factory,
                shots_allocator,
                hardware_type,
            )
            return concurrent_estimator

        return concurrent_parametric_sampling_estimater

    def _noise_model(
        self,
        bitflip_error: float,
        single_qubit_depolarizing_error: float,
        double_qubit_depolarizing_error: float,
        t1: float,
        t2: float,
        gate_time: float,
    ) -> NoiseModel:
        model = NoiseModel()
        model.add_noise(
            noise=DepolarizingNoise(single_qubit_depolarizing_error),
            custom_gate_filter=lambda gate: len(gate.target_indices)
            + len(gate.control_indices)
            == 1,
        )
        model.add_noise(
            noise=DepolarizingNoise(double_qubit_depolarizing_error),
            custom_gate_filter=lambda gate: len(gate.target_indices)
            + len(gate.control_indices)
            == 2,
        )
        model.add_noise(
            noise=ThermalRelaxationNoise(
                t1=t1, t2=t2, gate_time=gate_time, excited_state_population=0.1
            )
        )
        model.add_noise(
            noise=MeasurementNoise(single_qubit_noises=[BitFlipNoise(bitflip_error)])
        )
        return model

    def _concurrent_sampler(self, noise_model: NoiseModel) -> ConcurrentSampler:
        if self._noise:
            concurrent_sampler = create_qulacs_noisesimulator_concurrent_sampler(
                model=noise_model,
            )
        else:
            concurrent_sampler = create_qulacs_vector_concurrent_sampler()
        return concurrent_sampler

    def _noise_model_with_transpiled_circuit(
        self,
        circuit: NonParametricQuantumCircuit,
        hardware_type: str,
    ) -> tuple[NoiseModel, NonParametricQuantumCircuit]:
        if hardware_type == "sc":
            transpiler = SCSquareLatticeTranspiler()
            # decompose to X, SX, RZ, CNOT, Identity
            # sc (super conductor type) transpiler
            transpiled_circuit = transpiler(circuit)

            t1 = 1.5 * 1e-4
            t2 = 1.5 * 1e-4
            single_qubit_depolarizing_error = 1e-3
            double_qubit_depolarizing_error = 1e-2
            bitflip_error = 1e-2
            initializing_time = 1e-6
            gate_time = 1e-6
        elif hardware_type == "it":
            transpiler = QuantinuumSetTranspiler()
            #: decompose to Quantinuum native gates U1q, ZZ, RZZ, RZ
            transpiled_circuit = transpiler(circuit)

            t1 = 1e1
            t2 = 1e0
            single_qubit_depolarizing_error = 1e-5
            double_qubit_depolarizing_error = 1e-3
            bitflip_error = 1e-3
            initializing_time = 1e-4
            gate_time = 1e-4
        else:
            raise NotImplementedError(
                f"Unsupported hardware_type type: {hardware_type}"
            )
        noise_model = self._noise_model(
            bitflip_error=bitflip_error,
            single_qubit_depolarizing_error=single_qubit_depolarizing_error,
            double_qubit_depolarizing_error=double_qubit_depolarizing_error,
            t1=t1,
            t2=t2,
            gate_time=gate_time,
        )
        self.initializing_time = initializing_time
        self.gate_time = gate_time
        self.transpiler = transpiler
        self.transpiled_circuit = transpiled_circuit
        return noise_model, transpiled_circuit

    def reset(self) -> None:
        self.total_shots = 0
        self.total_jobs = 0
        self.total_quantum_circuit_time = 0


class TimeExceededError(Exception):
    def __init__(self, qc_time: float, run_time: float):
        self.qc_time = qc_time
        self.run_time = run_time

    def __str__(self) -> str:
        if self.run_time > max_run_time:
            return (
                f"Reached maximum runtime {max_run_time}. "
                f"Run time {self.run_time}"
            )
        else:
            return (
                f"Reached maximum quantum circuit time {max_qc_time}. "
                f"Quantum circuit time {self.qc_time}"
            )


if __name__ == "__main__":
    pass
