"""Janela principal: navegador de mes, total do mes e lista de lancamentos."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from poupy import config
from poupy.models import Gasto
from poupy.services.gastos import GastoService
from poupy.ui import tema
from poupy.ui.categorias_dialog import CategoriasDialog
from poupy.ui.format import format_competencia, format_moeda
from poupy.ui.gasto_dialog import GastoDialog
from poupy.ui.graficos import GraficosWidget
from poupy.ui.theme_toggle import ThemeToggle

_COLUNAS = ("Data", "Categoria", "Descrição", "Valor")


class MainWindow(QMainWindow):
    def __init__(self, service: GastoService, paleta: tema.Paleta = tema.CLARO) -> None:
        super().__init__()
        self._service = service
        self._ano_mes = date.today().strftime("%Y-%m")
        self.setWindowTitle("Poupy")
        self.resize(880, 780)

        self._btn_anterior = QToolButton()
        self._btn_anterior.setText("‹")
        self._btn_anterior.clicked.connect(self._mes_anterior)
        self._btn_proximo = QToolButton()
        self._btn_proximo.setText("›")
        self._btn_proximo.clicked.connect(self._mes_proximo)
        self._competencia = QComboBox()
        self._competencia.setObjectName("competencia")
        self._competencia.currentIndexChanged.connect(self._mudar_mes)

        self._toggle_tema = ThemeToggle()
        self._toggle_tema.set_escuro(paleta.escuro)
        self._toggle_tema.alternado.connect(self._trocar_tema)

        navegador = QHBoxLayout()
        navegador.addWidget(self._btn_anterior)
        navegador.addWidget(self._competencia, 1)
        navegador.addWidget(self._btn_proximo)
        navegador.addSpacing(12)
        navegador.addWidget(self._toggle_tema)

        self._total = QLabel()
        self._total.setObjectName("total")

        botao_novo = QPushButton("Novo gasto")
        botao_novo.setObjectName("botaoNovo")
        botao_novo.setShortcut("Ctrl+N")
        botao_novo.clicked.connect(self._abrir_novo_gasto)

        botao_categorias = QPushButton("Categorias")
        botao_categorias.clicked.connect(self._abrir_categorias)

        acoes = QHBoxLayout()
        acoes.addWidget(botao_novo)
        acoes.addStretch(1)
        acoes.addWidget(botao_categorias)

        self._tabela = QTableWidget(0, len(_COLUNAS))
        self._tabela.setHorizontalHeaderLabels(_COLUNAS)
        self._tabela.verticalHeader().setVisible(False)
        self._tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabela.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabela.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tabela.cellDoubleClicked.connect(self._editar_linha)
        cabecalho = self._tabela.horizontalHeader()
        cabecalho.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self._graficos = GraficosWidget(self._service, paleta)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addLayout(navegador)
        layout.addWidget(self._total)
        layout.addLayout(acoes)
        layout.addWidget(self._tabela, 1)
        layout.addWidget(self._graficos)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self._atualizar()

    def _trocar_tema(self, escuro: bool) -> None:
        """Aplica o tema em todo o app, repinta os graficos e persiste a escolha."""
        paleta = tema.ESCURO if escuro else tema.CLARO
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.setStyleSheet(tema.qss(paleta))
        self._graficos.aplicar_tema(paleta)
        config.gravar_tema("escuro" if escuro else "claro")

    def _abrir_novo_gasto(self) -> None:
        dialog = GastoDialog(self._service, self)
        if dialog.exec() == int(GastoDialog.DialogCode.Accepted):
            self._ir_para_gasto_salvo(dialog)
            self._atualizar()

    def _abrir_categorias(self) -> None:
        CategoriasDialog(self._service, self).exec()
        self._atualizar()

    def _editar_linha(self, linha: int, _coluna: int) -> None:
        item = self._tabela.item(linha, 0)
        if item is None:
            return
        gasto: Gasto = item.data(Qt.ItemDataRole.UserRole)
        dialog = GastoDialog(self._service, self, gasto=gasto)
        if dialog.exec() == int(GastoDialog.DialogCode.Accepted):
            self._ir_para_gasto_salvo(dialog)
            self._atualizar()

    def _ir_para_gasto_salvo(self, dialog: GastoDialog) -> None:
        """Seleciona o mes do gasto recem-salvo, para o usuario ver o lancamento.

        Ao excluir (sem gasto_salvo), mantem o mes atual.
        """
        if dialog.gasto_salvo is not None:
            self._ano_mes = dialog.gasto_salvo.data.strftime("%Y-%m")

    def _mes_anterior(self) -> None:
        self._competencia.setCurrentIndex(self._competencia.currentIndex() - 1)

    def _mes_proximo(self) -> None:
        self._competencia.setCurrentIndex(self._competencia.currentIndex() + 1)

    def _mudar_mes(self, indice: int) -> None:
        if indice < 0:
            return
        self._ano_mes = str(self._competencia.itemData(indice))
        self._atualizar_conteudo()

    def _atualizar(self) -> None:
        """Recarrega os meses disponiveis e o conteudo do mes selecionado."""
        meses = self._service.meses_disponiveis()
        if self._ano_mes not in meses:
            self._ano_mes = meses[-1]
        self._competencia.blockSignals(True)
        self._competencia.clear()
        for ano_mes in meses:
            self._competencia.addItem(format_competencia(ano_mes), ano_mes)
        self._competencia.setCurrentIndex(meses.index(self._ano_mes))
        self._competencia.blockSignals(False)
        self._atualizar_conteudo()

    def _atualizar_conteudo(self) -> None:
        """Atualiza setas, total e lista para o mes selecionado."""
        self._btn_anterior.setEnabled(self._competencia.currentIndex() > 0)
        self._btn_proximo.setEnabled(
            self._competencia.currentIndex() < self._competencia.count() - 1
        )
        self._total.setText(format_moeda(self._service.total_do_mes(self._ano_mes)))

        gastos = self._service.gastos_do_mes(self._ano_mes)
        self._tabela.setRowCount(len(gastos))
        for linha, gasto in enumerate(gastos):
            valor = QTableWidgetItem(format_moeda(gasto.valor_centavos))
            valor.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            data = QTableWidgetItem(gasto.data.strftime("%d/%m/%Y"))
            data.setData(Qt.ItemDataRole.UserRole, gasto)
            celulas = (
                data,
                QTableWidgetItem(gasto.categoria_nome),
                QTableWidgetItem(gasto.descricao or ""),
                valor,
            )
            for coluna, item in enumerate(celulas):
                self._tabela.setItem(linha, coluna, item)

        self._graficos.atualizar(self._ano_mes)
