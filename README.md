# Poupy

Poupy é um aplicativo desktop de controle de gastos pessoais, local-first e
multiplataforma (Windows, macOS e Linux). O usuário registra seus próprios
gastos de forma simples e é dono dos dados: tudo fica gravado localmente na
máquina, num único arquivo SQLite.

- Usuário único. Não há contas, login, nuvem nem sincronização.
- Foco em gastos: registrar, listar, editar e excluir lançamentos, com
  categorias personalizáveis, total do mês e relatórios em gráficos.

Construído em Python com PySide6 (Qt 6); gráficos com pyqtgraph; dados em
SQLite pela biblioteca padrão.

## Sumário

- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Executando o aplicativo](#executando-o-aplicativo)
- [Como usar o aplicativo](#como-usar-o-aplicativo)
- [Onde os dados ficam salvos](#onde-os-dados-ficam-salvos)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Desenvolvimento](#desenvolvimento)
- [Gerando o executável com PyInstaller](#gerando-o-executável-com-pyinstaller)
- [Licença](#licença)

## Funcionalidades

- Registrar gastos com valor, data, categoria e descrição opcional.
- Listar, editar e excluir lançamentos.
- Categorias personalizáveis (criar, renomear e excluir).
- Total gasto no mês selecionado, em destaque.
- Navegação entre os meses que possuem registros.
- Gráficos de gastos por categoria e de evolução mensal do total.

## Requisitos

- Python 3.12 ou superior.
- [uv](https://docs.astral.sh/uv/) para gerenciar o ambiente e as dependências.

Instalar o uv:

```powershell
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

```sh
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

O uv cuida da versão do Python (definida em `.python-version`) e de todas as
dependências automaticamente; não é preciso criar o ambiente virtual à mão.

## Instalação

Clone o repositório e sincronize as dependências:

```sh
git clone <url-do-repositorio> poupy
cd poupy
uv sync
```

O `uv sync` cria o ambiente virtual e instala tudo a partir do `uv.lock`,
garantindo versões reprodutíveis.

## Executando o aplicativo

```sh
uv run poupy
```

O comando abre a janela do Poupy. Na primeira execução, o banco de dados é
criado automaticamente e já vem com algumas categorias padrão.

## Como usar o aplicativo

A janela principal reúne tudo em uma tela:

- **Navegador de mês:** no topo, use as setas ou o seletor para trocar o mês
  exibido. A navegação cobre do primeiro lançamento registrado até o mês atual.
- **Total do mês:** o número em destaque mostra quanto foi gasto no mês
  selecionado.
- **Novo gasto:** clique em "Novo gasto" (ou use `Ctrl+N`) para abrir o
  formulário. Informe valor, categoria, descrição (opcional) e data. Se
  precisar de uma categoria que ainda não existe, use "Nova categoria" ali
  mesmo, sem sair do fluxo.
- **Editar ou excluir:** dê um duplo clique em um lançamento da lista para
  reabrir o formulário já preenchido. A exclusão pede confirmação.
- **Categorias:** o botão "Categorias" abre a tela de gestão, onde é possível
  renomear e excluir categorias (não é possível excluir uma categoria que já
  tenha gastos vinculados).
- **Gráficos:** na parte inferior, os gráficos de gastos por categoria e de
  evolução mensal se atualizam conforme o mês selecionado.

Todos os valores são exibidos como moeda; internamente são sempre armazenados
em centavos inteiros.

## Onde os dados ficam salvos

O Poupy grava tudo em um único arquivo SQLite, num diretório de dados do
sistema obtido via `QStandardPaths.AppDataLocation`:

- **Windows:** `%APPDATA%\Poupy\Poupy\poupy.db`
- **macOS:** `~/Library/Application Support/Poupy/poupy.db`
- **Linux:** `~/.local/share/Poupy/poupy.db`

O arquivo é criado no primeiro uso e preservado entre atualizações do app.
Para fazer backup, basta copiar esse arquivo.

## Estrutura do projeto

O código segue um layout `src/` com arquitetura em camadas dentro de um único
processo. A interface nunca executa SQL diretamente: toda a lógica e o acesso
a dados passam pela camada de serviço.

```
src/poupy/
  __main__.py     Ponto de entrada (cria a aplicação Qt e a janela)
  models.py       Dataclasses tipadas do domínio
  db/             Conexão, repositório (SQL) e migrações de schema
  services/       Lógica de negócio e validações que a UI consome
  ui/             Telas e widgets Qt, tema QSS e gráficos
```

## Desenvolvimento

Comandos principais durante o desenvolvimento:

```sh
uv run poupy          # roda o app
uv run pytest         # testes (pytest + pytest-qt)
uv run ruff check     # lint e formatação
uv run mypy           # checagem de tipos (modo strict)
```

## Gerando o executável com PyInstaller

O executável é gerado com o PyInstaller a partir da receita `poupy.spec`.

**Importante:** o PyInstaller não faz cross-compile. O executável gerado é
sempre o da plataforma onde o comando roda. Para produzir o `.exe` do Windows,
rode o comando em uma máquina Windows. A mesma receita `poupy.spec` funciona
nas três plataformas.

Na pasta do projeto:

```powershell
uv sync
uv run pyinstaller poupy.spec --noconfirm
```

O resultado (modo onedir) fica em `dist/Poupy/`. No Windows, o executável é
`dist\Poupy\Poupy.exe`, acompanhado da pasta `_internal` ao lado.

Para distribuir, compacte a pasta `dist/Poupy` inteira: o executável sozinho
não roda sem a pasta `_internal`.

Notas:

- Para um único arquivo executável (mais cômodo de distribuir, porém com
  inicialização mais lenta), remova o bloco `COLLECT` de `poupy.spec` e passe
  `a.binaries` e `a.datas` diretamente no `EXE`. O modo onedir é o recomendado
  para aplicações Qt.

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para os termos completos.
