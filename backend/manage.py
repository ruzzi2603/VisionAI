#!/usr/bin/env python
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root.parent / ".env")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
