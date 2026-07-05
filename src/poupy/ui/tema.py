"""Paleta de cores do tema, fonte unica das cores usadas em codigo.

Os graficos do pyqtgraph nao leem o QSS, entao precisam das cores em Python.
Este modulo centraliza esses valores para nao ficarem como literais soltos e
duplicados. O style.qss usa os mesmos tons; ao mudar o tema, manter os dois
em sincronia.
"""

from __future__ import annotations

# Azul de destaque: barras, linha de evolucao e o botao "Novo gasto".
PRIMARIA = "#2563eb"
# Fundo dos paineis (tabela e area dos graficos).
SUPERFICIE = "#ffffff"
# Cinza dos eixos e rotulos secundarios.
EIXO = "#6b7280"
