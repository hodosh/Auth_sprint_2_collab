from pathlib import Path


def work_dir() -> Path:
    return Path(__file__).parent.parent.resolve()


def pre_tests_actions():
    pass
