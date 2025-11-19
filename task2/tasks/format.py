from invoke import task


@task(name="format")
def format_code(c):
    """
    Format the code with isort and black.
    """
    c.run("isort .", pty=True)
    c.run("black --config=./pyproject.toml .", pty=True)
