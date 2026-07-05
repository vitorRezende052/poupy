"""Conexao com a base ativa, que e o proprio arquivo .db escolhido pelo usuario.

A base e um arquivo .db com nome livre em qualquer pasta; os sidecars do WAL
(-wal/-shm) sao gerados pelo SQLite ao lado dele. Ao abrir uma base EXISTENTE,
valida-se a IDENTIDADE do arquivo (SQLite integro, banco Poupy, versao
nao-futura) ANTES de habilitar o WAL ou aplicar migracoes, para nunca sujar um
arquivo alheio com as tabelas do Poupy.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from poupy.db.migrations import MIGRATIONS, aplicar_migracoes

# Identidade do formato de banco do Poupy, gravada em PRAGMA application_id na
# criacao da base. Sao os bytes ASCII de "POUY" (0x504F5559). Serve para
# reconhecer um .db do Poupy e recusar arquivos de outros programas.
POUPY_APPLICATION_ID = 0x504F5559


class BaseInvalida(Exception):
    """Base que nao pode ser aberta com seguranca. Ver as subclasses."""


class BaseNaoSQLite(BaseInvalida):
    """O arquivo nao e um banco SQLite integro."""


class BaseNaoPoupy(BaseInvalida):
    """E um SQLite integro, mas nao e um banco do Poupy (application_id difere)."""


class BaseVersaoFutura(BaseInvalida):
    """Base criada por uma versao mais nova do Poupy (user_version no futuro)."""


def base_existe(db_path: Path) -> bool:
    """Ha uma base no caminho? Olha SOMENTE o arquivo .db, ignora os sidecars."""
    return Path(db_path).is_file()


def validar_escrita(db_path: Path) -> bool:
    """Verifica escrita na PASTA que contera o .db (onde o WAL sera criado).

    Cria a pasta se necessario. Recebe o caminho do ARQUIVO .db e testa a pasta
    que o conteria (``db_path.parent``).
    """
    pasta = Path(db_path).parent
    try:
        pasta.mkdir(parents=True, exist_ok=True)
        teste = pasta / ".poupy_write_test"
        teste.write_text("", encoding="utf-8")
        teste.unlink()
        return True
    except OSError:
        return False


def abrir_conexao(db_path: Path) -> sqlite3.Connection:
    """Abre a base do arquivo .db, habilita WAL e garante o schema.

    Arquivo inexistente -> base NOVA: grava o application_id do Poupy e aplica as
    migracoes. Arquivo existente -> valida a IDENTIDADE (SQLite integro, banco
    Poupy, versao nao-futura) ANTES de habilitar o WAL ou migrar, e so entao
    aplica as migracoes. Levanta uma subclasse de BaseInvalida se a base
    existente nao puder ser aberta com seguranca.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    nova = not db_path.is_file()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        if nova:
            conn.execute("PRAGMA journal_mode = WAL")
            _inicializar_base_nova(conn)
        else:
            # Identidade primeiro, com PRAGMAs somente-leitura: um arquivo alheio
            # ou corrompido e recusado sem ganhar WAL nem tabelas do Poupy.
            _validar_identidade(conn)
            conn.execute("PRAGMA journal_mode = WAL")
            aplicar_migracoes(conn)
            _validar_schema(conn)
    except BaseInvalida:
        conn.close()
        raise
    return conn


def fechar_conexao(conn: sqlite3.Connection) -> None:
    """Faz checkpoint do WAL e fecha, deixando o .db integro para copia."""
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    conn.close()


def _inicializar_base_nova(conn: sqlite3.Connection) -> None:
    conn.execute(f"PRAGMA application_id = {POUPY_APPLICATION_ID}")
    aplicar_migracoes(conn)


def _validar_identidade(conn: sqlite3.Connection) -> None:
    """Camadas de identidade, NESTA ORDEM, antes de qualquer escrita/migracao."""
    try:
        integridade = conn.execute("PRAGMA integrity_check").fetchone()[0]
    except sqlite3.DatabaseError as erro:
        raise BaseNaoSQLite("O arquivo não é um banco válido.") from erro
    if integridade != "ok":
        raise BaseNaoSQLite("O arquivo não é um banco válido.")

    app_id = conn.execute("PRAGMA application_id").fetchone()[0]
    if app_id != POUPY_APPLICATION_ID:
        raise BaseNaoPoupy("O arquivo não é um banco do Poupy.")

    versao = conn.execute("PRAGMA user_version").fetchone()[0]
    if versao > len(MIGRATIONS):
        raise BaseVersaoFutura(
            "Base criada por uma versão mais nova do Poupy; atualize o app."
        )


def _validar_schema(conn: sqlite3.Connection) -> None:
    tabelas = {
        linha[0]
        for linha in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    if not {"categoria", "gasto"} <= tabelas:
        raise BaseNaoPoupy("O arquivo não é um banco Poupy válido.")
