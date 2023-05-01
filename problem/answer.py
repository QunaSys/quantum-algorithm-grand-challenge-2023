import sys
from typing import Any

sys.path.append("../")
from utils.challenge_2023 import ChallengeSampling

challenge_sampling = ChallengeSampling(noise=True)

"""
####################################
add codes here
####################################
"""


class RunAlgorithm:
    def __init__(self) -> None:
        challenge_sampling.reset()

    def result_for_evaluation(self) -> tuple[Any, float]:
        energy_final = self.get_result()
        qc_time_final = challenge_sampling.total_quantum_circuit_time

        return energy_final, qc_time_final

    def get_result(self) -> float:
        """
        ####################################
        add codes here
        ####################################
        """

        return 0


if __name__ == "__main__":
    run_algorithm = RunAlgorithm()
    print(run_algorithm.get_result())
