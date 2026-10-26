"""Exact-option argument parsing for repository commands.

Only the interface used by this repository is provided. Every option token is
compared as a fixed string; no pattern engine participates in dispatch.
"""

from __future__ import annotations

import sys
from typing import Any, Callable


_MISSING = object()


class Namespace:
    def __init__(self, **values: Any) -> None:
        self.__dict__.update(values)


class _Argument:
    def __init__(
        self,
        name: str,
        destination: str,
        positional: bool,
        action: str | None,
        nargs: str | None,
        converter: Callable[[str], Any],
        choices: tuple[Any, ...] | None,
        required: bool,
        default: Any,
        help: str | None,
        metavar: str | None,
        version: str | None,
    ) -> None:
        self.name = name
        self.destination = destination
        self.positional = positional
        self.action = action
        self.nargs = nargs
        self.converter = converter
        self.choices = choices
        self.required = required
        self.default = default
        self.help = help
        self.metavar = metavar
        self.version = version


class _Group:
    def __init__(self, parser: ArgumentParser, required: bool) -> None:
        self.parser = parser
        self.required = required
        self.arguments: list[_Argument] = []

    def add_argument(self, name: str, **options: Any) -> _Argument:
        argument = self.parser.add_argument(name, **options)
        self.arguments.append(argument)
        return argument


class _Subparsers:
    def __init__(self, destination: str, required: bool) -> None:
        self.destination = destination
        self.required = required
        self.parsers: dict[str, ArgumentParser] = {}

    def add_parser(self, name: str, **options: Any) -> ArgumentParser:
        if name in self.parsers:
            raise ValueError("duplicate subcommand: " + name)
        parser = ArgumentParser(description=options.get("description"), prog=name)
        self.parsers[name] = parser
        return parser


