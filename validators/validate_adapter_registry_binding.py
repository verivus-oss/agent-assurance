#!/usr/bin/env python3
"""Registry binding CLI; structural checks only, with inert citations."""

from _runtime_document_vocab import validate_adapter
from _runtime_validation import cli


def validate(doc, repo_root):
    return validate_adapter(doc, repo_root, binding=True)


if __name__ == "__main__":
    raise SystemExit(cli("adapter-registry-binding"))
