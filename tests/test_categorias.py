"""Testes de gestao de categorias (servico e UI)."""

from __future__ import annotations

import sqlite3
from datetime import date

import pytest
from PySide6.QtWidgets import QMessageBox
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from poupy.services.gastos import GastoService
from poupy.ui.categorias_dialog import CategoriasDialog


def test_renomear_categoria(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    categoria = service.categorias()[0]
    service.renomear_categoria(categoria.id, "  Renomeada  ")
    nomes = [c.nome for c in service.categorias()]
    assert "Renomeada" in nomes


def test_renomear_nome_vazio_rejeitado(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    categoria = service.categorias()[0]
    with pytest.raises(ValueError):
        service.renomear_categoria(categoria.id, "   ")


def test_renomear_nome_duplicado_rejeitado(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    categorias = service.categorias()
    with pytest.raises(ValueError):
        service.renomear_categoria(categorias[0].id, categorias[1].nome)


def test_excluir_categoria_sem_gastos(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    nova = service.criar_categoria("Descartavel")
    service.excluir_categoria(nova.id)
    assert "Descartavel" not in [c.nome for c in service.categorias()]


def test_excluir_categoria_em_uso_bloqueada(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    categoria = service.categorias()[0]
    service.registrar_gasto(1000, date(2026, 7, 1), categoria.id, None)
    with pytest.raises(ValueError):
        service.excluir_categoria(categoria.id)
    # Continua existindo.
    assert categoria.id in [c.id for c in service.categorias()]


def test_dialog_cria_categoria(
    conn: sqlite3.Connection, qtbot: QtBot, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "poupy.ui.categorias_dialog.QInputDialog.getText",
        lambda *args, **kwargs: ("Nova", True),
    )
    service = GastoService(conn)
    total_inicial = len(service.categorias())

    dialog = CategoriasDialog(service)
    qtbot.addWidget(dialog)
    dialog._criar()

    assert "Nova" in [c.nome for c in service.categorias()]
    assert dialog._lista.count() == total_inicial + 1


def test_dialog_exclui_categoria(
    conn: sqlite3.Connection, qtbot: QtBot, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "poupy.ui.categorias_dialog.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    service = GastoService(conn)
    total_inicial = len(service.categorias())

    dialog = CategoriasDialog(service)
    qtbot.addWidget(dialog)
    dialog._lista.setCurrentRow(0)
    dialog._excluir()

    assert len(service.categorias()) == total_inicial - 1
    assert dialog._lista.count() == total_inicial - 1
