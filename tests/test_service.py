"""Testes da camada de servico."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pytest

from poupy.db.connection import abrir_conexao
from poupy.services.gastos import GastoService


def test_registrar_gasto_persiste(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    gasto = service.registrar_gasto(1500, date(2026, 7, 10), 1, "  Almoco  ")

    assert gasto.id > 0
    assert gasto.descricao == "Almoco"  # trimmed
    assert gasto.categoria_nome == "Alimentação"
    assert service.total_do_mes("2026-07") == 1500


def test_descricao_vazia_vira_none(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    gasto = service.registrar_gasto(1000, date(2026, 7, 1), 1, "   ")
    assert gasto.descricao is None


def test_valor_invalido_rejeitado(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    with pytest.raises(ValueError):
        service.registrar_gasto(0, date(2026, 7, 1), 1, None)


def test_criar_categoria_valida_nome(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    categoria = service.criar_categoria("  Viagem  ")
    assert categoria.nome == "Viagem"
    with pytest.raises(ValueError):
        service.criar_categoria("   ")


def test_criar_categoria_duplicada_rejeitada(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    existente = service.categorias()[0].nome
    # Nome duplicado vira ValueError amigavel, nao um sqlite3.IntegrityError cru.
    with pytest.raises(ValueError):
        service.criar_categoria(existente)


def test_atualizar_gasto_persiste(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    gasto = service.registrar_gasto(1500, date(2026, 7, 10), 1, "Almoco")

    service.atualizar_gasto(gasto.id, 2000, date(2026, 7, 11), 2, "Jantar")

    atualizado = service.gastos_do_mes("2026-07")[0]
    assert atualizado.valor_centavos == 2000
    assert atualizado.categoria_id == 2
    assert atualizado.descricao == "Jantar"
    assert atualizado.data == date(2026, 7, 11)


def test_atualizar_valor_invalido_rejeitado(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    gasto = service.registrar_gasto(1500, date(2026, 7, 10), 1, None)
    with pytest.raises(ValueError):
        service.atualizar_gasto(gasto.id, 0, date(2026, 7, 10), 1, None)


def test_excluir_gasto(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    gasto = service.registrar_gasto(1500, date(2026, 7, 10), 1, None)
    service.excluir_gasto(gasto.id)
    assert service.total_do_mes("2026-07") == 0


def test_persistencia_apos_reabrir(caminho_db: Path) -> None:
    conn = abrir_conexao(caminho_db)
    GastoService(conn).registrar_gasto(4200, date(2026, 7, 5), 1, "Cafe")
    conn.close()

    conn = abrir_conexao(caminho_db)
    service = GastoService(conn)
    assert service.total_do_mes("2026-07") == 4200
    assert service.gastos_do_mes("2026-07")[0].descricao == "Cafe"
    conn.close()
