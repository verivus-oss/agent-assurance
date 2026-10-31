"""Fixed-token parsing for verification output."""


def contains_table_diagnostic(output: str, table: str, count: int) -> bool:
    expected = [table, str(count), "!=" if count else "==", "0"]
    return any(line.split()[:4] == expected for line in output.splitlines())
