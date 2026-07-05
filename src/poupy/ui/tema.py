"""Paletas de tema (claro/escuro) e geracao do QSS a partir delas.

Fonte unica das cores do app. Os graficos do pyqtgraph nao leem QSS, entao
precisam das cores em Python; e o QSS tambem sai daqui, montado por `qss()`.
Assim as cores vivem num so lugar e os dois temas ficam sempre em sincronia.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Paleta:
    """Todas as cores usadas pela UI e pelos graficos, para um tema."""

    escuro: bool
    # Fundo da janela e cor de texto padrao.
    fundo: str
    texto: str
    # Fundo dos paineis: tabela, cabecalho, campos, botoes e area dos graficos.
    superficie: str
    # Bordas de controles; a "suave" e das bordas da tabela/cabecalho.
    borda: str
    borda_suave: str
    borda_hover: str
    # Linhas da grade da tabela.
    grade: str
    # Texto secundario: cabecalho da tabela e eixos/rotulos dos graficos.
    texto_secundario: str
    # Numero de destaque (total) e texto dos controles (setas, dropdown, botoes).
    texto_forte: str
    texto_controle: str
    # Texto de controle desabilitado (setas no limite dos meses).
    desabilitado: str
    # Azul de destaque: barras, linha de evolucao e o botao "Novo gasto".
    primaria: str
    primaria_hover: str
    primaria_texto: str
    # Linha selecionada na tabela.
    selecao_fundo: str
    selecao_texto: str


CLARO = Paleta(
    escuro=False,
    fundo="#f5f6f8",
    texto="#1f2430",
    superficie="#ffffff",
    borda="#d1d5db",
    borda_suave="#e5e7eb",
    borda_hover="#9ca3af",
    grade="#eef0f3",
    texto_secundario="#6b7280",
    texto_forte="#111827",
    texto_controle="#374151",
    desabilitado="#cbd5e1",
    primaria="#2563eb",
    primaria_hover="#1d4ed8",
    primaria_texto="#ffffff",
    selecao_fundo="#dbeafe",
    selecao_texto="#111827",
)

ESCURO = Paleta(
    escuro=True,
    fundo="#15171c",
    texto="#e5e7eb",
    superficie="#1f232b",
    borda="#3a3f4b",
    borda_suave="#2c313a",
    borda_hover="#565d6b",
    grade="#2c313a",
    texto_secundario="#9aa3b2",
    texto_forte="#f3f4f6",
    texto_controle="#cbd2dc",
    desabilitado="#4b5563",
    primaria="#3b82f6",
    primaria_hover="#2563eb",
    primaria_texto="#ffffff",
    selecao_fundo="#1e3a5f",
    selecao_texto="#f3f4f6",
)


def qss(p: Paleta) -> str:
    """Monta a folha de estilo do app para a paleta dada."""
    return f"""
QWidget {{
    background-color: {p.fundo};
    color: {p.texto};
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
}}

QComboBox#competencia {{
    font-size: 16px;
    font-weight: 600;
    color: {p.texto_controle};
    padding: 8px 12px;
}}

QToolButton {{
    background-color: {p.superficie};
    border: 1px solid {p.borda};
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 18px;
    color: {p.texto_controle};
}}

QToolButton:hover {{
    border-color: {p.borda_hover};
}}

QToolButton:disabled {{
    color: {p.desabilitado};
}}

QLabel#total {{
    font-size: 40px;
    font-weight: 700;
    color: {p.texto_forte};
}}

QPushButton {{
    background-color: {p.superficie};
    border: 1px solid {p.borda};
    border-radius: 8px;
    padding: 8px 16px;
}}

QPushButton:hover {{
    border-color: {p.borda_hover};
}}

QPushButton#botaoNovo {{
    background-color: {p.primaria};
    color: {p.primaria_texto};
    border: none;
    font-weight: 600;
}}

QPushButton#botaoNovo:hover {{
    background-color: {p.primaria_hover};
}}

QTableWidget {{
    background-color: {p.superficie};
    border: 1px solid {p.borda_suave};
    border-radius: 8px;
    gridline-color: {p.grade};
}}

QHeaderView::section {{
    background-color: {p.superficie};
    color: {p.texto_secundario};
    border: none;
    border-bottom: 1px solid {p.borda_suave};
    padding: 8px;
    font-weight: 600;
}}

QTableWidget::item {{
    padding: 6px 8px;
}}

QTableWidget::item:selected {{
    background-color: {p.selecao_fundo};
    color: {p.selecao_texto};
}}

QLineEdit, QComboBox, QDateEdit {{
    background-color: {p.superficie};
    border: 1px solid {p.borda};
    border-radius: 6px;
    padding: 6px 8px;
}}
"""
