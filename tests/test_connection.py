"""Testes da abertura da base (arquivo .db), WAL, checkpoint e validacao."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pytest

from poupy.db import connection, migrations
from poupy.db.connection import (
    POUPY_APPLICATION_ID,
    BaseNaoPoupy,
    BaseNaoSQLite,
    BaseVersaoFutura,
    abrir_conexao,
    base_existe,
    fechar_conexao,
    validar_escrita,
)


def _wal(db_path: Path) -> Path:
    return db_path.parent / (db_path.name + "-wal")


def _shm(db_path: Path) -> Path:
    return db_path.parent / (db_path.name + "-shm")


def test_wal_ativo_apos_abrir(base: Path) -> None:
    conn = abrir_conexao(base)
    try:
        modo = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert modo == "wal"
    finally:
        fechar_conexao(conn)


def test_habilitar_wal_loga_quando_nao_engata(caplog: pytest.LogCaptureFixture) -> None:
    # Base em memoria nunca aceita WAL (fica em "memory"): deve registrar aviso.
    conn = sqlite3.connect(":memory:")
    try:
        with caplog.at_level(logging.WARNING, logger=connection.__name__):
            connection._habilitar_wal(conn)
    finally:
        conn.close()
    assert any("WAL" in registro.message for registro in caplog.records)


def test_checkpoint_esvazia_wal_ao_fechar(base: Path) -> None:
    conn = abrir_conexao(base)
    conn.execute(
        "INSERT INTO gasto (valor_centavos, data, categoria_id) VALUES (100, '2026-07-01', 1)"
    )
    conn.commit()
    fechar_conexao(conn)

    wal = _wal(base)
    assert not wal.exists() or wal.stat().st_size == 0


def test_base_existe_ignora_sidecars(base: Path) -> None:
    assert not base_existe(base)
    # Apenas os sidecars, sem o .db, nao contam como base.
    _wal(base).write_text("", encoding="utf-8")
    _shm(base).write_text("", encoding="utf-8")
    assert not base_existe(base)

    fechar_conexao(abrir_conexao(base))
    assert base_existe(base)


def test_validar_escrita(tmp_path: Path) -> None:
    # Pasta gravavel (criada se necessario) a partir do caminho do .db.
    assert validar_escrita(tmp_path / "nova" / "poupy.db")
    # Um arquivo no lugar da pasta impede a escrita.
    arquivo = tmp_path / "arquivo"
    arquivo.write_text("", encoding="utf-8")
    assert not validar_escrita(arquivo / "poupy.db")


def test_base_nova_grava_application_id(base: Path) -> None:
    conn = abrir_conexao(base)
    try:
        assert conn.execute("PRAGMA application_id").fetchone()[0] == POUPY_APPLICATION_ID
        assert conn.execute("PRAGMA user_version").fetchone()[0] == len(migrations.MIGRATIONS)
    finally:
        fechar_conexao(conn)


def test_migracoes_aplicadas_ao_reabrir_base_antiga(
    base: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Base criada por um app "antigo" (apenas as migracoes atuais).
    fechar_conexao(abrir_conexao(base))
    versao_antiga = len(migrations.MIGRATIONS)

    # Um app "mais novo" traz uma migracao adicional.
    def _migracao_extra(conn: sqlite3.Connection) -> None:
        conn.execute("ALTER TABLE gasto ADD COLUMN nota TEXT")

    monkeypatch.setattr(migrations, "MIGRATIONS", (*migrations.MIGRATIONS, _migracao_extra))

    conn = abrir_conexao(base)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == versao_antiga + 1
        colunas = {linha[1] for linha in conn.execute("PRAGMA table_info(gasto)")}
        assert "nota" in colunas
    finally:
        fechar_conexao(conn)


def test_reabrir_base_valida_nao_duplica(base: Path) -> None:
    conn = abrir_conexao(base)
    conn.execute(
        "INSERT INTO gasto (valor_centavos, data, categoria_id) VALUES (100, '2026-07-01', 1)"
    )
    conn.commit()
    fechar_conexao(conn)

    conn = abrir_conexao(base)
    try:
        categorias = conn.execute("SELECT COUNT(*) FROM categoria").fetchone()[0]
        gastos = conn.execute("SELECT COUNT(*) FROM gasto").fetchone()[0]
        assert categorias == len(migrations.CATEGORIAS_PADRAO)
        assert gastos == 1
    finally:
        fechar_conexao(conn)


def test_arquivo_corrompido_recusado(base: Path) -> None:
    base.write_text("nao sou um banco sqlite", encoding="utf-8")
    with pytest.raises(BaseNaoSQLite):
        abrir_conexao(base)


def test_db_de_outro_programa_recusado_e_intacto(tmp_path: Path) -> None:
    outro = tmp_path / "outro.db"
    con = sqlite3.connect(outro)
    con.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT)")
    con.commit()
    con.close()

    with pytest.raises(BaseNaoPoupy):
        abrir_conexao(outro)

    # Permanece intacto: sem tabelas do Poupy e sem sidecar de WAL criado.
    assert not _wal(outro).exists()
    con = sqlite3.connect(outro)
    tabelas = {
        linha[0] for linha in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    con.close()
    assert tabelas == {"clientes"}


def test_base_versao_futura_recusada(base: Path) -> None:
    fechar_conexao(abrir_conexao(base))
    con = sqlite3.connect(base)
    con.execute(f"PRAGMA user_version = {len(migrations.MIGRATIONS) + 1}")
    con.close()

    with pytest.raises(BaseVersaoFutura):
        abrir_conexao(base)


def test_schema_incompleto_recusado(base: Path) -> None:
    # Identidade Poupy, mas sem as tabelas e com user_version ja no topo (nenhuma
    # migracao roda para cria-las): a rede final (_validar_schema) recusa.
    con = sqlite3.connect(base)
    con.execute(f"PRAGMA application_id = {POUPY_APPLICATION_ID}")
    con.execute(f"PRAGMA user_version = {len(migrations.MIGRATIONS)}")
    con.close()

    with pytest.raises(BaseNaoPoupy):
        abrir_conexao(base)
