"""Migracoes de schema versionadas via PRAGMA user_version.

Cada migracao e uma funcao que recebe a conexao e aplica suas mudancas.
A posicao na lista MIGRATIONS define a versao alvo (indice + 1).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable

CATEGORIAS_PADRAO = (
    "Alimentação",
    "Transporte",
    "Moradia",
    "Lazer",
    "Saúde",
    "Outros",
)


def _migracao_v1(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE categoria (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE
        );

        CREATE TABLE gasto (
            id INTEGER PRIMARY KEY,
            valor_centavos INTEGER NOT NULL CHECK (valor_centavos > 0),
            data TEXT NOT NULL,
            categoria_id INTEGER NOT NULL REFERENCES categoria(id),
            descricao TEXT
        );

        CREATE INDEX idx_gasto_data ON gasto(data);
        """
    )
    conn.executemany(
        "INSERT INTO categoria (nome) VALUES (?)",
        [(nome,) for nome in CATEGORIAS_PADRAO],
    )


def _migracao_v2(conn: sqlite3.Connection) -> None:
    # Unicidade de categoria sem depender de maiusculas/minusculas: "Lazer" e
    # "lazer" passam a colidir, evitando categorias duplicadas na pratica.
    conn.execute("CREATE UNIQUE INDEX idx_categoria_nome_nocase ON categoria(nome COLLATE NOCASE)")


MIGRATIONS: tuple[Callable[[sqlite3.Connection], None], ...] = (_migracao_v1, _migracao_v2)


def aplicar_migracoes(conn: sqlite3.Connection) -> None:
    """Aplica todas as migracoes pendentes com base em PRAGMA user_version."""
    versao_atual: int = conn.execute("PRAGMA user_version").fetchone()[0]
    for versao, migracao in enumerate(MIGRATIONS, start=1):
        if versao > versao_atual:
            migracao(conn)
            conn.execute(f"PRAGMA user_version = {versao}")
            conn.commit()
