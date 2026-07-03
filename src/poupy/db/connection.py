"""Conexao com o SQLite local e localizacao do arquivo de dados."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from poupy.db.migrations import aplicar_migracoes


def caminho_banco() -> Path:
    """Caminho do arquivo de banco em AppDataLocation, criando o diretorio."""
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    diretorio = Path(base)
    diretorio.mkdir(parents=True, exist_ok=True)
    return diretorio / "poupy.db"


def abrir_conexao(caminho: Path | str) -> sqlite3.Connection:
    """Abre a conexao, habilita chaves estrangeiras e aplica migracoes."""
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    aplicar_migracoes(conn)
    return conn
