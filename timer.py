import time

class Timer:
    """
    Simple utility class for measuring execution time of blocks of code
    """

    logging_enabled: bool
    t_start: float

    def _log_elapsed(self, elapsed: float, msg: str):
        if self.logging_enabled:
            print(f'{msg}: {elapsed}')

    def start(self):
        self.t_start = time.perf_counter()

    def stop(self, msg='') -> float:
        elapsed = time.perf_counter() - self.t_start
        if msg:
            self._log_elapsed(elapsed, msg)
        return elapsed
