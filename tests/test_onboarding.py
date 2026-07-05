"""Testes do onboarding e da resolucao da base no bootstrap."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox
from pytestqt.qtbot import QtBot

from poupy import __main__ as bootstrap
from poupy import config
from poupy.config import ler_config
from poupy.db.connection import POUPY_APPLICATION_ID, abrir_conexao, fechar_conexao
from poupy.ui import onboarding
from poupy.ui.onboarding import OnboardingDialog


@pytest.fixture(autouse=True)
def config_temporario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    caminho = tmp_path / "cfg" / "config.json"
    caminho.parent.mkdir()
    monkeypatch.setattr(config, "caminho_config", lambda: caminho)
    return caminho


def _criar_db_poupy(db_path: Path) -> Path:
    fechar_conexao(abrir_conexao(db_path))
    return db_path


# --- _base_ativa: quando disparar o onboarding (retorna None) ---


def test_sem_config_dispara_onboarding() -> None:
    assert bootstrap._base_ativa() is None


def test_config_corrompido_dispara_onboarding(config_temporario: Path) -> None:
    config_temporario.write_text("{ corrompido", encoding="utf-8")
    assert bootstrap._base_ativa() is None


def test_config_valido_com_base_sumida_dispara_onboarding(tmp_path: Path) -> None:
    sumida = tmp_path / "sumida.db"
    config.gravar_config(sumida)  # aponta para um .db inexistente
    assert bootstrap._base_ativa() is None
    # Nao recriou a base silenciosamente.
    assert not sumida.exists()


def test_config_valido_com_base_presente_nao_dispara(tmp_path: Path) -> None:
    base = _criar_db_poupy(tmp_path / "dados.db")
    config.gravar_config(base)
    assert bootstrap._base_ativa() == base.resolve()


# --- OnboardingDialog: criar ---


def test_criar_grava_config_e_cria_base(qtbot: QtBot, tmp_path: Path) -> None:
    pasta = tmp_path / "dados"
    dialogo = OnboardingDialog()
    qtbot.addWidget(dialogo)
    dialogo._campo.setText(str(pasta))

    dialogo._criar()

    esperado = pasta / "poupy.db"
    assert dialogo.result() == QDialog.DialogCode.Accepted
    assert dialogo.base == esperado
    assert esperado.is_file()
    lido = ler_config()
    assert lido is not None
    assert lido.active_data_path == esperado.resolve()
    # A base criada carrega a identidade do Poupy.
    con = sqlite3.connect(esperado)
    assert con.execute("PRAGMA application_id").fetchone()[0] == POUPY_APPLICATION_ID
    con.close()


def test_criar_em_pasta_sem_permissao_bloqueia(
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

    dialogo._criar()

    assert dialogo.base is None
    assert dialogo.result() != QDialog.DialogCode.Accepted
    assert avisos  # exibiu o aviso
    assert ler_config() is None  # nada gravado


def test_criar_sem_pasta_bloqueia(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    avisos = _capturar_avisos(monkeypatch)
    dialogo = OnboardingDialog()
    qtbot.addWidget(dialogo)
    dialogo._campo.setText("   ")

    dialogo._criar()

    assert dialogo.base is None
    assert avisos
    assert ler_config() is None


def test_cancelar_nao_grava_config(qtbot: QtBot) -> None:
    dialogo = OnboardingDialog()
    qtbot.addWidget(dialogo)

    dialogo.reject()

    assert dialogo.base is None
    assert dialogo.result() != QDialog.DialogCode.Accepted
    assert ler_config() is None


# --- OnboardingDialog: abrir base existente ---


def _selecionar_arquivo(monkeypatch: pytest.MonkeyPatch, arquivo: Path) -> None:
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        staticmethod(lambda *a, **k: (str(arquivo), "")),
    )


def _capturar_avisos(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    avisos: list[str] = []

    def _capturar(_parent: object, _titulo: str, texto: str) -> QMessageBox.StandardButton:
        avisos.append(texto)
        return QMessageBox.StandardButton.Ok

    monkeypatch.setattr(QMessageBox, "warning", _capturar)
    return avisos


def test_abrir_base_poupy_valida(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    existente = _criar_db_poupy(tmp_path / "backup.db")
    _selecionar_arquivo(monkeypatch, existente)

    dialogo = OnboardingDialog()
    qtbot.addWidget(dialogo)
    dialogo._abrir()

    assert dialogo.result() == QDialog.DialogCode.Accepted
    assert dialogo.base == existente
    lido = ler_config()
    assert lido is not None
    assert lido.active_data_path == existente.resolve()


def test_abrir_db_de_outro_programa_bloqueia(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    outro = tmp_path / "outro.db"
    con = sqlite3.connect(outro)
    con.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY)")
    con.commit()
    con.close()
    _selecionar_arquivo(monkeypatch, outro)
    avisos = _capturar_avisos(monkeypatch)

    dialogo = OnboardingDialog()
    qtbot.addWidget(dialogo)
    dialogo._abrir()

    assert dialogo.base is None
    assert dialogo.result() != QDialog.DialogCode.Accepted
    assert any("Poupy" in aviso for aviso in avisos)  # "nao e um banco do Poupy"
    assert ler_config() is None
    # Arquivo alheio permanece intacto.
    con = sqlite3.connect(outro)
    tabelas = {
        linha[0]
        for linha in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    con.close()
    assert tabelas == {"clientes"}


def test_abrir_db_versao_futura_bloqueia(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from poupy.db import migrations

    futura = _criar_db_poupy(tmp_path / "futura.db")
    con = sqlite3.connect(futura)
    con.execute(f"PRAGMA user_version = {len(migrations.MIGRATIONS) + 1}")
    con.close()
    _selecionar_arquivo(monkeypatch, futura)
    avisos = _capturar_avisos(monkeypatch)

    dialogo = OnboardingDialog()
    qtbot.addWidget(dialogo)
    dialogo._abrir()

    assert dialogo.base is None
    assert dialogo.result() != QDialog.DialogCode.Accepted
    assert any("mais nova" in aviso for aviso in avisos)


# --- _resolver_base: glue do boot entre a base ativa e o onboarding ---


def test_resolver_base_usa_base_ativa_sem_onboarding(tmp_path: Path) -> None:
    base = _criar_db_poupy(tmp_path / "dados.db")
    config.gravar_config(base)
    assert bootstrap._resolver_base() == base.resolve()


def test_resolver_base_cancelado_retorna_none(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Sem base ativa -> abre o onboarding; cancelar -> None (o app encerra).
    monkeypatch.setattr(
        OnboardingDialog, "exec", lambda self: QDialog.DialogCode.Rejected
    )
    assert bootstrap._resolver_base() is None
    assert ler_config() is None


def test_resolver_base_aceito_retorna_base_escolhida(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    escolhida = tmp_path / "escolhida.db"

    def _fake_exec(self: OnboardingDialog) -> QDialog.DialogCode:
        self.base = escolhida
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(OnboardingDialog, "exec", _fake_exec)
    assert bootstrap._resolver_base() == escolhida
    assert ler_config() is None
