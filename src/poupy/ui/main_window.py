"""Janela principal: cabecalho com total do mes e lista de lancamentos."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from poupy.services.gastos import GastoService
from poupy.ui.format import format_competencia, format_moeda
from poupy.ui.novo_gasto_dialog import NovoGastoDialog

_COLUNAS = ("Data", "Categoria", "Descricao", "Valor")


class MainWindow(QMainWindow):
    def __init__(self, service: GastoService) -> None:
        super().__init__()
        self._service = service
        self._ano_mes = date.today().strftime("%Y-%m")
        self.setWindowTitle("Poupy")
        self.resize(720, 560)

        self._competencia = QLabel()
        self._competencia.setObjectName("competencia")

        self._total = QLabel()
        self._total.setObjectName("total")

        botao_novo = QPushButton("Novo gasto")
        botao_novo.setObjectName("botaoNovo")
        botao_novo.setShortcut("Ctrl+N")
        botao_novo.clicked.connect(self._abrir_novo_gasto)

        self._tabela = QTableWidget(0, len(_COLUNAS))
        self._tabela.setHorizontalHeaderLabels(_COLUNAS)
        self._tabela.verticalHeader().setVisible(False)
        self._tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        cabecalho = self._tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(self._competencia)
        layout.addWidget(self._total)
        layout.addWidget(botao_novo)
        layout.addWidget(self._tabela, 1)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self._atualizar()

    def _abrir_novo_gasto(self) -> None:
        dialog = NovoGastoDialog(self._service, self)
        if dialog.exec() == int(NovoGastoDialog.DialogCode.Accepted):
            self._atualizar()

    def _atualizar(self) -> None:
        self._competencia.setText(format_competencia(self._ano_mes))
        self._total.setText(format_moeda(self._service.total_do_mes(self._ano_mes)))

        gastos = self._service.gastos_do_mes(self._ano_mes)
        self._tabela.setRowCount(len(gastos))
        for linha, gasto in enumerate(gastos):
            valor = QTableWidgetItem(format_moeda(gasto.valor_centavos))
            valor.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            celulas = (
                QTableWidgetItem(gasto.data.strftime("%d/%m/%Y")),
                QTableWidgetItem(gasto.categoria_nome),
                QTableWidgetItem(gasto.descricao or ""),
                valor,
            )
            for coluna, item in enumerate(celulas):
                self._tabela.setItem(linha, coluna, item)
