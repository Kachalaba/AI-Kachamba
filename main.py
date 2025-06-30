import argparse
import asyncio
import logging
import sys
from importlib import import_module
from types import ModuleType
from typing import Callable, Dict

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")


SubCommand = Callable[[list[str]], None]


def _lazy_import(name: str) -> ModuleType:
    """Import module only when its sub-command is invoked."""
    return import_module(name)


def _run_autopost(_: list[str]) -> None:
    module = _lazy_import("autopost")
    module.main()


def _run_bot(_: list[str]) -> None:
    module = _lazy_import("bot")
    module.main()


def _run_digest(_: list[str]) -> None:
    module = _lazy_import("news_digest")
    module.main()


COMMANDS: Dict[str, SubCommand] = {
    "autopost": _run_autopost,
    "bot": _run_bot,
    "news-digest": _run_digest,
}


def main(argv: list[str] | None = None) -> None:
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(description="AI-Kachamba unified CLI")
    parser.add_argument("command", choices=COMMANDS.keys(), help="Which sub-command to run")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments forwarded to sub-command")
    ns = parser.parse_args(argv)

    COMMANDS[ns.command](ns.args)


if __name__ == "__main__":
    main()
