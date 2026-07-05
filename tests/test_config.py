"""Testes do ponteiro da base ativa (config.json)."""

from __future__ import annotations

from pathlib import Path

import pytest

from poupy import config


@pytest.fixture(autouse=True)
def config_temporario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redireciona o config.json para uma pasta temporaria isolada."""
    caminho = tmp_path / "config.json"
    monkeypatch.setattr(config, "caminho_config", lambda: caminho)
    return caminho


def test_round_trip(tmp_path: Path) -> None:
    base = tmp_path / "dados"
    config.gravar_config(base)
    lido = config.ler_config()
    assert lido is not None
    assert lido.active_data_path == base.resolve()


def test_arquivo_inexistente_retorna_none() -> None:
    assert config.ler_config() is None


def test_json_invalido_retorna_none(config_temporario: Path) -> None:
    config_temporario.write_text("{ nao e json", encoding="utf-8")
    assert config.ler_config() is None


def test_chave_ausente_retorna_none(config_temporario: Path) -> None:
    config_temporario.write_text('{"outra": "coisa"}', encoding="utf-8")
    assert config.ler_config() is None


def test_tema_default_claro() -> None:
    assert config.ler_tema() == "claro"


def test_tema_round_trip() -> None:
    config.gravar_tema("escuro")
    assert config.ler_tema() == "escuro"


def test_tema_valor_invalido_vira_claro(config_temporario: Path) -> None:
    config_temporario.write_text('{"theme": "roxo"}', encoding="utf-8")
    assert config.ler_tema() == "claro"


def test_tema_e_base_coexistem(tmp_path: Path) -> None:
    base = tmp_path / "dados"
    config.gravar_config(base)
    config.gravar_tema("escuro")
    # Gravar o tema nao apaga o ponteiro da base, e vice-versa.
    lido = config.ler_config()
    assert lido is not None
    assert lido.active_data_path == base.resolve()
    assert config.ler_tema() == "escuro"
