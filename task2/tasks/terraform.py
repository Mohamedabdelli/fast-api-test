import os
import sys
from contextlib import contextmanager
from enum import Enum
from pathlib import Path

from invoke import task

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra" / "terraform"

# TODO: (ME) Refactor tasks
# Enum fro workspaces
class Workspace(str, Enum):
    dev = "dev"
    staging = "staging"
    prod = "production"

    @classmethod
    def values(self):
        return [v.value for v in self]


def is_valid_workspace(workspace):
    # check if workspace is valid otherwise exit
    valid_workspaces = Workspace.values()
    if workspace not in valid_workspaces:
        print(f"Invalid workspace: {workspace}")
        print(f"Valid workspaces are: {', '.join(valid_workspaces)}")
        sys.exit(1)


# Context manager to change the directory
@contextmanager
def change_directory(directory):
    prev_dir = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(prev_dir)


# Function to ensure symlink exists
def ensure_symlink(src, dest):
    src_path = Path(src)
    dest_path = Path(dest)

    if dest_path.is_symlink() or dest_path.exists():
        dest_path.unlink()  # Remove existing file or symlink

    dest_path.symlink_to(src_path.resolve())


# Helper function to check and switch the workspace
def check_and_switch_workspace(ctx, workspace, workspace_dir):
    with change_directory(workspace_dir):
        # Get the list of existing workspaces
        result = ctx.run("terraform workspace list", hide=True)
        existing_workspaces = result.stdout.splitlines()
        existing_workspaces = [w.strip("* ").strip() for w in existing_workspaces]

        # Check if the workspace exists
        if workspace in existing_workspaces:
            # Switch to the workspace
            ctx.run(f"terraform workspace select {workspace}")
        else:
            print(f"Terraform Workspace '{workspace}' does not exist.")
            print("Existing workspaces are:")
            for ws in existing_workspaces:
                print(f"  - {ws}")
            print(
                "🚫 Check if the workspace is valid and/or create it using "
                f"`cd infra/terraform/environment/{workspace} && "
                f"terraform workspace new {workspace}`"
            )
            raise SystemExit("Exiting due to non-existent workspace.")


@task(
    help={
        "workspace": "Workspace to plan the infrastructure [dev, staging, production]",
        "reconfigure": "If True, reconfigure the Terraform state",
        "upgrade": "If True, upgrade the Terraform state",
    }
)
def plan(c, workspace: str, reconfigure: bool = False, upgrade: bool = False):
    """
    Plan the infrastructure using Terraform.

    Args:
        c: The context object for running commands.
        workspace (str): Workspace to plan the infrastructure [dev, staging, production]
        reconfigure (bool): If True, reconfigure the Terraform state.
        upgrade (bool): If True, upgrade the Terraform state.
    """
    # +-- Paths --+
    workspace_dir = INFRA_DIR / "environment" / workspace
    global_config_path = INFRA_DIR / "config" / "global" / "settings.tf"
    symlink_path = workspace_dir / "settings.tf"
    var_file = INFRA_DIR / "config" / "environment" / f"{workspace}.tfvars"
    var_secrets_file = (
        INFRA_DIR / "config" / "environment" / f"{workspace}.secrets.tfvars"
    )

    is_valid_workspace(workspace)

    # Ensure symlink exists
    ensure_symlink(global_config_path, symlink_path)

    # Make sure the init comes first, Initialize Terraform with backend config
    # XXX: move this to a separate task
    # +-- Initialize Terraform --+
    init_command = "terraform init"

    if reconfigure:
        init_command += " -reconfigure"
    else:
        init_command += " -migrate-state"

    if upgrade:
        init_command += " -upgrade"

    with change_directory(workspace_dir):
        c.run(init_command)
    # +-- Check and switch workspace --+
    check_and_switch_workspace(c, workspace, workspace_dir)

    # Change directory to workspace
    with change_directory(workspace_dir):
        # ctx.run(f"terraform plan -var-file={var_file}")
        c.run(f"terraform plan -var-file={var_file} -var-file={var_secrets_file}")


@task(
    help={
        "workspace": "Workspace to apply the infrastructure [dev, staging, production]",
        "auto-approve": "If True, auto-approve the Terraform apply [default: False]",
    }
)
def apply(c, workspace: str, auto_approve: bool = False):
    """
    Apply the infrastructure changes using Terraform.

    Args:
        c: The context object for running commands.
        workspace (str): Workspace to apply the infra [dev, staging, production].
        auto_approve (bool): If True, auto-approve the Terraform apply.
    """
    # Paths
    workspace_dir = INFRA_DIR / "environment" / workspace
    global_config_path = INFRA_DIR / "config" / "global" / "settings.tf"
    symlink_path = workspace_dir / "settings.tf"
    var_file = INFRA_DIR / "config" / "environment" / f"{workspace}.tfvars"
    var_secrets_file = (
        INFRA_DIR / "config" / "environment" / f"{workspace}.secrets.tfvars"
    )

    is_valid_workspace(workspace)

    # Ensure symlink exists
    ensure_symlink(global_config_path, symlink_path)

    # Check and switch workspace
    check_and_switch_workspace(c, workspace, workspace_dir)

    # # Initialize Terraform with backend config
    # init_command = f"terraform init"

    # Change directory to workspace
    with change_directory(workspace_dir):
        # Run terraform apply
        if auto_approve:
            c.run(
                f"terraform apply -var-file={var_file} "
                f"-var-file={var_secrets_file} -auto-approve"
            )
        else:
            c.run(
                f"terraform apply -var-file={var_file} " f"-var-file={var_secrets_file}"
            )


@task(
    help={
        "workspace": "Workspace to destroy the infra [dev, staging, production]",
        "auto-approve": "If True, auto-approve the Terraform destroy [default: False]",
    }
)
def destroy(c, workspace: str, auto_approve: bool = False):
    """
    Destroy the infrastructure using Terraform.

    Args:
        c: The context object for running commands.
        workspace (str): Workspace to destroy the infra [dev, staging, production].
        auto_approve (bool): If True, auto-approve the Terraform destroy.
    """
    # Paths
    workspace_dir = INFRA_DIR / "environment" / workspace
    global_config_path = INFRA_DIR / "config" / "global" / "settings.tf"
    symlink_path = workspace_dir / "settings.tf"
    var_file = INFRA_DIR / "config" / "environment" / f"{workspace}.tfvars"
    var_secrets_file = (
        INFRA_DIR / "config" / "environment" / f"{workspace}.secrets.tfvars"
    )

    # Ensure symlink exists
    ensure_symlink(global_config_path, symlink_path)

    init_command = "terraform init"

    # Change directory to workspace
    with change_directory(workspace_dir):
        # Run terraform destroy
        c.run(init_command)
        if auto_approve:
            c.run(
                f"terraform destroy -var-file={var_file} "
                f"-var-file={var_secrets_file} -auto-approve"
            )
        else:
            c.run(
                f"terraform destroy -var-file={var_file} "
                f"-var-file={var_secrets_file}"
            )
