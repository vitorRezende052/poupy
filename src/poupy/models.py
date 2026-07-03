"""Dataclasses tipadas do dominio. Dinheiro sempre em centavos inteiros."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class Categoria:
    id: int
    nome: str


@dataclass(frozen=True, slots=True)
class Gasto:
    id: int
    valor_centavos: int
    data: date
    categoria_id: int
    categoria_nome: str
    descricao: str | None
