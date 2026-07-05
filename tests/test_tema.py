"""Testes do tema: toggle, troca no MainWindow e repintura dos graficos."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from pytestqt.qtbot import QtBot

from poupy import config
from poupy.services.gastos import GastoService
from poupy.ui import tema
from poupy.ui.graficos import GraficosWidget
from poupy.ui.main_window import MainWindow
from poupy.ui.theme_toggle import ThemeToggle


@pytest.fixture(autouse=True)
def config_temporario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Isola o config.json para as gravacoes de tema nao vazarem entre testes."""
    monkeypatch.setattr(config, "caminho_config", lambda: tmp_path / "config.json")


def _clicar(widget: ThemeToggle) -> None:
    """Despacha um clique esquerdo tipado (evita a API nao-tipada do qtbot)."""
    evento = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(5, 5),
        QPointF(5, 5),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    widget.mousePressEvent(evento)


def test_toggle_emite_sinal_ao_alternar(qtbot: QtBot) -> None:
    toggle = ThemeToggle()
    qtbot.addWidget(toggle)
    estados: list[bool] = []
    toggle.alternado.connect(estados.append)

    _clicar(toggle)
    _clicar(toggle)

    assert estados == [True, False]
    assert toggle.is_escuro() is False


def test_set_escuro_nao_emite(qtbot: QtBot) -> None:
    toggle = ThemeToggle()
    qtbot.addWidget(toggle)
    estados: list[bool] = []
    toggle.alternado.connect(estados.append)

    toggle.set_escuro(True)

    assert toggle.is_escuro() is True
    assert estados == []


def test_graficos_aplicar_tema_repinta(conn: sqlite3.Connection, qtbot: QtBot) -> None:
    service = GastoService(conn)
    service.registrar_gasto(1000, date.today(), 1, None)
    widget = GraficosWidget(service)
    qtbot.addWidget(widget)
    widget.atualizar(date.today().strftime("%Y-%m"))

    widget.aplicar_tema(tema.ESCURO)

    assert widget._paleta is tema.ESCURO
    # Continua com a barra de categoria apos repintar.
    import pyqtgraph as pg

    barras = [
        item for item in widget._categorias.getPlotItem().items if isinstance(item, pg.BarGraphItem)
    ]
    assert len(barras) == 1


def test_main_window_troca_tema_e_persiste(conn: sqlite3.Connection, qtbot: QtBot) -> None:
    service = GastoService(conn)
    janela = MainWindow(service)
    qtbot.addWidget(janela)

    janela._trocar_tema(True)

    assert janela._graficos._paleta is tema.ESCURO
    assert config.ler_tema() == "escuro"

    janela._trocar_tema(False)

    assert janela._graficos._paleta is tema.CLARO
    assert config.ler_tema() == "claro"
