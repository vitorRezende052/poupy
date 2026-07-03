"""Ponto de entrada do Poupy."""

from __future__ import annotations

import sys
from importlib.resources import files

from PySide6.QtWidgets import QApplication

from poupy.db.connection import abrir_conexao, caminho_banco
from poupy.services.gastos import GastoService
from poupy.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Poupy")
    app.setOrganizationName("Poupy")
    app.setStyleSheet(files("poupy.ui").joinpath("style.qss").read_text(encoding="utf-8"))

    conn = abrir_conexao(caminho_banco())
    service = GastoService(conn)

    janela = MainWindow(service)
    janela.show()

    codigo = app.exec()
    conn.close()
    sys.exit(codigo)


if __name__ == "__main__":
    main()