class ArgumentParser:
    def __init__(self, *, description: str | None = None, prog: str | None = None) -> None:
        self.description = description
        self.prog = prog or sys.argv[0]
        self.arguments: list[_Argument] = []
        self.groups: list[_Group] = []
        self.subparsers: _Subparsers | None = None

    def add_argument(
        self,
        name: str,
        *,
        action: str | None = None,
        choices: tuple[Any, ...] | list[Any] | None = None,
        default: Any = _MISSING,
        dest: str | None = None,
        help: str | None = None,
        metavar: str | None = None,
        nargs: str | None = None,
        required: bool = False,
        type: Callable[[str], Any] = str,
        version: str | None = None,
    ) -> _Argument:
        if not isinstance(name, str) or not name or name.startswith("-") and not name.startswith("--"):
            raise ValueError("only named positionals and long options are supported")
        if action not in (None, "store_true", "store_false", "append", "version"):
            raise ValueError("unsupported argument action")
        if nargs not in (None, "?", "*", "+"):
            raise ValueError("unsupported argument arity")
        if default is _MISSING:
            default = False if action == "store_true" else True if action == "store_false" else None
        argument = _Argument(name, dest or name.lstrip("-").replace("-", "_"),
                             not name.startswith("--"), action, nargs, type,
                             tuple(choices) if choices is not None else None,
                             required, default, help, metavar, version)
        if any(existing.name == argument.name for existing in self.arguments):
            raise ValueError("duplicate argument: " + name)
        self.arguments.append(argument)
        return argument

    def add_mutually_exclusive_group(self, *, required: bool = False) -> _Group:
        group = _Group(self, required)
        self.groups.append(group)
        return group

    def add_subparsers(self, *, dest: str, required: bool = False) -> _Subparsers:
        if self.subparsers is not None:
            raise ValueError("only one subcommand selector is supported")
        self.subparsers = _Subparsers(dest, required)
        return self.subparsers

    def _help(self, child: ArgumentParser | None = None) -> str:
        lines = ["usage: " + self.prog + " [options]"]
        if self.description:
            lines.extend(("", self.description))
        lines.extend(("", "options:", "  --help  show this help message and exit"))
        for argument in self.arguments + (child.arguments if child else []):
            label = argument.name
            if argument.positional:
                label = argument.metavar or label
            elif argument.action not in ("store_true", "store_false", "version"):
                label += " " + (argument.metavar or argument.destination.upper())
            lines.append("  " + label + ("  " + argument.help if argument.help else ""))
        if self.subparsers:
            lines.append("subcommands: " + ", ".join(self.subparsers.parsers))
        return "\n".join(lines)

    def error(self, message: str) -> None:
        print(self._help().splitlines()[0], file=sys.stderr)
        print(self.prog + ": error: " + message, file=sys.stderr)
        raise SystemExit(2)

    def parse_args(self, args: list[str] | None = None) -> Namespace:
        tokens = list(sys.argv[1:] if args is None else args)
        child: ArgumentParser | None = None
        if self.subparsers:
            parent_options = {argument.name: argument for argument in self.arguments if not argument.positional}
            cursor = 0
            while cursor < len(tokens) and tokens[cursor] != "--":  # nosec B105  # noqa: S105
                token = tokens[cursor]
                name, equals, _ = token.partition("=")
                option = parent_options.get(name)
                if option is not None:
                    cursor += 1
                    if not equals and option.action not in ("store_true", "store_false", "version"):
                        if option.nargs in ("*", "+"):
                            self.error("variable arity before a subcommand is unsupported")
                        cursor += 1
                    continue
                if token.startswith("--"):
                    cursor += 1
                    continue
                child = self.subparsers.parsers.get(token)
                if child is None:
                    self.error("unrecognized subcommand: " + token)
                tokens.pop(cursor)
                break
        arguments = self.arguments + (child.arguments if child else [])
        help_tokens = tokens[:tokens.index("--")] if "--" in tokens else tokens  # nosec B105  # noqa: S105
        if "--help" in help_tokens:
            print(self._help(child))
            raise SystemExit(0)
        by_name = {argument.name: argument for argument in arguments if not argument.positional}
        positionals = [argument for argument in arguments if argument.positional]
        if len(positionals) > 1:
            raise ValueError("multiple positional arguments are unsupported")
        values = {argument.destination: argument.default for argument in arguments}
        if self.subparsers:
            values[self.subparsers.destination] = next(
                (name for name, parser in self.subparsers.parsers.items() if parser is child), None
            )
        seen: set[str] = set()
        positional_values: list[str] = []
        index = 0
        literal_mode = False
        while index < len(tokens):
            token = tokens[index]
            if token == "--" and not literal_mode:  # nosec B105  # noqa: S105
                literal_mode = True
                index += 1
                continue
            name, equals, attached = token.partition("=")
            if not literal_mode and name.startswith("--"):
                argument = by_name.get(name)
                if argument is None:
                    self.error("unrecognized argument: " + token)
                if argument.action == "version":
                    print(argument.version or "")
                    raise SystemExit(0)
                if argument.action in ("store_true", "store_false"):
                    if equals:
                        self.error("option does not accept a value: " + name)
                    values[argument.destination] = argument.action == "store_true"
                    seen.add(argument.name)
                    index += 1
                    continue
                collected = [attached] if equals else []
                index += 1
                if argument.nargs in ("*", "+"):
                    while index < len(tokens) and tokens[index] != "--" and not tokens[index].startswith("--"):
                        collected.append(tokens[index])
                        index += 1
                    if argument.nargs == "+" and not collected:
                        self.error("option requires at least one value: " + name)
                else:
                    if not collected:
                        if index == len(tokens) or tokens[index].startswith("--"):
                            self.error("option requires a value: " + name)
                        collected.append(tokens[index])
                        index += 1
                converted = [self._convert(argument, value) for value in collected]
                if argument.action == "append":
                    if values[argument.destination] is None:
                        values[argument.destination] = []
                    values[argument.destination].extend(converted)
                elif argument.nargs in ("*", "+"):
                    values[argument.destination] = converted
                else:
                    values[argument.destination] = converted[0]
                seen.add(argument.name)
                continue
            positional_values.append(token)
            index += 1
        if positionals:
            argument = positionals[0]
            if argument.nargs in ("*", "+"):
                if argument.nargs == "+" and not positional_values:
                    self.error("missing required argument: " + argument.name)
                values[argument.destination] = [self._convert(argument, value) for value in positional_values]
            elif argument.nargs == "?":
                if len(positional_values) > 1:
                    self.error("too many positional arguments")
                if positional_values:
                    values[argument.destination] = self._convert(argument, positional_values[0])
            else:
                if len(positional_values) != 1:
                    self.error("expected one positional argument: " + argument.name)
                values[argument.destination] = self._convert(argument, positional_values[0])
        elif positional_values:
            self.error("unrecognized positional arguments: " + " ".join(positional_values))
        for argument in arguments:
            if argument.required and argument.name not in seen:
                self.error("missing required option: " + argument.name)
        for group in self.groups + (child.groups if child else []):
            count = sum(argument.name in seen for argument in group.arguments)
            if count > 1 or group.required and count != 1:
                self.error("exactly one of these options is required: " + ", ".join(arg.name for arg in group.arguments))
        if self.subparsers and self.subparsers.required and child is None:
            self.error("a subcommand is required")
        return Namespace(**values)

    def _convert(self, argument: _Argument, value: str) -> Any:
        try:
            converted = argument.converter(value)
        except (ValueError, TypeError) as exc:
            self.error("invalid value for " + argument.name + ": " + str(exc))
        if argument.choices is not None and converted not in argument.choices:
            self.error("invalid choice for " + argument.name + ": " + str(converted))
        return converted
