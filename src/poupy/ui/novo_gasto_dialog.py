"""Dialogo modal para registrar um novo gasto."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from poupy.models import Gasto
from poupy.services.gastos import GastoService
from poupy.ui.format import parse_moeda


class NovoGastoDialog(QDialog):
    """Coleta Valor, Categoria, Descricao e Data e salva via servico.

    Apos exec() == Accepted, o gasto criado fica em ``gasto_criado``.
    """

    def __init__(self, service: GastoService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = service
        self.gasto_criado: Gasto | None = None
        self.setWindowTitle("Novo gasto")
        self.setModal(True)

        self._valor = QLineEdit()
        self._valor.setPlaceholderText("0,00")

        self._categoria = QComboBox()
        self._recarregar_categorias()
        botao_nova = QPushButton("Nova categoria")
        botao_nova.clicked.connect(self._nova_categoria)
        linha_categoria = QHBoxLayout()
        linha_categoria.addWidget(self._categoria, 1)
        linha_categoria.addWidget(botao_nova)

        self._descricao = QLineEdit()

        self._data = QDateEdit()
        self._data.setCalendarPopup(True)
        self._data.setDisplayFormat("dd/MM/yyyy")
        self._data.setDate(QDate.currentDate())

        formulario = QFormLayout(self)
        formulario.addRow("Valor", self._valor)
        formulario.addRow("Categoria", linha_categoria)
        formulario.addRow("Descricao", self._descricao)
        formulario.addRow("Data", self._data)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        formulario.addRow(botoes)

        self._valor.setFocus()

    def _recarregar_categorias(self, selecionar_id: int | None = None) -> None:
        self._categoria.clear()
        for categoria in self._service.categorias():
            self._categoria.addItem(categoria.nome, categoria.id)
        if selecionar_id is not None:
            indice = self._categoria.findData(selecionar_id)
            if indice >= 0:
                self._categoria.setCurrentIndex(indice)

    def _nova_categoria(self) -> None:
        nome, ok = QInputDialog.getText(self, "Nova categoria", "Nome da categoria:")
        if not ok:
            return
        try:
            categoria = self._service.criar_categoria(nome)
        except ValueError as erro:
            QMessageBox.warning(self, "Nova categoria", str(erro))
            return
        self._recarregar_categorias(selecionar_id=categoria.id)

    def accept(self) -> None:
        try:
            valor_centavos = parse_moeda(self._valor.text())
        except ValueError as erro:
            QMessageBox.warning(self, "Novo gasto", str(erro))
            return

        categoria_id = self._categoria.currentData()
        if categoria_id is None:
            QMessageBox.warning(self, "Novo gasto", "Selecione uma categoria.")
            return

        qdata = self._data.date()
        data = date(qdata.year(), qdata.month(), qdata.day())
        try:
            self.gasto_criado = self._service.registrar_gasto(
                valor_centavos, data, int(categoria_id), self._descricao.text()
            )
        except ValueError as erro:
            QMessageBox.warning(self, "Novo gasto", str(erro))
            return
        super().accept()
