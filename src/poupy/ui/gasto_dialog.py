"""Dialogo modal para registrar ou editar um gasto."""

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
from poupy.ui.format import format_centavos_editavel, parse_moeda


class GastoDialog(QDialog):
    """Coleta Valor, Categoria, Descricao e Data e salva via servico.

    Sem ``gasto``, registra um novo. Com ``gasto``, edita o existente e
    oferece exclusao. Apos exec() == Accepted, ``gasto_salvo`` traz o gasto
    (None quando foi excluido) e ``excluido`` indica exclusao.
    """

    def __init__(
        self,
        service: GastoService,
        parent: QWidget | None = None,
        gasto: Gasto | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._gasto = gasto
        self.gasto_salvo: Gasto | None = None
        self.excluido = False
        self._titulo = "Editar gasto" if gasto else "Novo gasto"
        self.setWindowTitle(self._titulo)
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
        if gasto is not None:
            botao_excluir = botoes.addButton(
                "Excluir", QDialogButtonBox.ButtonRole.DestructiveRole
            )
            botao_excluir.clicked.connect(self._excluir)
        formulario.addRow(botoes)

        if gasto is not None:
            self._preencher(gasto)
        self._valor.setFocus()

    def _preencher(self, gasto: Gasto) -> None:
        self._valor.setText(format_centavos_editavel(gasto.valor_centavos))
        indice = self._categoria.findData(gasto.categoria_id)
        if indice >= 0:
            self._categoria.setCurrentIndex(indice)
        self._descricao.setText(gasto.descricao or "")
        self._data.setDate(QDate(gasto.data.year, gasto.data.month, gasto.data.day))

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

    def _excluir(self) -> None:
        resposta = QMessageBox.question(
            self, "Excluir gasto", "Deseja excluir este lancamento?"
        )
        if resposta != QMessageBox.StandardButton.Yes or self._gasto is None:
            return
        self._service.excluir_gasto(self._gasto.id)
        self.excluido = True
        super().accept()

    def accept(self) -> None:
        try:
            valor_centavos = parse_moeda(self._valor.text())
        except ValueError as erro:
            QMessageBox.warning(self, self._titulo, str(erro))
            return

        categoria_id = self._categoria.currentData()
        if categoria_id is None:
            QMessageBox.warning(self, self._titulo, "Selecione uma categoria.")
            return

        qdata = self._data.date()
        data = date(qdata.year(), qdata.month(), qdata.day())
        try:
            if self._gasto is None:
                self.gasto_salvo = self._service.registrar_gasto(
                    valor_centavos, data, int(categoria_id), self._descricao.text()
                )
            else:
                self.gasto_salvo = self._service.atualizar_gasto(
                    self._gasto.id, valor_centavos, data, int(categoria_id),
                    self._descricao.text(),
                )
        except ValueError as erro:
            QMessageBox.warning(self, self._titulo, str(erro))
            return
        super().accept()
