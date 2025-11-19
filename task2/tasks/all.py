from invoke import task
from rich import print

from .check import check
from .format import format_code
from .test import test


@task(name="all")
def run_all(c):
    """
    Run code formatter, linter, type checker, and the testsuite with a single command. \
(coffee not included)
    """
    print("Formatting code...")
    format_code(c)

    print("Checking code...")
    check(c)

    print("Running tests...")
    test(c)
