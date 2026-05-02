__all__ = ("signer",)

import sys


def signer():
    from telegram_signer import cli

    sys.exit(cli.telegram_signer())

