"""Ponto de entrada do Poupy."""

from __future__ import annotations

import sqlite3
import sys
from importlib.resources import files
from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from poupy.config import ler_config
from poupy.db.connection import abrir_conexao, base_existe, fechar_conexao
from poupy.services.gastos import GastoService
from poupy.ui.main_window import MainWindow
from poupy.ui.onboarding import OnboardingDialog


def _base_ativa() -> Path | None:
    """Pasta da base ativa utilizavel, ou None se precisa de onboarding.

    Precisa de onboarding quando nao ha config OU o poupy.db apontado sumiu
    (pasta apagada, HD externo desconectado, nuvem indisponivel). Nunca recria
    uma base silenciosamente: sempre re-pergunta via onboarding.
    """
    config = ler_config()
    if config is None or not base_existe(config.active_data_path):
        return None
    return config.active_data_path


def _resolver_base() -> Path | None:
    """Resolve a base ativa, disparando o onboarding quando necessario."""
    base = _base_ativa()
    if base is not None:
        return base
    dialogo = OnboardingDialog()
    if dialogo.exec() != QDialog.DialogCode.Accepted:
        return None
    return dialogo.base


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Poupy")
    app.setOrganizationName("Poupy")
    app.setStyleSheet(files("poupy.ui").joinpath("style.qss").read_text(encoding="utf-8"))

    base = _resolver_base()
    if base is None:
        sys.exit(0)

    try:
        conn = abrir_conexao(base)
    except sqlite3.DatabaseError:
        QMessageBox.critical(
            None,
            "Poupy",
            f"A pasta {base} contem um poupy.db invalido ou corrompido.\n\n"
            "O Poupy nao vai abrir para nao arriscar seus dados. Verifique o "
            "arquivo ou aponte o app para outra pasta.",
        )
        sys.exit(1)

    service = GastoService(conn)
    janela = MainWindow(service)
    janela.show()

    codigo = app.exec()
    fechar_conexao(conn)
    sys.exit(codigo)


if __name__ == "__main__":
    main()
