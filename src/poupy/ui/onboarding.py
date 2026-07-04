"""Dialogo de primeira execucao: escolher a pasta da base ativa.

Este e o UNICO ponto em que o usuario escolhe a pasta da base. Nao ha tela de
configuracoes: para trocar de base, fecha-se o app, move-se/apaga-se o poupy.db
(ou o config.json) e reabre-se, caindo aqui de novo.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from poupy.config import gravar_config
from poupy.db.connection import abrir_conexao, fechar_conexao, validar_escrita

_EXPLICACAO = (
    "Seus dados ficam guardados nesta maquina, num arquivo poupy.db dentro da "
    "pasta que voce escolher. Voce e o responsavel pelo backup: basta fechar o "
    "app e copiar a pasta da base.\n\n"
    "Voce pode usar uma pasta de nuvem (OneDrive, Google Drive, Dropbox), mas "
    "evite abrir a mesma base em dois computadores ao mesmo tempo."
)


def _pasta_padrao() -> Path:
    documentos = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DocumentsLocation
    )
    return Path(documentos) / "Poupy"


class OnboardingDialog(QDialog):
    """Coleta a pasta da base, cria/abre a base e grava o ponteiro.

    Apos exec() == Accepted, ``base`` traz a pasta escolhida. Cancelar deixa
    ``base`` como None e nao grava nada.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.base: Path | None = None
        self.setWindowTitle("Bem-vindo ao Poupy")
        self.setModal(True)

        explicacao = QLabel(_EXPLICACAO)
        explicacao.setWordWrap(True)

        self._campo = QLineEdit(str(_pasta_padrao()))
        botao_escolher = QPushButton("Escolher pasta...")
        botao_escolher.clicked.connect(self._escolher)
        linha = QHBoxLayout()
        linha.addWidget(self._campo, 1)
        linha.addWidget(botao_escolher)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.button(QDialogButtonBox.StandardButton.Ok).setText("Comecar")
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Onde guardar seus dados?"))
        layout.addWidget(explicacao)
        layout.addLayout(linha)
        layout.addWidget(botoes)

    def _escolher(self) -> None:
        pasta = QFileDialog.getExistingDirectory(
            self, "Escolher pasta da base", self._campo.text()
        )
        if pasta:
            self._campo.setText(pasta)

    def accept(self) -> None:
        texto = self._campo.text().strip()
        if not texto:
            QMessageBox.warning(self, "Poupy", "Escolha uma pasta para guardar os dados.")
            return
        pasta = Path(texto)

        if not validar_escrita(pasta):
            QMessageBox.warning(
                self, "Poupy", "Sem permissao de escrita nessa pasta. Escolha outra."
            )
            return

        try:
            conn = abrir_conexao(pasta)
        except sqlite3.DatabaseError:
            QMessageBox.warning(
                self,
                "Poupy",
                "Essa pasta contem um poupy.db invalido ou corrompido. Escolha outra.",
            )
            return
        fechar_conexao(conn)

        gravar_config(pasta)
        self.base = pasta
        super().accept()
