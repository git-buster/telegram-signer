import asyncio
import os
import pathlib
from contextlib import contextmanager
from typing import Optional

import click

from telegram_signer.core import UserSigner
from telegram_signer.sign_record_store import SignRecordStore

MAX_PARALLEL_ACCOUNTS = 5


def build_signer(
    ctx_obj: dict,
    task_name: Optional[str] = None,
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> UserSigner:
    return UserSigner(
        task_name=task_name,
        account=ctx_obj["account"],
        session_dir=ctx_obj["session_dir"],
        workdir=ctx_obj["workdir"],
        session_string=ctx_obj["session_string"],
        in_memory=ctx_obj["in_memory"],
        loop=loop,
    )


@contextmanager
def account_run_slot(ctx_obj: dict):
    lock_root = pathlib.Path(ctx_obj["workdir"]) / ".run-locks"
    lock_root.mkdir(parents=True, exist_ok=True)
    lock_path = lock_root / f"{ctx_obj['account']}.{os.getpid()}.lock"
    active_locks = [path for path in lock_root.glob("*.lock") if path.is_file()]
    if len(active_locks) >= MAX_PARALLEL_ACCOUNTS:
        raise click.UsageError(
            f"At most {MAX_PARALLEL_ACCOUNTS} accounts may run at the same time."
        )
    lock_path.write_text(str(os.getpid()), encoding="utf-8")
    try:
        yield
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


@click.group(
    name="telegram-signer",
    help=(
        "Telegram check-in scheduler. Usage: "
        "telegram-signer <account> <command> [arguments]"
    ),
)
@click.argument("account")
@click.option(
    "--log-level",
    "-l",
    default="info",
    show_default=True,
    type=click.Choice(["debug", "info", "warn", "error"], case_sensitive=False),
    help="Logging level.",
)
@click.option(
    "--log-file",
    default="logs/telegram-signer.log",
    show_default=True,
    type=click.Path(),
    help="Log file path.",
)
@click.option(
    "--log-dir",
    default="logs",
    show_default=True,
    type=click.Path(),
    help="Directory for log files.",
)
@click.option(
    "--session-dir",
    default=".",
    show_default=True,
    type=click.Path(),
    help="Directory used to store Telegram session files.",
)
@click.option(
    "--workdir",
    "-w",
    default=".signer",
    show_default=True,
    type=click.Path(),
    help="Directory used to store check-in configs, state, and records.",
)
@click.option(
    "--session-string",
    default=None,
    show_default=True,
    show_envvar=True,
    envvar="TG_SESSION_STRING",
    help="Telegram session string. Overrides TG_SESSION_STRING when provided.",
)
@click.option(
    "--in-memory",
    default=False,
    is_flag=True,
    help="Keep the Telegram session in memory instead of writing a session file.",
)
@click.pass_context
def telegram_signer(
    ctx: click.Context,
    account: str,
    log_level: str,
    log_file: str,
    log_dir: str,
    session_dir: str,
    workdir: str,
    session_string: str,
    in_memory: bool,
):
    from telegram_signer.logger import configure_logger

    if not account.strip():
        raise click.UsageError("Account is required.")

    logger = configure_logger(log_level=log_level, log_dir=log_dir, log_file=log_file)
    logger.info("Using account: %s", account)

    ctx.ensure_object(dict)
    ctx.obj.update(
        {
            "account": account,
            "session_dir": session_dir,
            "workdir": workdir,
            "session_string": session_string,
            "in_memory": in_memory,
        }
    )


@telegram_signer.command(help="Print the package version.")
def version():
    from telegram_signer import __version__

    click.echo(f"telegram-signer {__version__}")


@telegram_signer.command(help="Create or refresh the Telegram session.")
@click.option(
    "--num-of-dialogs",
    "-n",
    default=50,
    show_default=True,
    type=int,
    help="Number of recent dialogs to display after login.",
)
@click.pass_obj
def login(obj, num_of_dialogs: int):
    signer = build_signer(obj)
    signer.app_run(signer.login(num_of_dialogs))


@telegram_signer.command(help="Log out and remove the Telegram session.")
@click.pass_obj
def logout(obj):
    signer = build_signer(obj)
    signer.app_run(signer.logout())


@telegram_signer.command(help="Run one check-in task continuously by schedule.")
@click.argument("task_name")
@click.option(
    "--num-of-dialogs",
    "-n",
    default=50,
    show_default=True,
    type=int,
    help="Number of recent dialogs to display while bootstrapping.",
)
@click.pass_obj
def run(obj, task_name: str, num_of_dialogs: int):
    signer = build_signer(obj, task_name=task_name)
    with account_run_slot(obj):
        signer.app_run(signer.run(num_of_dialogs))


@telegram_signer.command(name="run-force", help="Force one immediate check-in run.")
@click.argument("task_name")
@click.option(
    "--num-of-dialogs",
    "-n",
    default=50,
    show_default=True,
    type=int,
    help="Number of recent dialogs to display while bootstrapping.",
)
@click.pass_obj
def force_run(obj, task_name: str, num_of_dialogs: int):
    signer = build_signer(obj, task_name=task_name)
    with account_run_slot(obj):
        signer.app_run(signer.force_run(num_of_dialogs))


@telegram_signer.command(help="List check-in task names.")
@click.pass_obj
def list(obj):
    signer = build_signer(obj)
    signer.list_()


@telegram_signer.command(help="Interactively create or update a check-in task.")
@click.argument("task_name")
@click.pass_obj
def reconfig(obj, task_name: str):
    signer = build_signer(obj, task_name=task_name)
    signer.reconfig()


@telegram_signer.command(name="list-records", help="List recent check-in records.")
@click.argument("task_name", required=False)
@click.option("--limit", "-n", default=10, show_default=True, type=int)
@click.option("--user-id", default=None, help="Filter by Telegram user id.")
@click.pass_obj
def list_records(obj, task_name: str | None, limit: int, user_id: str | None):
    store = SignRecordStore(obj["workdir"])
    records = store.list_recent_records(
        limit=limit, task_name=task_name, user_id=user_id
    )
    if not records:
        click.echo("No SQLite check-in records found.")
        return
    for record in records:
        click.echo(
            f"{record.signed_at} | task={record.task_name} | "
            f"user={record.user_id} | date={record.sign_date} | source={record.source}"
        )


@telegram_signer.command(
    name="migrate-records",
    help="Migrate legacy sign_record.json files into SQLite.",
)
@click.option(
    "--legacy-user-id",
    default=None,
    help="User id to use for legacy signs/<task>/sign_record.json files.",
)
@click.option(
    "--delete-json",
    default=False,
    is_flag=True,
    help="Delete migrated JSON files after a successful migration.",
)
@click.pass_obj
def migrate_records(obj, legacy_user_id: str | None, delete_json: bool):
    store = SignRecordStore(obj["workdir"])
    summary = store.migrate_all_json_records(
        legacy_user_id=legacy_user_id,
        remove_files=delete_json,
        account=obj["account"],
    )
    click.echo(f"SQLite database: {store.db_path}")
    click.echo(f"Migrated files: {summary.migrated_files}")
    click.echo(f"Migrated records: {summary.migrated_records}")
    if delete_json:
        click.echo(f"Deleted JSON files: {summary.removed_files}")
    if summary.skipped_files:
        click.echo("Skipped files:")
        for path in summary.skipped_files:
            click.echo(f"  - {path}")


@telegram_signer.command(name="llm-config", help="Configure OpenAI-compatible API.")
@click.pass_obj
def llm_config(obj):
    from telegram_signer.ai_tools import OpenAIConfigManager

    OpenAIConfigManager(obj["workdir"]).ask_for_config()
