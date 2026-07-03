"""Testes de UI com pytest-qt."""

from __future__ import annotations

import sqlite3
from datetime import date

from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from poupy.services.gastos import GastoService
from poupy.ui.format import format_moeda
from poupy.ui.main_window import MainWindow
from poupy.ui.novo_gasto_dialog import NovoGastoDialog


def test_dialog_salva_gasto(conn: sqlite3.Connection, qtbot: QtBot) -> None:
    service = GastoService(conn)
    dialog = NovoGastoDialog(service)
    qtbot.addWidget(dialog)

    dialog._valor.setText("12,34")
    dialog._descricao.setText("Cafe")
    dialog.accept()

    assert dialog.result() == int(NovoGastoDialog.DialogCode.Accepted)
    assert dialog.gasto_criado is not None
    assert dialog.gasto_criado.valor_centavos == 1234
    assert service.gastos_do_mes(date.today().strftime("%Y-%m"))[0].descricao == "Cafe"


def test_dialog_valor_invalido_nao_fecha(
    conn: sqlite3.Connection, qtbot: QtBot, monkeypatch: MonkeyPatch
) -> None:
    avisos: list[str] = []
    monkeypatch.setattr(
        "poupy.ui.novo_gasto_dialog.QMessageBox.warning",
        lambda *args, **kwargs: avisos.append(args[-1]),
    )
    service = GastoService(conn)
    dialog = NovoGastoDialog(service)
    qtbot.addWidget(dialog)

    dialog._valor.setText("abc")
    dialog.accept()

    assert dialog.gasto_criado is None
    assert dialog.result() != int(NovoGastoDialog.DialogCode.Accepted)
    assert avisos


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
