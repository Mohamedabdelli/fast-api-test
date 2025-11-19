from invoke import task
from rich import print


@task
def check(c):
    """
    Check the code quality with the type checker and linter.
    """
    print("Checking code quality with [bold]mypy[/bold]...")
    c.run("mypy . --exclude 'vendored/.*' --exclude '.*\\.ipynb$'", pty=True)

    print("Checking code quality with [bold]ruff[/bold]...")
    c.run("ruff check . --exclude vendored/ --extend-exclude '\\.ipynb$'", pty=True)
