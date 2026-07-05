"""Ponto de entrada do Poupy."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from poupy.config import ler_config, ler_tema
from poupy.db.connection import BaseInvalida, abrir_conexao, base_existe, fechar_conexao
from poupy.services.gastos import GastoService
from poupy.ui import tema
from poupy.ui.main_window import MainWindow
from poupy.ui.onboarding import OnboardingDialog


def _base_ativa() -> Path | None:
    """Arquivo .db da base ativa utilizavel, ou None se precisa de onboarding.

    Precisa de onboarding quando nao ha config OU o arquivo .db apontado sumiu
    (apagado, HD externo desconectado, nuvem indisponivel). Nunca recria uma
    base silenciosamente: sempre re-pergunta via onboarding.
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
    paleta = tema.ESCURO if ler_tema() == "escuro" else tema.CLARO
    app.setStyleSheet(tema.qss(paleta))

    base = _resolver_base()
    if base is None:
        sys.exit(0)

    try:
        conn = abrir_conexao(base)
    except BaseInvalida as erro:
        QMessageBox.critical(
            None,
            "Poupy",
            f"A base em {base} não pôde ser aberta:\n\n{erro}\n\n"
            "O Poupy não vai abrir para não arriscar seus dados. Verifique o "
            "arquivo ou aponte o app para outra base.",
        )
        sys.exit(1)

    service = GastoService(conn)
    janela = MainWindow(service, paleta)
    janela.show()

    codigo = app.exec()
    fechar_conexao(conn)
    sys.exit(codigo)


if __name__ == "__main__":
    main()
