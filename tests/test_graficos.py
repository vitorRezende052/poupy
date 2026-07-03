"""Testes dos dados de graficos (servico)."""

from __future__ import annotations

import sqlite3
from datetime import date

from poupy.services.gastos import GastoService


def test_gastos_por_categoria_ordenado_desc(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    service.registrar_gasto(1000, date(2026, 7, 1), 1, None)  # Alimentacao
    service.registrar_gasto(500, date(2026, 7, 2), 1, None)  # Alimentacao
    service.registrar_gasto(2000, date(2026, 7, 3), 2, None)  # Transporte

    dados = service.gastos_por_categoria("2026-07")
    assert dados[0] == ("Transporte", 2000)
    assert dados[1] == ("Alimentacao", 1500)
    # Mes sem gastos retorna vazio.
    assert service.gastos_por_categoria("2026-08") == []


def test_evolucao_mensal_preenche_meses_vazios(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    service.registrar_gasto(1000, date(2026, 5, 1), 1, None)
    service.registrar_gasto(3000, date(2026, 7, 1), 1, None)

    evolucao = service.evolucao_mensal()
    como_dict = dict(evolucao)
    assert como_dict["2026-05"] == 1000
    assert como_dict["2026-06"] == 0  # mes sem lancamento, preenchido com 0
    assert como_dict["2026-07"] == 3000
    # Cobre o intervalo continuo do primeiro mes ate hoje.
    assert [mes for mes, _ in evolucao] == service.meses_disponiveis()
