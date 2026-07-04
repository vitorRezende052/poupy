"""Dialogo de gestao de categorias: renomear e excluir."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from poupy.services.gastos import GastoService


class CategoriasDialog(QDialog):
    def __init__(self, service: GastoService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self.setWindowTitle("Categorias")
        self.setModal(True)
        self.resize(320, 400)

        self._lista = QListWidget()
        self._lista.itemDoubleClicked.connect(lambda _item: self._renomear())

        botao_criar = QPushButton("Nova categoria")
        botao_criar.clicked.connect(self._criar)

        botao_renomear = QPushButton("Renomear")
        botao_renomear.clicked.connect(self._renomear)
        botao_excluir = QPushButton("Excluir")
        botao_excluir.clicked.connect(self._excluir)
        acoes = QHBoxLayout()
        acoes.addWidget(botao_renomear)
        acoes.addWidget(botao_excluir)

        fechar = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        fechar.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(botao_criar)
        layout.addWidget(self._lista, 1)
        layout.addLayout(acoes)
        layout.addWidget(fechar)

        self._recarregar()

    def _recarregar(self) -> None:
        self._lista.clear()
        for categoria in self._service.categorias():
            item = QListWidgetItem(categoria.nome)
            item.setData(Qt.ItemDataRole.UserRole, categoria.id)
            self._lista.addItem(item)

    def _selecionada(self) -> QListWidgetItem | None:
        item = self._lista.currentItem()
        if item is None:
            QMessageBox.information(self, "Categorias", "Selecione uma categoria.")
        return item

    def _criar(self) -> None:
        nome, ok = QInputDialog.getText(self, "Nova categoria", "Nome da categoria:")
        if not ok:
            return
        try:
            self._service.criar_categoria(nome)
        except ValueError as erro:
            QMessageBox.warning(self, "Nova categoria", str(erro))
            return
        self._recarregar()

    def _renomear(self) -> None:
        item = self._selecionada()
        if item is None:
            return
        nome, ok = QInputDialog.getText(
            self, "Renomear categoria", "Novo nome:", text=item.text()
        )
        if not ok:
            return
        try:
            self._service.renomear_categoria(item.data(Qt.ItemDataRole.UserRole), nome)
        except ValueError as erro:
            QMessageBox.warning(self, "Renomear categoria", str(erro))
            return
        self._recarregar()

    def _excluir(self) -> None:
        item = self._selecionada()
        if item is None:
            return
        resposta = QMessageBox.question(
            self, "Excluir categoria", f"Excluir a categoria '{item.text()}'?"
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return
        try:
            self._service.excluir_categoria(item.data(Qt.ItemDataRole.UserRole))
        except ValueError as erro:
            QMessageBox.warning(self, "Excluir categoria", str(erro))
            return
        self._recarregar()
