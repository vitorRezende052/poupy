"""Ponteiro da base ativa e preferencias: leitura/escrita do config.json.

O config.json fica no diretorio de configuracao do SO (AppConfigLocation),
FORA da base. Se ficasse ao lado dela, cairia num paradoxo ovo-e-galinha: o app
precisaria ja saber onde estao os dados para ler o ponteiro que diz onde estao
os dados. Guarda o caminho do ARQUIVO .db da base ativa (`activeDataPath`) e o
tema escolhido (`theme`), que coexistem no mesmo arquivo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QStandardPaths


@dataclass(frozen=True)
class Config:
    active_data_path: Path


def caminho_config() -> Path:
    """Caminho do config.json no diretorio de config do SO, criando o diretorio."""
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    diretorio = Path(base)
    diretorio.mkdir(parents=True, exist_ok=True)
    return diretorio / "config.json"


def _ler_bruto() -> dict[str, str]:
    """Le o config.json inteiro. Ausente, ilegivel ou nao-objeto -> {}."""
    try:
        dados = json.loads(caminho_config().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(dados, dict):
        return {}
    return dados


def _gravar_bruto(dados: dict[str, str]) -> None:
    caminho_config().write_text(json.dumps(dados), encoding="utf-8")


def ler_config() -> Config | None:
    """Le o ponteiro da base ativa. Ausente ou sem a chave -> None."""
    caminho = _ler_bruto().get("activeDataPath")
    if not isinstance(caminho, str):
        return None
    return Config(active_data_path=Path(caminho))


def gravar_config(active_data_path: Path) -> None:
    """Grava o ponteiro para o arquivo .db da base ativa, preservando o tema."""
    dados = _ler_bruto()
    dados["activeDataPath"] = str(active_data_path.resolve())
    _gravar_bruto(dados)


def ler_tema() -> str:
    """Le o tema salvo ('claro' ou 'escuro'); qualquer outro valor -> 'claro'."""
    tema = _ler_bruto().get("theme")
    return tema if tema in ("claro", "escuro") else "claro"


def gravar_tema(nome: str) -> None:
    """Grava o tema escolhido, preservando o ponteiro da base."""
    dados = _ler_bruto()
    dados["theme"] = nome
    _gravar_bruto(dados)
