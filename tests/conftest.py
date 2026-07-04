"""Fixtures compartilhadas dos testes."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from poupy.db.connection import abrir_conexao


@pytest.fixture
def base(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def conn(base: Path) -> Iterator[sqlite3.Connection]:
    conexao = abrir_conexao(base)
    try:
        yield conexao
    finally:
        conexao.close()
