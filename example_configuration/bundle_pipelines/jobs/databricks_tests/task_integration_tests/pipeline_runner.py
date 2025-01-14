import sys

sys.dont_write_bytecode = True  # fixes `OSError: [Errno 95] Operation not supported: '/.../tests/__pycache__'` error

import pytest

paths_to_test = sys.argv[3:]

if __name__ == "__main__":
    print(f"{paths_to_test=}")
    exit_code = pytest.main([*paths_to_test, "--pspec"])
    assert exit_code == 0, f"Exit Code is not zero: {exit_code}. Please see the logs for more information."
