"""Camada de servico: API de negocio que a UI consome.

A UI fala apenas com esta camada, nunca com o repositorio ou o SQLite
diretamente. Aqui ficam as validacoes e regras de negocio.
"""

from __future__ import annotations

import sqlite3
from datetime import date

from poupy.db import repository
from poupy.models import Categoria, Gasto


class GastoService:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def categorias(self) -> list[Categoria]:
        return repository.listar_categorias(self._conn)

    def criar_categoria(self, nome: str) -> Categoria:
        nome_limpo = nome.strip()
        if not nome_limpo:
            raise ValueError("O nome da categoria nao pode ser vazio.")
        return repository.criar_categoria(self._conn, nome_limpo)

    def registrar_gasto(
        self,
        valor_centavos: int,
        data: date,
        categoria_id: int,
        descricao: str | None,
    ) -> Gasto:
        if valor_centavos <= 0:
            raise ValueError("O valor do gasto deve ser maior que zero.")
        descricao_limpa = (descricao or "").strip() or None
        gasto_id = repository.inserir_gasto(
            self._conn, valor_centavos, data, categoria_id, descricao_limpa
        )
        return Gasto(
            id=gasto_id,
            valor_centavos=valor_centavos,
            data=data,
            categoria_id=categoria_id,
            categoria_nome=self._nome_categoria(categoria_id),
            descricao=descricao_limpa,
        )

    def gastos_do_mes(self, ano_mes: str) -> list[Gasto]:
        return repository.gastos_do_mes(self._conn, ano_mes)

    def total_do_mes(self, ano_mes: str) -> int:
        return repository.total_do_mes(self._conn, ano_mes)

    def _nome_categoria(self, categoria_id: int) -> str:
        for categoria in self.categorias():
            if categoria.id == categoria_id:
                return categoria.nome
        raise ValueError(f"Categoria {categoria_id} nao encontrada.")
