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

O comando abre a janela do Poupy. Na primeira execução, o app pergunta onde
guardar seus dados (veja [Onde os dados ficam salvos](#onde-os-dados-ficam-salvos))
e cria a base já com algumas categorias padrão.

## Como usar o aplicativo

A janela principal reúne tudo em uma tela:

- **Navegador de mês:** no topo, use as setas ou o seletor para trocar o mês
  exibido. A navegação cobre do primeiro lançamento registrado até o mês atual.
- **Total do mês:** o número em destaque mostra quanto foi gasto no mês
  selecionado.
- **Novo gasto:** clique em "Novo gasto" (ou use `Ctrl+N`) para abrir o
  formulário. Informe valor, categoria, descrição (opcional) e data. A
  categoria é escolhida em um dropdown com as categorias existentes.
- **Editar ou excluir:** dê um duplo clique em um lançamento da lista para
  reabrir o formulário já preenchido. A exclusão pede confirmação.
- **Categorias:** o botão "Categorias" abre a tela de gestão, onde é possível
  criar, renomear e excluir categorias (não é possível excluir uma categoria
  que já tenha gastos vinculados).
- **Gráficos:** na parte inferior, os gráficos de gastos por categoria e de
  evolução mensal se atualizam conforme o mês selecionado.

Todos os valores são exibidos como moeda; internamente são sempre armazenados
em centavos inteiros.

## Onde os dados ficam salvos

O Poupy guarda tudo em uma **base**: uma pasta escolhida por você que contém um
único arquivo SQLite (`poupy.db`). Na primeira execução, o app explica isso e já
sugere um local padrão (`Documentos/Poupy`); você pode confirmar ou escolher
outra pasta pelo seletor nativo.

O caminho da base ativa é lembrado num pequeno arquivo de configuração do
sistema (`config.json`), gravado separadamente dos seus dados:

- **Windows:** `%APPDATA%\Poupy\config.json`
- **macOS:** `~/Library/Application Support/Poupy/config.json`
- **Linux:** `~/.config/poupy/config.json`

### Backup

Você é o dono dos dados e o responsável pelo backup. Para fazer backup, **feche
o app e copie a pasta da base** (a que contém o `poupy.db`) para onde quiser,
inclusive uma pasta de nuvem como OneDrive, Google Drive ou Dropbox. Feche o app
antes de copiar para garantir um arquivo íntegro.

Atenção: use a nuvem como destino de backup, mas evite abrir a MESMA base
sincronizada em dois computadores ao mesmo tempo - isso pode corromper o banco.

### Trocar de base ou usar em outro computador

O onboarding da primeira execução é o único ponto em que você escolhe a pasta da
base; não há tela de configurações. Para apontar o app para outra pasta (uma
cópia, um backup restaurado ou os dados em outro computador), o fluxo é manual e
**não-destrutivo**:

1. Feche o app.
2. Mova ou apague o `poupy.db` da pasta atual, ou apague o `config.json` (o
   ponteiro; veja os caminhos acima).
3. Reabra o app: sem uma base ativa, ele cai no onboarding e deixa você escolher
   a nova pasta.
   - Uma pasta **vazia** vira uma base nova, do zero.
   - Uma pasta que já contém `poupy.db` **abre aquela base existente**.

A base anterior continua intacta na pasta antiga, e você pode voltar a ela
apontando o onboarding de volta para aquela pasta. Para levar seus dados a outro
computador, copie a pasta da base (com o app fechado) e, no outro computador,
aponte o onboarding para a cópia.

Se a pasta da base ficar indisponível (HD externo desconectado, nuvem ainda não
sincronizada), o app não recria os dados por conta própria: ele volta ao
onboarding para você reconectar a pasta ou escolher outra.

### Atualização

Para atualizar, basta substituir o executável. Seus dados permanecem intactos,
porque vivem em uma pasta separada (a base) e o app apenas guarda o ponteiro
para ela.

## Estrutura do projeto

O código segue um layout `src/` com arquitetura em camadas dentro de um único
processo. A interface nunca executa SQL diretamente: toda a lógica e o acesso
a dados passam pela camada de serviço.

```
src/poupy/
  __main__.py     Ponto de entrada (resolve a base ativa e cria a janela)
  config.py       Ponteiro da base ativa (config.json no dir de config do SO)
  models.py       Dataclasses tipadas do domínio
  db/             Conexão, repositório (SQL) e migrações de schema
  services/       Lógica de negócio e validações que a UI consome
  ui/             Telas e widgets Qt (inclui o onboarding), tema QSS e gráficos
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

O resultado (modo onefile) é um único executável em `dist/`. No Windows, é
`dist\Poupy.exe`. Para distribuir, basta esse arquivo: não há pasta de apoio
nem instalador. Atualizar é substituir o `.exe`; seus dados não são afetados,
porque vivem numa pasta separada (a base) com o ponteiro em `%APPDATA%\Poupy`.

Notas:

- O modo onefile extrai os arquivos para uma pasta temporária a cada execução,
  então a inicialização é um pouco mais lenta que a de uma pasta onedir. A troca
  vale a distribuição em arquivo único.
- O `sqlite3` vem da biblioteca padrão do Python e já é embutido pelo
  PyInstaller; não há módulo nativo extra para reempacotar.
- O executável não é assinado. Na primeira execução no Windows, o SmartScreen
  pode exibir um aviso; escolha "Mais informações" e depois "Executar assim
  mesmo" para abrir o app.

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para os termos completos.
