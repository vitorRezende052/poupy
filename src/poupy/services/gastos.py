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
        nome_limpo = self._nome_categoria_valido(nome)
        try:
            return repository.criar_categoria(self._conn, nome_limpo)
        except sqlite3.IntegrityError as erro:
            raise ValueError(f"Já existe uma categoria chamada '{nome_limpo}'.") from erro

    def renomear_categoria(self, categoria_id: int, nome: str) -> None:
        nome_limpo = self._nome_categoria_valido(nome)
        try:
            repository.renomear_categoria(self._conn, categoria_id, nome_limpo)
        except sqlite3.IntegrityError as erro:
            raise ValueError(f"Já existe uma categoria chamada '{nome_limpo}'.") from erro

    def excluir_categoria(self, categoria_id: int) -> None:
        if repository.categoria_em_uso(self._conn, categoria_id):
            raise ValueError("Não é possível excluir uma categoria com gastos vinculados.")
        repository.excluir_categoria(self._conn, categoria_id)

    def registrar_gasto(
        self,
        valor_centavos: int,
        data: date,
        categoria_id: int,
        descricao: str | None,
    ) -> Gasto:
        descricao_limpa = self._validar(valor_centavos, descricao)
        gasto_id = repository.inserir_gasto(
            self._conn, valor_centavos, data, categoria_id, descricao_limpa
        )
        return self._montar_gasto(gasto_id, valor_centavos, data, categoria_id, descricao_limpa)

    def atualizar_gasto(
        self,
        gasto_id: int,
        valor_centavos: int,
        data: date,
        categoria_id: int,
        descricao: str | None,
    ) -> Gasto:
        descricao_limpa = self._validar(valor_centavos, descricao)
        repository.atualizar_gasto(
            self._conn, gasto_id, valor_centavos, data, categoria_id, descricao_limpa
        )
        return self._montar_gasto(gasto_id, valor_centavos, data, categoria_id, descricao_limpa)

    def excluir_gasto(self, gasto_id: int) -> None:
        repository.excluir_gasto(self._conn, gasto_id)

    def gastos_do_mes(self, ano_mes: str) -> list[Gasto]:
        return repository.gastos_do_mes(self._conn, ano_mes)

    def total_do_mes(self, ano_mes: str) -> int:
        return repository.total_do_mes(self._conn, ano_mes)

    def gastos_por_categoria(self, ano_mes: str) -> list[tuple[str, int]]:
        """(nome, total_centavos) por categoria no mes, do maior para o menor."""
        return repository.total_por_categoria(self._conn, ano_mes)

    def evolucao_mensal(self) -> list[tuple[str, int]]:
        """(ano_mes, total_centavos) para cada mes do intervalo continuo.

        Meses sem lancamento entram com total 0, para a linha nao distorcer.
        """
        totais = dict(repository.total_por_mes(self._conn))
        return [(mes, totais.get(mes, 0)) for mes in self.meses_disponiveis()]

    def meses_disponiveis(self) -> list[str]:
        """Intervalo continuo 'YYYY-MM' do primeiro lancamento ate o mes atual.

        Ascendente. Sem lancamentos, retorna apenas o mes atual.
        """
        mes_atual = date.today().strftime("%Y-%m")
        primeiro = repository.primeiro_mes(self._conn) or mes_atual
        meses: list[str] = []
        ano, mes = map(int, primeiro.split("-"))
        ano_fim, mes_fim = map(int, mes_atual.split("-"))
        while (ano, mes) <= (ano_fim, mes_fim):
            meses.append(f"{ano:04d}-{mes:02d}")
            ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)
        return meses

    def _nome_categoria_valido(self, nome: str) -> str:
        """Normaliza o nome da categoria; rejeita vazio."""
        nome_limpo = nome.strip()
        if not nome_limpo:
            raise ValueError("O nome da categoria não pode ser vazio.")
        return nome_limpo

    def _validar(self, valor_centavos: int, descricao: str | None) -> str | None:
        """Valida o valor e devolve a descricao normalizada (vazio vira None)."""
        if valor_centavos <= 0:
            raise ValueError("O valor do gasto deve ser maior que zero.")
        return (descricao or "").strip() or None

    def _montar_gasto(
        self,
        gasto_id: int,
        valor_centavos: int,
        data: date,
        categoria_id: int,
        descricao: str | None,
    ) -> Gasto:
        return Gasto(
            id=gasto_id,
            valor_centavos=valor_centavos,
            data=data,
            categoria_id=categoria_id,
            categoria_nome=self._nome_categoria(categoria_id),
            descricao=descricao,
        )

    def _nome_categoria(self, categoria_id: int) -> str:
        return repository.nome_categoria(self._conn, categoria_id)
