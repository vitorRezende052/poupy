"""Formatacao e leitura de moeda em pt-BR. Internamente sempre centavos."""

from __future__ import annotations

_SIMBOLO = "R$"

_MESES = (
    "Janeiro",
    "Fevereiro",
    "Março",
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


def format_mes_curto(ano_mes: str) -> str:
    """Formata 'YYYY-MM' como 'Jul/26', para rotulos de eixo."""
    ano, mes = ano_mes.split("-")
    return f"{_MESES[int(mes) - 1][:3]}/{ano[2:]}"


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

    Parsing com aritmetica inteira, sem ponto flutuante. Casas decimais alem de
    duas sao truncadas ('10,999' -> R$ 10,99). Levanta ValueError se a entrada
    for vazia ou nao numerica.
    """
    limpo = texto.strip().replace(_SIMBOLO, "").replace(" ", "").replace(".", "")
    if not limpo:
        raise ValueError("Informe um valor.")
    reais, _, centavos = limpo.partition(",")
    reais = reais or "0"
    centavos = centavos[:2].ljust(2, "0")
    if not (reais.isdigit() and centavos.isdigit()):
        raise ValueError(f"Valor inválido: {texto!r}")
    return int(reais) * 100 + int(centavos)
