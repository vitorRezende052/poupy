"""Testes da resolucao da base, WAL e checkpoint no encerramento."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from poupy.db import migrations
from poupy.db.connection import (
    abrir_conexao,
    base_existe,
    fechar_conexao,
    validar_escrita,
)


def test_wal_ativo_apos_abrir(base: Path) -> None:
    conn = abrir_conexao(base)
    try:
        modo = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert modo == "wal"
    finally:
        fechar_conexao(conn)


def test_checkpoint_esvazia_wal_ao_fechar(base: Path) -> None:
    conn = abrir_conexao(base)
    conn.execute(
        "INSERT INTO gasto (valor_centavos, data, categoria_id) VALUES (100, '2026-07-01', 1)"
    )
    conn.commit()
    fechar_conexao(conn)

    wal = base / "poupy.db-wal"
    assert not wal.exists() or wal.stat().st_size == 0


def test_base_existe_ignora_sidecars(base: Path) -> None:
    assert not base_existe(base)
    # Apenas os sidecars, sem poupy.db, nao contam como base.
    (base / "poupy.db-wal").write_text("", encoding="utf-8")
    (base / "poupy.db-shm").write_text("", encoding="utf-8")
    assert not base_existe(base)

    fechar_conexao(abrir_conexao(base))
    assert base_existe(base)


def test_validar_escrita(base: Path) -> None:
    assert validar_escrita(base / "nova")
    # Um arquivo no lugar de uma pasta impede a escrita.
    arquivo = base / "arquivo"
    arquivo.write_text("", encoding="utf-8")
    assert not validar_escrita(arquivo / "sub")


def test_migracoes_aplicadas_em_base_nova(base: Path) -> None:
    conn = abrir_conexao(base)
    try:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
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


def test_base_invalida_levanta(base: Path) -> None:
    (base / "poupy.db").write_text("nao sou um banco sqlite", encoding="utf-8")
    with pytest.raises(sqlite3.DatabaseError):
        abrir_conexao(base)
