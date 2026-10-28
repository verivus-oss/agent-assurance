# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2021 Taneli Hukkinen
# Licensed to PSF under a Contributor Agreement.

from collections.abc import Callable

# Type annotations
ParseFloat = Callable[[str], object]
Key = tuple[str, ...]
Pos = int
