"""Formatacao e leitura de moeda em pt-BR. Internamente sempre centavos."""

from __future__ import annotations

_SIMBOLO = "R$"

_MESES = (
    "Janeiro",
    "Fevereiro",
    "Marco",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
)


def format_competencia(ano_mes: str) -> str:
    """Formata 'YYYY-MM' como 'Julho de 2026'."""
    ano, mes = ano_mes.split("-")
    return f"{_MESES[int(mes) - 1]} de {ano}"


def format_moeda(centavos: int) -> str:
    """Formata centavos como 'R$ 12.345,67' (ponto de milhar, virgula decimal)."""
    sinal = "-" if centavos < 0 else ""
    reais, resto = divmod(abs(centavos), 100)
    inteiro = f"{reais:,}".replace(",", ".")
    return f"{sinal}{_SIMBOLO} {inteiro},{resto:02d}"


def format_centavos_editavel(centavos: int) -> str:
    """Formata centavos como '1234,56' (sem simbolo), para preencher inputs."""
    reais, resto = divmod(centavos, 100)
    return f"{reais},{resto:02d}"


def parse_moeda(texto: str) -> int:
    """Le uma entrada pt-BR ('1.234,56', '12,5', '12', 'R$ 9,90') em centavos.

    Levanta ValueError se a entrada for vazia ou nao numerica.
    """
    limpo = texto.strip().replace(_SIMBOLO, "").replace(" ", "").replace(".", "")
    limpo = limpo.replace(",", ".")
    if not limpo:
        raise ValueError("Informe um valor.")
    try:
        valor = round(float(limpo) * 100)
    except ValueError as erro:
        raise ValueError(f"Valor invalido: {texto!r}") from erro
    return valor
