"""Dialogo de primeira execucao: criar uma base nova ou abrir um .db existente.

Este e o UNICO ponto em que o usuario escolhe a base. Nao ha tela de
configuracoes: para trocar de base, fecha-se o app, apaga-se o config.json (ou
move-se o .db) e reabre-se, caindo aqui de novo.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from poupy.config import gravar_config
from poupy.db.connection import (
    BaseInvalida,
    abrir_conexao,
    base_existe,
    fechar_conexao,
    validar_escrita,
)

_EXPLICACAO = (
    "Seus dados ficam nesta máquina, num arquivo .db. Você é o responsável pelo "
    "backup: basta fechar o app e copiar o arquivo. Se guardar a base numa pasta "
    "em nuvem (Google Drive, OneDrive, Dropbox), não abra a mesma base em duas "
    "máquinas ao mesmo tempo, para não corromper os dados."
)

_NOME_BASE = "poupy.db"


def _pasta_padrao() -> Path:
    documentos = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    return Path(documentos) / "Poupy"


class OnboardingDialog(QDialog):
    """Cria uma base nova ou abre um .db existente e grava o ponteiro.

    Comeca numa pagina de escolha (criar OU abrir). Apos exec() == Accepted,
    ``base`` traz o caminho do arquivo .db escolhido. Cancelar deixa ``base``
    como None e nao grava nada.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.base: Path | None = None
        self.setWindowTitle("Bem-vindo ao Poupy")
        self.setModal(True)

        self._paginas = QStackedWidget()
        self._paginas.addWidget(self._pagina_escolha())
        self._paginas.addWidget(self._pagina_criar())

        layout = QVBoxLayout(self)
        layout.addWidget(self._paginas)

    def _pagina_escolha(self) -> QWidget:
        explicacao = QLabel(_EXPLICACAO)
        explicacao.setWordWrap(True)

        criar = QPushButton("Criar base nova")
        criar.clicked.connect(lambda: self._paginas.setCurrentIndex(1))
        abrir = QPushButton("Abrir base existente")
        abrir.clicked.connect(self._abrir)
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)

        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.addWidget(QLabel("Como você quer começar?"))
        layout.addWidget(explicacao)
        layout.addWidget(criar)
        layout.addWidget(abrir)
        layout.addWidget(cancelar)
        return pagina

    def _pagina_criar(self) -> QWidget:
        self._campo = QLineEdit(str(_pasta_padrao()))
        escolher = QPushButton("Escolher pasta...")
        escolher.clicked.connect(self._escolher_pasta)
        linha = QHBoxLayout()
        linha.addWidget(self._campo, 1)
        linha.addWidget(escolher)

        voltar = QPushButton("Voltar")
        voltar.clicked.connect(lambda: self._paginas.setCurrentIndex(0))
        criar = QPushButton("Criar")
        criar.setDefault(True)
        criar.clicked.connect(self._criar)
        botoes = QHBoxLayout()
        botoes.addWidget(voltar)
        botoes.addStretch(1)
        botoes.addWidget(criar)

        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.addWidget(QLabel("Onde criar sua base?"))
        layout.addLayout(linha)
        layout.addLayout(botoes)
        return pagina

    def _escolher_pasta(self) -> None:
        pasta = QFileDialog.getExistingDirectory(self, "Escolher pasta da base", self._campo.text())
        if pasta:
            self._campo.setText(pasta)

    def _criar(self) -> None:
        texto = self._campo.text().strip()
        if not texto:
            QMessageBox.warning(self, "Poupy", "Escolha uma pasta para guardar os dados.")
            return
        db_path = Path(texto) / _NOME_BASE
        if base_existe(db_path):
            # "Criar" nao pode abrir silenciosamente uma base ja existente: quem
            # pediu base nova acharia que apareceram dados "do nada".
            resposta = QMessageBox.question(
                self, "Poupy", "Já existe uma base nesta pasta. Deseja abri-la?"
            )
            if resposta == QMessageBox.StandardButton.Yes:
                self._confirmar(db_path)
            return
        if not validar_escrita(db_path):
            QMessageBox.warning(
                self, "Poupy", "Sem permissão de escrita nessa pasta. Escolha outra."
            )
            return
        self._confirmar(db_path)

    def _abrir(self) -> None:
        arquivo, _ = QFileDialog.getOpenFileName(
            self, "Abrir base do Poupy", str(_pasta_padrao()), "Bancos do Poupy (*.db)"
        )
        if arquivo:
            self._confirmar(Path(arquivo))

    def _confirmar(self, db_path: Path) -> None:
        """Abre/valida a base, grava o ponteiro e aceita o dialogo."""
        try:
            conn = abrir_conexao(db_path)
        except BaseInvalida as erro:
            QMessageBox.warning(self, "Poupy", str(erro))
            return
        fechar_conexao(conn)

        gravar_config(db_path)
        self.base = db_path
        self.accept()
