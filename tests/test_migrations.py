"""Testes das migracoes e do schema."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from poupy.db.connection import abrir_conexao
from poupy.db.migrations import CATEGORIAS_PADRAO


def test_schema_e_seed(conn: sqlite3.Connection) -> None:
    assert conn.execute("PRAGMA user_version").fetchone()[0] == 1

    tabelas = {
        linha[0]
        for linha in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    assert {"categoria", "gasto"} <= tabelas

    nomes = {linha["nome"] for linha in conn.execute("SELECT nome FROM categoria")}
    assert nomes == set(CATEGORIAS_PADRAO)


def test_migracao_idempotente(base: Path) -> None:
    conn = abrir_conexao(base)
    conn.execute(
        "INSERT INTO gasto (valor_centavos, data, categoria_id) VALUES (100, '2026-07-01', 1)"
    )
    conn.commit()
    conn.close()

    # Reabrir nao deve reaplicar a migracao nem duplicar categorias.
    conn = abrir_conexao(base)
    assert conn.execute("SELECT COUNT(*) FROM categoria").fetchone()[0] == len(CATEGORIAS_PADRAO)
    assert conn.execute("SELECT COUNT(*) FROM gasto").fetchone()[0] == 1
    conn.close()


def test_valor_negativo_rejeitado(conn: sqlite3.Connection) -> None:
    import pytest

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO gasto (valor_centavos, data, categoria_id) VALUES (-5, '2026-07-01', 1)"
        )
