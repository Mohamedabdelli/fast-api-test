from pathlib import Path

from invoke import task

from common.config import config

from .check import check
from .container import build
from .format import format_code

PROJECT_ROOT_PATH = Path(__file__).resolve().parent.parent


@task(
    help={
        "image-name": "Name of the Docker image to check [default: project name]",
    }
)
def docker_image_exists(c, image_name: str = config.PROJECT_NAME):
    """
    Check if a Docker image with the given name exists locally.
    Set the result in the context object as a boolean value.

    Args:
        c: The context object for running commands.
        image_name (str): Name of the Docker image to check [default: project name].
    """
    result = c.run(f"docker images -q {image_name}", hide=True, warn=True)
    c.image_exists = bool(result.stdout.strip())
    if c.image_exists:
        print(f"Found local image: {image_name}, skipping the build step...")
    else:
        print(f"Image {image_name} not found locally, building the image...")


@task(
    pre=[docker_image_exists],
    help={
        "no-format": "Skip code formatting [default: False]",
        "no-check": "Skip code checks [default: False]",
        "force-build": "Force the build step even if the image exists locally"
        " [default: False]",
    },
)
def chat(c, no_format: bool = False, no_check: bool = False, force_build: bool = False):
    """
    Run local chat server with the default chainlit frontend. For development purposes.

    Args:
        c: The context object for running commands.
        no_format (bool): If True, skip code formatting before building.
        no_check (bool): If True, skip code checks before building.
        force_build (bool): If True, force the build even if the image exists locally.
    """
    with_format = not no_format
    with_check = not no_check

    if with_format:
        format_code(c)
    if with_check:
        check(c)

    if not c.image_exists or force_build:
        build(c, remote=False)
    # Bind the project root directory to /app and the AWS credentials to /root/.aws
    volume_option = f"-v {PROJECT_ROOT_PATH}:/app " f"-v ~/.aws:/root/.aws "
    # Set a custom CMD if running locally
    cmd_override = "python -m chainlit run chat.py --host 0.0.0.0 --port 80"
    c.run(
        f"docker run -p 80:80 -e USE_PASSWORD_AUTH=true --env-file .env"
        f" {volume_option}"
        f" {config.PROJECT_NAME}:latest"
        f" {cmd_override}",
        pty=True,
    )


@task(
    pre=[docker_image_exists],
    help={
        "no_format": "Skip code formatting [default: False]",
        "no_check": "Skip code checks [default: False]",
        "local": "Bind local volumes to the Docker container [default: False]",
        "force_build": "Force the build step even if the image exists locally"
        " [default: False]",
    },
)
def server(
    c,
    no_format: bool = False,
    no_check: bool = False,
    local: bool = True,
    force_build: bool = False,
    no_cache: bool = False,
):
    """
    This Tasks runs the FastAPI server in a Docker container locally.
        - If a local image exists, it will run the existing image, unless
          `--force-build` option is used.
        - If the image does not exist, it will build the image and run the container.
        - Will mount the project root directory to `/app` and the AWS credentials to
          `/root/.aws`.

    Examples of usage:
        - `inv[oke] server [--local] [--force-build]`

    Args:
        c: The context object for running commands.
        no_format (bool): If True, skip code formatting before building.
        no_check (bool): If True, skip code checks before building.
        local (bool): If True, bind local volumes to the Docker container.
        force_build (bool): If True, force the build step even if the image exists
    """
    with_format = not no_format
    with_check = not no_check

    if with_format:
        format_code(c)
    if with_check:
        check(c)

    if not c.image_exists or force_build:
        build(c, remote=not local, no_cache=no_cache)
    # Bind the project root directory to /app and the AWS credentials to /root/.aws
    volume_option = (
        f"-v {PROJECT_ROOT_PATH}:/app " f"-v ~/.aws:/root/.aws " if local else ""
    )
    # Set a custom CMD if running locally
    cmd_override = (
        "uvicorn server:app --host 0.0.0.0 --port 80 --log-level debug --reload"
        if local
        else ""
    )

    c.run(
        f"docker run -p 80:80 --env-file .env {volume_option} "
        f"{config.PROJECT_NAME}:latest"
        f" {cmd_override}",
        pty=True,
    )
