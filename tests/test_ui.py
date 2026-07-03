"""Testes de UI com pytest-qt."""

from __future__ import annotations

import sqlite3
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from poupy.services.gastos import GastoService
from poupy.ui.format import format_moeda
from poupy.ui.gasto_dialog import GastoDialog
from poupy.ui.main_window import MainWindow


def test_dialog_salva_gasto(conn: sqlite3.Connection, qtbot: QtBot) -> None:
    service = GastoService(conn)
    dialog = GastoDialog(service)
    qtbot.addWidget(dialog)

    dialog._valor.setText("12,34")
    dialog._descricao.setText("Cafe")
    dialog.accept()

    assert dialog.result() == int(GastoDialog.DialogCode.Accepted)
    assert dialog.gasto_salvo is not None
    assert dialog.gasto_salvo.valor_centavos == 1234
    assert service.gastos_do_mes(date.today().strftime("%Y-%m"))[0].descricao == "Cafe"


def test_dialog_valor_invalido_nao_fecha(
    conn: sqlite3.Connection, qtbot: QtBot, monkeypatch: MonkeyPatch
) -> None:
    avisos: list[str] = []
    monkeypatch.setattr(
        "poupy.ui.gasto_dialog.QMessageBox.warning",
        lambda *args, **kwargs: avisos.append(args[-1]),
    )
    service = GastoService(conn)
    dialog = GastoDialog(service)
    qtbot.addWidget(dialog)

    dialog._valor.setText("abc")
    dialog.accept()

    assert dialog.gasto_salvo is None
    assert dialog.result() != int(GastoDialog.DialogCode.Accepted)
    assert avisos


def test_dialog_edita_gasto(conn: sqlite3.Connection, qtbot: QtBot) -> None:
    service = GastoService(conn)
    hoje = date.today()
    gasto = service.registrar_gasto(1500, hoje, 1, "Almoco")

    dialog = GastoDialog(service, gasto=gasto)
    qtbot.addWidget(dialog)

    # Campos vem pre-preenchidos com o gasto existente.
    assert dialog._valor.text() == "15,00"
    assert dialog._descricao.text() == "Almoco"

    dialog._valor.setText("20,00")
    dialog.accept()

    assert dialog.gasto_salvo is not None
    assert dialog.gasto_salvo.valor_centavos == 2000
    gastos = service.gastos_do_mes(hoje.strftime("%Y-%m"))
    assert len(gastos) == 1
    assert gastos[0].valor_centavos == 2000


def test_dialog_exclui_gasto(
    conn: sqlite3.Connection, qtbot: QtBot, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "poupy.ui.gasto_dialog.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    service = GastoService(conn)
    hoje = date.today()
    gasto = service.registrar_gasto(1500, hoje, 1, "Almoco")

    dialog = GastoDialog(service, gasto=gasto)
    qtbot.addWidget(dialog)
    dialog._excluir()

    assert dialog.excluido is True
    assert service.gastos_do_mes(hoje.strftime("%Y-%m")) == []


def test_main_window_reflete_total(conn: sqlite3.Connection, qtbot: QtBot) -> None:
    service = GastoService(conn)
    hoje = date.today()
    service.registrar_gasto(1500, hoje, 1, "Almoco")
    service.registrar_gasto(2500, hoje, 2, None)

    janela = MainWindow(service)
    qtbot.addWidget(janela)
    janela._atualizar()

    assert janela._total.text() == format_moeda(4000)
    assert janela._tabela.rowCount() == 2
    # A linha carrega o Gasto para edicao por duplo-clique.
    item = janela._tabela.item(0, 0)
    assert item is not None
    assert item.data(Qt.ItemDataRole.UserRole).id > 0
