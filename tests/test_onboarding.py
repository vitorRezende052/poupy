"""Testes do onboarding e da resolucao da base no bootstrap."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox
from pytestqt.qtbot import QtBot

from poupy import __main__ as bootstrap
from poupy import config
from poupy.config import ler_config
from poupy.db.connection import abrir_conexao, fechar_conexao
from poupy.ui import onboarding
from poupy.ui.onboarding import OnboardingDialog


@pytest.fixture(autouse=True)
def config_temporario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    caminho = tmp_path / "cfg" / "config.json"
    caminho.parent.mkdir()
    monkeypatch.setattr(config, "caminho_config", lambda: caminho)
    return caminho


# --- _base_ativa: quando disparar o onboarding (retorna None) ---


def test_sem_config_dispara_onboarding() -> None:
    assert bootstrap._base_ativa() is None


def test_config_corrompido_dispara_onboarding(config_temporario: Path) -> None:
    config_temporario.write_text("{ corrompido", encoding="utf-8")
    assert bootstrap._base_ativa() is None


def test_config_valido_com_base_sumida_dispara_onboarding(tmp_path: Path) -> None:
    sumida = tmp_path / "sumida"
    config.gravar_config(sumida)  # aponta para pasta sem poupy.db
    assert bootstrap._base_ativa() is None
    # Nao recriou a base silenciosamente.
    assert not (sumida / "poupy.db").exists()


def test_config_valido_com_base_presente_nao_dispara(tmp_path: Path) -> None:
    base = tmp_path / "dados"
    fechar_conexao(abrir_conexao(base))
    config.gravar_config(base)
    assert bootstrap._base_ativa() == base.resolve()


# --- OnboardingDialog ---


def test_confirmar_grava_config_e_cria_base(qtbot: QtBot, tmp_path: Path) -> None:
    base = tmp_path / "dados"
    dialogo = OnboardingDialog()
    qtbot.addWidget(dialogo)
    dialogo._campo.setText(str(base))

    dialogo.accept()

    assert dialogo.result() == QDialog.DialogCode.Accepted
    assert dialogo.base == base
    assert (base / "poupy.db").is_file()
    lido = ler_config()
    assert lido is not None
    assert lido.active_data_path == base.resolve()


def test_pasta_sem_permissao_bloqueia(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    avisos: list[str] = []
    monkeypatch.setattr(onboarding, "validar_escrita", lambda _p: False)

    def _capturar(_parent: object, _titulo: str, texto: str) -> QMessageBox.StandardButton:
        avisos.append(texto)
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "warning", _capturar)

    dialogo = OnboardingDialog()
    qtbot.addWidget(dialogo)
    dialogo._campo.setText(str(tmp_path / "dados"))

    dialogo.accept()

    assert dialogo.base is None
    assert dialogo.result() != QDialog.DialogCode.Accepted
    assert avisos  # exibiu o aviso
    assert ler_config() is None  # nada gravado
