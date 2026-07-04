# Achados do code review

Estado geral: 46 testes passando, `ruff check` limpo, `mypy` strict limpo.
O codigo esta bem estruturado e coeso. Ha um bug real (item 1) e uma
melhoria opcional (item 2).

## 1. [Bug] Gasto com data futura fica orfao e pode travar o app

- Arquivo: `src/poupy/ui/gasto_dialog.py`, no `__init__` (linhas 63-66), o
  `QDateEdit` nao define data maxima:

  ```python
  self._data = QDateEdit()
  self._data.setCalendarPopup(True)
  self._data.setDisplayFormat("dd/MM/yyyy")
  self._data.setDate(QDate.currentDate())
  ```

- Problema: o usuario pode escolher uma data em um mes futuro. Mas
  `GastoService.meses_disponiveis()` (em `src/poupy/services/gastos.py`,
  linhas 91-104) limita o intervalo ao mes atual (`mes_atual`, do primeiro
  lancamento ate hoje, conforme o requisito). Consequencias:
  - Um gasto lancado em mes futuro nao aparece na lista, nao entra no total
    de nenhum mes navegavel e some dos graficos: o dado inserido "desaparece".
  - Se esse for o unico gasto do banco, `meses_disponiveis()` retorna lista
    vazia (o `while` nao executa porque `primeiro > mes_atual`). Em seguida
    `MainWindow._atualizar()` (`src/poupy/ui/main_window.py`, linhas 129-140)
    executa `self._ano_mes = meses[-1]` sobre a lista vazia e levanta
    `IndexError`, travando o app. Reproducao: app sem dados, "Novo gasto"
    com data no proximo mes, Salvar.

- Correcao sugerida: impedir datas futuras no formulario, o que fica
  coerente com o intervalo de meses definido no requisito. Adicionar no
  `__init__` do `GastoDialog`, junto da configuracao do `QDateEdit`:

  ```python
  self._data.setMaximumDate(QDate.currentDate())
  ```

  Isso resolve tanto o desaparecimento do dado quanto o crash. Cobrir com
  um teste (por exemplo, verificar que `self._data.maximumDate()` e hoje, ou
  que `meses_disponiveis()` nunca fica vazio apos um registro).

## 2. [Opcional] Textos em pt-BR sem acentuacao na UI

- Arquivos: `src/poupy/ui/format.py` (`_MESES`: "Marco", e derivados como
  "Mar/26"), `src/poupy/db/migrations.py` (`CATEGORIAS_PADRAO`:
  "Alimentacao", "Saude"), e rotulos de formulario ("Descricao", "Competencia").

- Problema: o requisito pede uma "UI elegante e profissional". Para um app
  pt-BR, exibir "Marco de 2026", "Saude" e "Descricao" sem acento fica menos
  polido. Observacao: isso parece uma escolha deliberada de todo o
  codebase (comentarios tambem sao sem acento), entao e apenas uma sugestao,
  nao um defeito.

- Correcao sugerida (se desejado): acentuar apenas as strings exibidas ao
  usuario (nomes de meses, categorias-semente e rotulos), mantendo nomes de
  simbolos/identificadores em ASCII. Atencao: mudar `CATEGORIAS_PADRAO` so
  afeta bancos novos; bancos existentes mantem os nomes ja gravados.
