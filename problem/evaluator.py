import numpy as np
import sys
import traceback

from typing import Optional

from example import RunAlgorithm

num_exec = 1
ref_value = -8.42442890089805  #: reference value of 8 qubits

"""
reference values (n_qubits: reference_value)
4: -4, 
8: -8.42442890089805, 
"""


class EvaluateResults:
    def __init__(self) -> None:
        self.qc_time_history: list[float] = []
        self.result_history: list[float] = []
        self.points: Optional[float] = None

    def get_point(self, n_run: int = num_exec) -> float:
        """
        :return: Grade point of the algorithm.
        """
        for n in range(n_run):
            print(f"Running algorithm({n+1})..")
            run_algorithm = RunAlgorithm()
            try:
                energy, qc_time = run_algorithm.result_for_evaluation()
                ans = abs(ref_value - energy)
                print("\n############## Result ##############")
                print(f"Resulting energy = {energy}")
                print(f"Circuit time = {qc_time}")
                print("####################################\n")
                self.qc_time_history.append(qc_time)
                self.result_history.append(ans)
            except Exception as e:
                self.points = 0
                type_, value_, traceback_ = sys.exc_info()
                print(f"{type(e)}: {str(e)}")
                traceback_message = traceback.format_exception(
                    type_, value_, traceback_
                )
                for l_ in traceback_message:
                    print(l_.strip("\n"))
                return 0
        result_ave = np.average(self.result_history)
        self.points = 1 / result_ave
        print("\n############## Final Result ##############")
        print(f"Average accuracy = {result_ave}")
        print(f"Final point = {np.round(self.points, 8)}")
        print("##########################################")

        return self.points


if __name__ == "__main__":
    point_eval = EvaluateResults()
    point_eval.get_point(n_run=num_exec)
    print(f"Algorithm points: {point_eval.points}")
    print(f"Energy result history: {point_eval.result_history}")
    print("Finished")
