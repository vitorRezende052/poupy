"""Fixtures compartilhadas dos testes."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from poupy.db.connection import abrir_conexao


@pytest.fixture
def caminho_db(tmp_path: Path) -> Path:
    return tmp_path / "poupy.db"


@pytest.fixture
def conn(caminho_db: Path) -> Iterator[sqlite3.Connection]:
    conexao = abrir_conexao(caminho_db)
    try:
        yield conexao
    finally:
        conexao.close()
