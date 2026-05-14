"""Shared CLI option-parsing helpers."""

from __future__ import annotations

import json
from typing import Optional

import typer


def parse_str_list(raw: Optional[str], flag: str) -> Optional[list[str]]:
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        typer.echo(f"{flag} is not valid JSON: {e}", err=True)
        raise typer.Exit(code=2)
    if not isinstance(parsed, list):
        typer.echo(f"{flag} must be a JSON array of strings.", err=True)
        raise typer.Exit(code=2)
    return parsed


def parse_dict(raw: Optional[str], flag: str) -> Optional[dict]:
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        typer.echo(f"{flag} is not valid JSON: {e}", err=True)
        raise typer.Exit(code=2)
    if not isinstance(parsed, dict):
        typer.echo(f"{flag} must be a JSON object.", err=True)
        raise typer.Exit(code=2)
    return parsed


def parse_list_of_dicts(raw: Optional[str], flag: str) -> Optional[list[dict]]:
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        typer.echo(f"{flag} is not valid JSON: {e}", err=True)
        raise typer.Exit(code=2)
    if not isinstance(parsed, list):
        typer.echo(f"{flag} must be a JSON array.", err=True)
        raise typer.Exit(code=2)
    return parsed
