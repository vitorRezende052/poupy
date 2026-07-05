"""Switch deslizante de tema: sol (claro) <-> lua (escuro).

Desenhado com QPainter, monocromatico, sem emoji: identico em toda plataforma e
alinhado a paleta do app. A bolinha desliza entre um sol a esquerda e uma lua a
direita, indicando o tema ativo.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

_LARGURA = 52
_ALTURA = 28
_MARGEM = 4

# Cores proprias do controle (leem bem sobre a bolinha branca em ambos os temas).
_TRILHO_CLARO = QColor("#d1d5db")
_TRILHO_ESCURO = QColor("#3b82f6")
_BOLINHA = QColor("#ffffff")
_ICONE = QColor("#6b7280")


class ThemeToggle(QWidget):
    """Alterna entre tema claro e escuro. Emite `alternado(escuro)` no clique."""

    alternado = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._escuro = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Alternar tema claro/escuro")

    def sizeHint(self) -> QSize:
        return QSize(_LARGURA, _ALTURA)

    def is_escuro(self) -> bool:
        return self._escuro

    def set_escuro(self, escuro: bool) -> None:
        """Ajusta o estado sem emitir o sinal (usado na carga inicial)."""
        self._escuro = escuro
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._escuro = not self._escuro
            self.update()
            self.alternado.emit(self._escuro)

    def paintEvent(self, event: QPaintEvent) -> None:
        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.RenderHint.Antialiasing)

        raio_trilho = _ALTURA / 2
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(_TRILHO_ESCURO if self._escuro else _TRILHO_CLARO)
        pintor.drawRoundedRect(0, 0, _LARGURA, _ALTURA, raio_trilho, raio_trilho)

        raio_bolinha = raio_trilho - _MARGEM
        centro_y = _ALTURA / 2
        centro_x = _LARGURA - _MARGEM - raio_bolinha if self._escuro else _MARGEM + raio_bolinha
        centro = QPointF(centro_x, centro_y)
        pintor.setBrush(_BOLINHA)
        pintor.drawEllipse(centro, raio_bolinha, raio_bolinha)

        if self._escuro:
            self._desenhar_lua(pintor, centro, raio_bolinha * 0.55)
        else:
            self._desenhar_sol(pintor, centro, raio_bolinha * 0.55)

    def _desenhar_sol(self, pintor: QPainter, centro: QPointF, r: float) -> None:
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(_ICONE)
        pintor.drawEllipse(centro, r * 0.5, r * 0.5)
        caneta = QPen(_ICONE, 1.4)
        caneta.setCapStyle(Qt.PenCapStyle.RoundCap)
        pintor.setPen(caneta)
        for i in range(8):
            ang = i * math.pi / 4
            cos, sin = math.cos(ang), math.sin(ang)
            inicio = QPointF(centro.x() + cos * r * 0.75, centro.y() + sin * r * 0.75)
            fim = QPointF(centro.x() + cos * r * 1.05, centro.y() + sin * r * 1.05)
            pintor.drawLine(inicio, fim)

    def _desenhar_lua(self, pintor: QPainter, centro: QPointF, r: float) -> None:
        pintor.setPen(Qt.PenStyle.NoPen)
        pintor.setBrush(_ICONE)
        pintor.drawEllipse(centro, r, r)
        # Recorta a crescente sobrepondo um disco da cor da bolinha, deslocado.
        pintor.setBrush(_BOLINHA)
        deslocado = QPointF(centro.x() + r * 0.5, centro.y() - r * 0.35)
        pintor.drawEllipse(deslocado, r * 0.85, r * 0.85)
