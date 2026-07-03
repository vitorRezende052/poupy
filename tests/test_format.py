"""Testes de formatacao e leitura de moeda."""

from __future__ import annotations

import pytest

from poupy.ui.format import format_moeda, parse_moeda


@pytest.mark.parametrize(
    ("centavos", "esperado"),
    [
        (0, "R$ 0,00"),
        (5, "R$ 0,05"),
        (990, "R$ 9,90"),
        (1234567, "R$ 12.345,67"),
        (-2500, "-R$ 25,00"),
    ],
)
def test_format_moeda(centavos: int, esperado: str) -> None:
    assert format_moeda(centavos) == esperado


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("12,34", 1234),
        ("1.234,56", 123456),
        ("12", 1200),
        ("R$ 9,90", 990),
        ("  0,05 ", 5),
    ],
)
def test_parse_moeda(texto: str, esperado: int) -> None:
    assert parse_moeda(texto) == esperado


def test_parse_format_ida_e_volta() -> None:
    for centavos in (1, 990, 1234567):
        assert parse_moeda(format_moeda(centavos)) == centavos


@pytest.mark.parametrize("texto", ["", "   ", "abc", "R$"])
def test_parse_moeda_invalido(texto: str) -> None:
    with pytest.raises(ValueError):
        parse_moeda(texto)
