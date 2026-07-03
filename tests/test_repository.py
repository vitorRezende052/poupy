"""Testes do repositorio de acesso a dados."""

from __future__ import annotations

import sqlite3
from datetime import date

from poupy.db import repository


def test_criar_e_listar_categoria(conn: sqlite3.Connection) -> None:
    categoria = repository.criar_categoria(conn, "Viagem")
    assert categoria.id > 0
    nomes = [c.nome for c in repository.listar_categorias(conn)]
    assert "Viagem" in nomes
    assert nomes == sorted(nomes)  # ordenado por nome


def test_inserir_e_listar_gastos_do_mes(conn: sqlite3.Connection) -> None:
    repository.inserir_gasto(conn, 1500, date(2026, 7, 10), 1, "Almoco")
    repository.inserir_gasto(conn, 2500, date(2026, 7, 20), 2, None)
    repository.inserir_gasto(conn, 9900, date(2026, 6, 30), 1, "Mes anterior")

    gastos = repository.gastos_do_mes(conn, "2026-07")
    assert [g.valor_centavos for g in gastos] == [2500, 1500]  # mais recente primeiro
    assert gastos[1].descricao == "Almoco"
    assert gastos[1].categoria_nome == "Alimentacao"


def test_total_do_mes_soma_apenas_o_mes(conn: sqlite3.Connection) -> None:
    repository.inserir_gasto(conn, 1500, date(2026, 7, 10), 1, None)
    repository.inserir_gasto(conn, 2500, date(2026, 7, 20), 2, None)
    repository.inserir_gasto(conn, 9900, date(2026, 6, 30), 1, None)

    assert repository.total_do_mes(conn, "2026-07") == 4000
    assert repository.total_do_mes(conn, "2026-08") == 0
