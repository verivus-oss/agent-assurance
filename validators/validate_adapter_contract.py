#!/usr/bin/env python3
"""Adapter contract CLI; INV01..INV03 and required sections, INV04 scope boundary."""

from _runtime_document_vocab import validate_adapter
from _runtime_validation import cli

validate = validate_adapter

if __name__ == "__main__":
    raise SystemExit(cli("adapter-contract"))
