import time


class Timer:
    def __init__(self, log_file: str = "execution_log.txt") -> None:
        self.start = time.perf_counter()
        self.log_file = log_file
        with open(self.log_file, "w") as f:
            f.write("---- GPX Analyzer Execution Log ----\n")

    def log(self, label: str) -> None:
        now = time.perf_counter()
        elapsed = now - self.start
        message = f"[TIME] {label}: {elapsed:.3f} s"
        print(message)
        with open(self.log_file, "a") as f:
            f.write(message + "\n")
        self.start = now
