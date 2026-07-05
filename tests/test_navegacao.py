"""Testes da navegacao entre meses (servico e UI)."""

from __future__ import annotations

import sqlite3
from datetime import date

from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from poupy.services.gastos import GastoService
from poupy.ui.gasto_dialog import GastoDialog
from poupy.ui.main_window import MainWindow


def test_meses_sem_lancamentos_retorna_mes_atual(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    assert service.meses_disponiveis() == [date.today().strftime("%Y-%m")]


def test_meses_intervalo_continuo_inclui_meses_vazios(conn: sqlite3.Connection) -> None:
    service = GastoService(conn)
    # Lancamento antigo cria intervalo do passado ate o mes atual, sem buracos.
    service.registrar_gasto(1000, date(2000, 11, 1), 1, None)

    meses = service.meses_disponiveis()
    assert meses[0] == "2000-11"
    assert meses[1] == "2000-12"
    assert meses[2] == "2001-01"
    assert meses[-1] == date.today().strftime("%Y-%m")
    # Estritamente crescente e sem repeticoes.
    assert meses == sorted(set(meses))


def test_navegacao_setas_e_limites(conn: sqlite3.Connection, qtbot: QtBot) -> None:
    service = GastoService(conn)
    hoje = date.today()
    mes_atual = hoje.strftime("%Y-%m")
    service.registrar_gasto(500, date(2000, 11, 1), 1, "Antigo")
    service.registrar_gasto(700, hoje, 2, "Hoje")

    janela = MainWindow(service)
    qtbot.addWidget(janela)

    # Abre no mes atual: seta proxima desabilitada, anterior habilitada.
    assert janela._ano_mes == mes_atual
    assert not janela._btn_proximo.isEnabled()
    assert janela._btn_anterior.isEnabled()

    # Voltar ao primeiro mes desabilita a seta anterior.
    janela._competencia.setCurrentIndex(0)
    assert janela._ano_mes == "2000-11"
    assert not janela._btn_anterior.isEnabled()
    assert janela._btn_proximo.isEnabled()

    # A seta proxima avanca um mes e atualiza o conteudo.
    janela._mes_proximo()
    assert janela._ano_mes == "2000-12"
    assert janela._tabela.rowCount() == 0  # mes vazio no meio do intervalo


def test_salvar_gasto_navega_para_mes_do_lancamento(
    conn: sqlite3.Connection, qtbot: QtBot, monkeypatch: MonkeyPatch
) -> None:
    service = GastoService(conn)
    service.registrar_gasto(500, date(2000, 11, 1), 1, "Antigo")
    janela = MainWindow(service)
    qtbot.addWidget(janela)

    # Usuario navega para um mes antigo.
    janela._competencia.setCurrentIndex(0)
    assert janela._ano_mes == "2000-11"

    # Salvar um gasto de hoje deve levar a tela para o mes do lancamento.
    hoje = date.today()

    def _fake_exec(self: GastoDialog) -> int:
        self.gasto_salvo = service.registrar_gasto(700, hoje, 1, "Hoje")
        return int(GastoDialog.DialogCode.Accepted)

    monkeypatch.setattr(GastoDialog, "exec", _fake_exec)
    janela._abrir_novo_gasto()

    assert janela._ano_mes == hoje.strftime("%Y-%m")
    assert janela._competencia.currentData() == hoje.strftime("%Y-%m")
