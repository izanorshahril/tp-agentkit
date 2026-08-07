#!/usr/bin/env python3
"""Compatibility wrapper for the neutral HTML diff converter entry point."""

from __future__ import annotations

from html_diff_converter import main


if __name__ == "__main__":
    raise SystemExit(main())
