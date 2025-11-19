import subprocess
from enum import Enum
from pathlib import Path

from invoke import task

CF_TEMPLATE_PATH = Path("__file__").parent / "infra" / "cloudformation"


class ChatDBTableStack(Enum):
    DEV = "cominty-chat-table-dev-59C2566A-6973-4C40-8CC2-08CFF626A"
    STAGING = "cominty-chat-table-staging-9EEEC115-F270-42C2-8DD4-9CBF23A9B7BA"

    @classmethod
    def from_env(cls, env):
        return cls[env.upper()]


@task(
    help={
        "env": "Environment to update the chat table stack [dev, staging, production]",
    }
)
def update_chat_table(c, env: str):
    """
    Update the chat table stack.

    Args:
        c: The context object for running commands.
        env (str): Environment to update the chat table stack [dev, staging, production]
    """

    assert env in [
        "dev",
        "staging",
        "production",
    ], f"❌ Invalid environment {env}, must be one of [dev, staging, production]"

    chat_db_table_stack_base_name = "chat-backend-threads-table"

    stack_name = f"{chat_db_table_stack_base_name}-{env}"

    cf_template_path = (
        CF_TEMPLATE_PATH / "data_layer" / env / "cominty_chat_dynamodb_storage.json"
    )

    print(f"🛠️ Updating stack {stack_name}")
    print(f"📄 Using template {cf_template_path}")

    proceed = input("❓ Do you want to proceed? (y/n): ").lower().strip() == "y"

    if not proceed:
        print("🚫 Aborting...")
        return

    command = [
        "aws",
        "cloudformation",
        "update-stack",
        "--stack-name",
        stack_name,
        "--template-body",
        f"file://{cf_template_path}",
        "--capabilities",
        "CAPABILITY_IAM",
    ]

    try:
        print("⏳ Updating stack...")
        _ = subprocess.run(command, check=True, capture_output=True, text=True)
        print("✅ Stack updated successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error updating stack: {e.stderr}")


# chat to create chat table (first time) with stack name = cominty-chat-table-{env}
@task(
    help={
        "env": "Environment to create the chat table stack [dev, staging, production]",
    }
)
def create_chat_table(c, env):
    """
    Create the chat table stack and enable termination protection.

    Args:
        c: The context object for running commands.
        env (str): Environment to create the chat table stack [dev, staging, production]
    """

    assert env in [
        "dev",
        "staging",
        "production",
    ], f"❌ Invalid environment {env}, must be one of [dev, staging, production]"

    chat_db_table_stack_base_name = "chat-backend-threads-table"

    stack_name = f"{chat_db_table_stack_base_name}-{env}"

    cf_template_path = (
        CF_TEMPLATE_PATH / "data_layer" / env / "cominty_chat_dynamodb_storage.json"
    )

    print(f"🛠️ Creating stack {stack_name}")
    print(f"📄 Using template {cf_template_path}")

    proceed = input("❓ Do you want to proceed? (y/n): ").lower().strip() == "y"

    if not proceed:
        print("🚫 Aborting...")
        return

    command = [
        "aws",
        "cloudformation",
        "create-stack",
        "--stack-name",
        stack_name,
        "--template-body",
        f"file://{cf_template_path}",
        "--capabilities",
        "CAPABILITY_IAM",
    ]

    try:
        print("⏳ Creating stack...")
        _ = subprocess.run(command, check=True, capture_output=True, text=True)
        print("✅ Stack created successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating stack: {e.stderr}")

    # Command to enable termination protection
    protect_command = [
        "aws",
        "cloudformation",
        "update-termination-protection",
        "--enable-termination-protection",
        "--stack-name",
        stack_name,
    ]

    try:
        print("🔐 ⏳ Enabling termination protection...")
        _ = subprocess.run(protect_command, check=True, capture_output=True, text=True)
        print("✅ Termination protection enabled")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error enabling termination protection: {e.stderr}")
