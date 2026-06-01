"""Thin wrapper for the saltpost command-line interface."""

from __future__ import annotations

from saltpost.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
