import typing as t

from invoke import task
from rich import print

from common.aws import session
from common.config import config

from .check import check
from .format import format_code


def validate_version(version: str) -> bool:
    if not version.startswith("v"):
        return False
    version = version[1:]
    version_str_tuple = version.split(".")
    if len(version_str_tuple) != 3:
        return False
    for v in version_str_tuple:
        if not v.isdigit():
            return False
    return True


def parse_tag(tag: str) -> t.Tuple[int, ...]:
    version = tag[1:]  # remove prefix "v"
    version_str_tuple = version.split(".")  # split digits
    return tuple(map(int, version_str_tuple))


def get_last_version() -> t.Tuple[int, ...] | None:
    ecr_client = session.client("ecr")
    response = ecr_client.describe_images(repositoryName=config.PROJECT_NAME)
    image_list = response["imageDetails"]
    if image_list == []:
        return None

    tag_list = [image["imageTags"][0] for image in image_list if image.get("imageTags")]
    version_list = [parse_tag(tag) for tag in tag_list]  # "vX.Y.Z" -> (X, Y, Z)
    version_list.sort()

    return version_list[-1]


# TODO: (ME) This task should be refactored !!
@task(
    help={
        "no-format": "If True, skip code formatting before building [default: False]",
        "no-check": "If True, skip code checks before building [default: False]",
        "remote": "If True, build the image for ECS Fargate [default: True]",
        "no-cache": (
            "If True, build the Docker image without using cache " "[default: False]"
        ),
        "debug": (
            "If True, show detailed logs during the Docker build process "
            "[default: False]"
        ),
    }
)
def build(
    c,
    no_format: bool = False,
    no_check: bool = False,
    remote: bool = True,
    no_cache: bool = False,
    debug: bool = False,
):
    """
    Build the Docker image for the project.

    To build the Docker image locally without any issues, make sure to use remote=False

    Args:
        c: The context object for running commands.
        no_format (bool): If True, skip code formatting before building.
        no_check (bool): If True, skip code checks before building.
        remote (bool): If True, build the image for ECS Fargate by adding
                       '--platform linux/amd64' to the Docker build command.
                       Otherwise, it uses the local device platform by default.
        no_cache (bool): If True, build the Docker image without using cache.
        debug (bool): If True, use '--progress=plain' to show detailed logs
                      during the Docker build process.
    """

    with_format = not no_format
    with_check = not no_check

    if with_format:
        print("Formatting code...")
        format_code(c)
    if with_check:
        print("Checking code...")
        check(c)

    platform_option_cmd = "--platform linux/amd64" if remote else ""
    debug_option_cmd = "--progress=plain" if debug else ""

    if no_cache:
        print(
            f"Building docker image without cache..."
            f"platform_option_cmd: {platform_option_cmd}, "
            f"debug_option_cmd: {debug_option_cmd}"
        )
        c.run(
            f"docker build {platform_option_cmd} {debug_option_cmd} "
            f"--no-cache -t {config.PROJECT_NAME}:latest .",
            pty=True,
        )
        print(
            "[bold green]:tada: Project built successfully "
            "for platform linux/amd64![/bold green]"
        )
    else:
        print("Building docker image...")
        c.run(
            f"docker build {platform_option_cmd} {debug_option_cmd} "
            f"-t {config.PROJECT_NAME}:latest .",
            pty=True,
        )

    print("[bold green]:tada: Project built successfully![/bold green]")


@task(
    help={
        "version": "Version to push to ECR in vX.Y.Z format",
    }
)
def push(c, version: str):
    """
    Push the Docker image to ECR.

    Args:
        c: The context object for running commands.
        version (str): Version to push to ECR in vX.Y.Z format.
    """
    assert validate_version(version), (
        "Invalid version format. Must be vX.Y.Z where "
        "X, Y, Z are integers and 'v' letter in lowercase."
    )
    version_to_push = parse_tag(version)
    last_version = get_last_version()
    if last_version is not None:
        if version_to_push <= last_version:
            print(
                f"[bold red]Error: [/bold red] New version `[bold blue]{version}"
                f"[/bold blue]` must be greater than the last one `[bold blue]"
                f"v{last_version[0]}.{last_version[1]}.{last_version[2]}[/bold blue]`. "
            )
            return

    print("Logging in to ECR...")
    c.run(
        f"aws ecr get-login-password --region {config.AWS_REGION} | docker login "
        f"--username AWS --password-stdin {config.ECR_BASE_URL}"
    )

    print("Tagging docker...")
    local_path = f"{config.PROJECT_NAME}:latest"
    remote_path = f"{config.ECR_BASE_URL}/{config.PROJECT_NAME}:{version}"
    c.run(f"docker tag {local_path} {remote_path}", pty=True)

    print("Pushing project to ECR...")
    c.run(f"docker push {remote_path}", pty=True)

    print("[bold green]:tada: Project pushed successfully![/bold green]")
