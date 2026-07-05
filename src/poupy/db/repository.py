"""Acesso a dados tipado. Unico lugar que executa SQL.

A UI nunca chama estas funcoes diretamente: sempre via camada de servico.
Datas sao guardadas como texto ISO (YYYY-MM-DD); o mes e derivado por
substr(data, 1, 7) == 'YYYY-MM'.
"""

from __future__ import annotations

import sqlite3
from datetime import date

from poupy.models import Categoria, Gasto


def listar_categorias(conn: sqlite3.Connection) -> list[Categoria]:
    linhas = conn.execute("SELECT id, nome FROM categoria ORDER BY nome").fetchall()
    return [Categoria(id=linha["id"], nome=linha["nome"]) for linha in linhas]


def nome_categoria(conn: sqlite3.Connection, categoria_id: int) -> str:
    """Nome de uma categoria pelo id. Levanta ValueError se nao existir."""
    linha = conn.execute("SELECT nome FROM categoria WHERE id = ?", (categoria_id,)).fetchone()
    if linha is None:
        raise ValueError(f"Categoria {categoria_id} não encontrada.")
    return str(linha["nome"])


def criar_categoria(conn: sqlite3.Connection, nome: str) -> Categoria:
    cursor = conn.execute("INSERT INTO categoria (nome) VALUES (?)", (nome,))
    conn.commit()
    return Categoria(id=int(cursor.lastrowid or 0), nome=nome)


def renomear_categoria(conn: sqlite3.Connection, categoria_id: int, nome: str) -> None:
    conn.execute("UPDATE categoria SET nome = ? WHERE id = ?", (nome, categoria_id))
    conn.commit()


def excluir_categoria(conn: sqlite3.Connection, categoria_id: int) -> None:
    conn.execute("DELETE FROM categoria WHERE id = ?", (categoria_id,))
    conn.commit()


def categoria_em_uso(conn: sqlite3.Connection, categoria_id: int) -> bool:
    linha = conn.execute(
        "SELECT 1 FROM gasto WHERE categoria_id = ? LIMIT 1", (categoria_id,)
    ).fetchone()
    return linha is not None


def inserir_gasto(
    conn: sqlite3.Connection,
    valor_centavos: int,
    data: date,
    categoria_id: int,
    descricao: str | None,
) -> int:
    cursor = conn.execute(
        "INSERT INTO gasto (valor_centavos, data, categoria_id, descricao) VALUES (?, ?, ?, ?)",
        (valor_centavos, data.isoformat(), categoria_id, descricao),
    )
    conn.commit()
    return int(cursor.lastrowid or 0)


def atualizar_gasto(
    conn: sqlite3.Connection,
    gasto_id: int,
    valor_centavos: int,
    data: date,
    categoria_id: int,
    descricao: str | None,
) -> None:
    conn.execute(
        "UPDATE gasto SET valor_centavos = ?, data = ?, categoria_id = ?, descricao = ? "
        "WHERE id = ?",
        (valor_centavos, data.isoformat(), categoria_id, descricao, gasto_id),
    )
    conn.commit()


def excluir_gasto(conn: sqlite3.Connection, gasto_id: int) -> None:
    conn.execute("DELETE FROM gasto WHERE id = ?", (gasto_id,))
    conn.commit()


def gastos_do_mes(conn: sqlite3.Connection, ano_mes: str) -> list[Gasto]:
    """Gastos de um mes 'YYYY-MM', mais recentes primeiro."""
    linhas = conn.execute(
        """
        SELECT g.id, g.valor_centavos, g.data, g.categoria_id,
               c.nome AS categoria_nome, g.descricao
        FROM gasto g
        JOIN categoria c ON c.id = g.categoria_id
        WHERE substr(g.data, 1, 7) = ?
        ORDER BY g.data DESC, g.id DESC
        """,
        (ano_mes,),
    ).fetchall()
    return [
        Gasto(
            id=linha["id"],
            valor_centavos=linha["valor_centavos"],
            data=date.fromisoformat(linha["data"]),
            categoria_id=linha["categoria_id"],
            categoria_nome=linha["categoria_nome"],
            descricao=linha["descricao"],
        )
        for linha in linhas
    ]


def total_do_mes(conn: sqlite3.Connection, ano_mes: str) -> int:
    """Soma em centavos dos gastos de um mes 'YYYY-MM'."""
    linha = conn.execute(
        "SELECT COALESCE(SUM(valor_centavos), 0) AS total FROM gasto WHERE substr(data, 1, 7) = ?",
        (ano_mes,),
    ).fetchone()
    return int(linha["total"])


def total_por_categoria(conn: sqlite3.Connection, ano_mes: str) -> list[tuple[str, int]]:
    """(nome_categoria, soma_centavos) do mes, do maior para o menor."""
    linhas = conn.execute(
        """
        SELECT c.nome AS nome, SUM(g.valor_centavos) AS total
        FROM gasto g
        JOIN categoria c ON c.id = g.categoria_id
        WHERE substr(g.data, 1, 7) = ?
        GROUP BY c.id
        ORDER BY total DESC
        """,
        (ano_mes,),
    ).fetchall()
    return [(linha["nome"], int(linha["total"])) for linha in linhas]


def total_por_mes(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """(ano_mes, soma_centavos) de cada mes com registro, em ordem crescente."""
    linhas = conn.execute(
        """
        SELECT substr(data, 1, 7) AS mes, SUM(valor_centavos) AS total
        FROM gasto
        GROUP BY mes
        ORDER BY mes
        """
    ).fetchall()
    return [(linha["mes"], int(linha["total"])) for linha in linhas]


def primeiro_mes(conn: sqlite3.Connection) -> str | None:
    """Ano-mes 'YYYY-MM' do lancamento mais antigo, ou None se nao ha gastos."""
    linha = conn.execute("SELECT min(substr(data, 1, 7)) AS mes FROM gasto").fetchone()
    mes = linha["mes"]
    return None if mes is None else str(mes)
