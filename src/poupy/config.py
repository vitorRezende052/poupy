"""Ponteiro da base ativa: leitura/escrita do config.json.

O config.json fica no diretorio de configuracao do SO (AppConfigLocation),
FORA da base. Se ficasse ao lado dela, cairia num paradoxo ovo-e-galinha: o app
precisaria ja saber onde estao os dados para ler o ponteiro que diz onde estao
os dados. O ponteiro guarda o caminho do ARQUIVO .db da base ativa.
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


def ler_config() -> Config | None:
    """Le o ponteiro da base ativa. Ausente, ilegivel ou sem a chave -> None."""
    try:
        dados = json.loads(caminho_config().read_text(encoding="utf-8"))
        return Config(active_data_path=Path(dados["activeDataPath"]))
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return None


def gravar_config(active_data_path: Path) -> None:
    """Grava o ponteiro para o arquivo .db da base ativa (caminho absoluto)."""
    conteudo = json.dumps({"activeDataPath": str(active_data_path.resolve())})
    caminho_config().write_text(conteudo, encoding="utf-8")
