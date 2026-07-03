"""Widget com os graficos: gastos por categoria e evolucao mensal."""

from __future__ import annotations

import pyqtgraph as pg
from PySide6.QtWidgets import QHBoxLayout, QWidget

from poupy.services.gastos import GastoService
from poupy.ui.format import format_mes_curto

_COR = "#2563eb"
_FUNDO = "#ffffff"
_EIXO = "#6b7280"


class GraficosWidget(QWidget):
    """Dois graficos estaticos que reagem ao mes selecionado."""

    def __init__(self, service: GastoService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._service = service
        pg.setConfigOptions(antialias=True)
        # Altura fixa para os graficos nao competirem por espaco com a lista.
        self.setFixedHeight(260)

        self._categorias = self._novo_plot("Gastos por categoria")
        self._evolucao = self._novo_plot("Evolucao mensal")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self._categorias)
        layout.addWidget(self._evolucao)

    def _novo_plot(self, titulo: str) -> pg.PlotWidget:
        plot = pg.PlotWidget(background=_FUNDO, title=titulo)
        plot.setMouseEnabled(x=False, y=False)
        plot.setMenuEnabled(False)
        plot.hideButtons()
        for nome in ("left", "bottom"):
            eixo = plot.getAxis(nome)
            eixo.setPen(_EIXO)
            eixo.setTextPen(_EIXO)
        return plot

    def atualizar(self, ano_mes: str) -> None:
        self._atualizar_categorias(ano_mes)
        self._atualizar_evolucao(ano_mes)

    def _atualizar_categorias(self, ano_mes: str) -> None:
        plot = self._categorias
        plot.clear()
        eixo_y = plot.getAxis("left")
        # Do maior para o menor; invertido para o maior ficar no topo.
        dados = list(reversed(self._service.gastos_por_categoria(ano_mes)))
        if not dados:
            eixo_y.setTicks([[]])
            return
        posicoes = list(range(len(dados)))
        valores = [centavos / 100 for _, centavos in dados]
        plot.addItem(
            pg.BarGraphItem(x0=0, y=posicoes, height=0.6, width=valores, brush=_COR, pen=None)
        )
        eixo_y.setTicks([[(i, nome) for i, (nome, _) in enumerate(dados)]])
        plot.getViewBox().setYRange(-0.6, len(dados) - 0.4)

    def _atualizar_evolucao(self, ano_mes: str) -> None:
        plot = self._evolucao
        plot.clear()
        dados = self._service.evolucao_mensal()
        posicoes = list(range(len(dados)))
        valores = [centavos / 100 for _, centavos in dados]
        plot.plot(
            posicoes,
            valores,
            pen=pg.mkPen(_COR, width=2),
            symbol="o",
            symbolSize=6,
            symbolBrush=_COR,
            symbolPen=None,
        )
        meses = [mes for mes, _ in dados]
        if ano_mes in meses:
            indice = meses.index(ano_mes)
            plot.plot(
                [indice],
                [valores[indice]],
                pen=None,
                symbol="o",
                symbolSize=13,
                symbolBrush=None,
                symbolPen=pg.mkPen(_COR, width=2),
            )
        plot.getAxis("bottom").setTicks(
            [[(i, format_mes_curto(mes)) for i, mes in enumerate(meses)]]
        )
        # Folga lateral para os rotulos das pontas nao serem cortados.
        plot.getViewBox().setXRange(-0.4, len(dados) - 0.6, padding=0)
