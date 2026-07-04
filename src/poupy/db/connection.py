"""Conexao com o SQLite local dentro da pasta da base ativa.

A responsabilidade de "onde fica o poupy.db" e da base ativa (uma pasta
escolhida pelo usuario no onboarding), nao mais de AppDataLocation.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from poupy.db.migrations import aplicar_migracoes


def caminho_banco(base: Path) -> Path:
    """Caminho do poupy.db dentro da pasta da base."""
    return Path(base) / "poupy.db"


def base_existe(pasta: Path) -> bool:
    """Ha uma base na pasta? Olha SOMENTE o poupy.db, ignora sidecars -wal/-shm."""
    return caminho_banco(pasta).is_file()


def validar_escrita(pasta: Path) -> bool:
    """Verifica permissao de escrita, criando a pasta se necessario."""
    pasta = Path(pasta)
    try:
        pasta.mkdir(parents=True, exist_ok=True)
        teste = pasta / ".poupy_write_test"
        teste.write_text("", encoding="utf-8")
        teste.unlink()
        return True
    except OSError:
        return False


def abrir_conexao(base: Path) -> sqlite3.Connection:
    """Abre (ou cria) o poupy.db da base, habilita WAL e aplica migracoes.

    Levanta sqlite3.DatabaseError se o poupy.db existente nao for um banco
    Poupy legivel (arquivo corrompido ou de outro app).
    """
    Path(base).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(caminho_banco(base))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    aplicar_migracoes(conn)
    _validar_schema(conn)
    return conn


def fechar_conexao(conn: sqlite3.Connection) -> None:
    """Faz checkpoint do WAL e fecha, deixando o poupy.db integro para copia."""
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()


def _validar_schema(conn: sqlite3.Connection) -> None:
    tabelas = {
        linha[0]
        for linha in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    if not {"categoria", "gasto"} <= tabelas:
        raise sqlite3.DatabaseError("O arquivo nao e um banco Poupy valido.")
