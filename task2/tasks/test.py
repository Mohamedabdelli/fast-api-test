from pathlib import Path

from invoke import task

PROJECT_ROOT_PATH = Path(__file__).resolve().parent.parent


@task(
    help={
        "verbose": "If True, run tests with verbose output",
        "minimal": "If True, show minimal output and ignore all warnings",
    },
    aliases=["tests"],
)
def test(ctx, verbose: bool = False, minimal: bool = False) -> None:
    """
    Run pytest with optional verbosity and warning handling.

    :param c: The invoke context
    :param verbose: If True, run tests with verbose output
    :param minimal: If True, show minimal output and ignore all warnings
    """
    # Base command
    command = "pytest"

    # Add verbose flag if needed
    if verbose:
        command += " --capture=no --verbose"

    # Add minimal flag if needed
    if minimal:
        command += " -q --disable-warnings"

    with ctx.cd(PROJECT_ROOT_PATH):
        ctx.run(command, pty=True)
