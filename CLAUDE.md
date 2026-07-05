# Poupy

## Requisitos de Negócio

- Poupy é um app desktop de gastos pessoais local-first: o usuário registra seus gastos de forma simples e é dono dos próprios dados
- Usuário único. Sem contas, sem login, sem nuvem, sem sincronização - os dados vivem localmente na máquina do usuário
- Capacidades centrais: registrar gastos com valor, data, categoria e descrição opcional; listar, editar e excluir; categorias personalizáveis; total gasto do mês; relatórios de gastos por categoria e de evolução mensal como gráficos
- Por enquanto o app é somente de gastos: não há receita nem saldo. Não implementar esses conceitos por antecipação
- Manter o produto simples e focado: priorizar uma UI elegante e profissional, com gráficos prontos, acima da quantidade de funcionalidades. Implementar funcionalidades quando forem pedidas; não adicionar recursos por antecipação

## Detalhes Técnicos

- App desktop em Python com PySide6 (Qt 6), multiplataforma (Windows, macOS, Linux)
- Front-end: widgets Qt via PySide6; estilização com QSS (tema próprio para um visual elegante); gráficos com `pyqtgraph`
- Arquitetura em camadas dentro de um único processo: a UI (telas e widgets) é separada da lógica. Toda a lógica de negócio e o acesso a dados ficam numa camada de serviço/repositório tipada; a UI nunca executa SQL direto, sempre chama o serviço
- Banco: SQLite via módulo `sqlite3` da stdlib, um único arquivo local na máquina do usuário (um arquivo `.db`, sem dependência extra). O caminho do arquivo `.db` NÃO é fixo em `AppDataLocation`: o usuário cria uma base nova ou abre um `.db` existente, e o caminho é resolvido pela camada de base ativa descrita em "Armazenamento de dados e base ativa". Mudanças de schema tratadas com migrações simples e versionadas via `PRAGMA user_version`
- Estrutura (`src/` layout): `poupy/ui` (telas e widgets Qt), `poupy/services` (lógica de negócio), `poupy/db` (conexão, repositórios e migrações), `poupy/models` (dataclasses tipadas). Ponto de entrada em `poupy/__main__.py`
- Ambiente e dependências: `uv` (`uv init`, `uv add`, `uv run`). Lint e formatação com `ruff`. Tipos com `mypy` em modo strict. Testes com `pytest` e `pytest-qt`
- Empacotamento e distribuição: `PyInstaller` para as três plataformas

## Armazenamento de dados e base ativa

Esta seção é a fonte de verdade sobre onde os dados vivem e como o app escolhe
com qual base trabalhar. Ela substitui qualquer suposição anterior de que o
`poupy.db` fica sempre em `AppDataLocation`.

### Conceitos

- **Base**: um arquivo `.db` (o banco em si), criado ou escolhido pelo usuário,
  com nome livre e em qualquer pasta. Os arquivos sidecar do WAL (`-wal`/`-shm`)
  vivem ao lado dele, na mesma pasta. O app opera sobre UMA base ativa por vez.
- **Ponteiro da base ativa**: um `config.json` gravado no diretório de
  configuração do sistema operacional, FORA da pasta de dados, apontando para o
  ARQUIVO `.db` da base ativa.

### Invariante crítico: o ponteiro fica no diretório de config do SO

- O `config.json` é gravado no diretório de configuração do SO, obtido via
  `QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)`
  (nunca com caminho fixo no código). Isso resolve para:
  - **Windows** (foco principal): `%APPDATA%\Poupy\config.json`
  - **Linux**: `~/.config/poupy/config.json`
  - **macOS**: `~/Library/Application Support/Poupy/config.json`
- Conteúdo mínimo: `{ "activeDataPath": "<caminho absoluto do arquivo .db>" }`.
- INVARIANTE: o ponteiro NUNCA pode ficar dentro da pasta de dados. Se ficasse,
  cai-se num paradoxo ovo-e-galinha: o app precisaria já saber onde estão os
  dados para ler o ponteiro que diz onde estão os dados. Por isso o ponteiro
  mora no diretório de config do SO e a pasta de dados é separada.
- Distinção clara: diretório de config do SO = casa do `config.json` (ponteiro);
  o arquivo `.db` (criado/escolhido pelo usuário, com nome livre) = a base.

### Primeira execução (onboarding)

Disparar o fluxo de primeira execução quando não há uma base ativa utilizável:
`activeDataPath` ausente (config inexistente, ilegível ou sem a chave) OU o
arquivo `.db` apontado pelo config não existe mais (apagado, HD externo
desconectado, nuvem ainda não sincronizada). Neste último caso, SEMPRE
re-perguntar via onboarding e NUNCA recriar silenciosamente um `.db` vazio no
mesmo caminho: isso enganaria o usuário fazendo parecer que os dados sumiram
quando o arquivo está apenas temporariamente inacessível.

O onboarding oferece DOIS caminhos: criar uma base nova ou abrir um arquivo `.db`
já existente (de outra instância, cópia ou backup). Passos:

1. Exibir uma explicação breve: os dados ficam guardados localmente, num arquivo
   `.db`; o usuário é responsável pelo backup (basta fechar o app e copiar o
   arquivo).
2. Criar base nova (fluxo padrão): oferecer um local padrão sensato JÁ
   PREENCHIDO — `Documentos/Poupy` (derivar `Documentos` de
   `QStandardPaths.DocumentsLocation`) — e um botão que abre o seletor NATIVO de
   pastas (`QFileDialog.getExistingDirectory`) para escolher outra pasta; cria-se
   um `poupy.db` dentro dela.
3. Abrir base existente: um botão que abre o seletor NATIVO de arquivos
   (`QFileDialog.getOpenFileName`, filtro `*.db`) para apontar diretamente para
   um arquivo `.db` já existente, com qualquer nome e em qualquer pasta.
4. Ao confirmar CRIAR: validar permissão de escrita na pasta -> criar o `.db`
   (gravar o `application_id` do Poupy e aplicar migrações) -> gravar o caminho
   do arquivo em `activeDataPath`.
5. Ao confirmar ABRIR: validar que o arquivo é um banco Poupy legível (ver
   "Validação da base ao abrir") -> aplicar migrações se for base antiga ->
   gravar o caminho do arquivo em `activeDataPath`.

### Validação da base ao abrir

Ao apontar para um arquivo `.db` (no onboarding, ao abrir um existente, ou no
boot ao reabrir a base do `config.json`), validar em CAMADAS, NESTA ORDEM. A
ordem é o ponto crítico: confirmar a IDENTIDADE do arquivo ANTES de migrar.

1. **É um SQLite íntegro?** `PRAGMA integrity_check`. Um `.db` pode ser um
   arquivo qualquer renomeado ou um banco truncado. Se falhar, recusar ("o
   arquivo não é um banco válido").
2. **É um banco do Poupy?** `PRAGMA application_id` comparado com a constante do
   Poupy (gravada na criação da base). Se não bate, recusar ("não é um banco do
   Poupy") — assim um `.db` de outro programa é rejeitado sem depender de
   adivinhar pela estrutura das tabelas.
3. **Não é de versão futura?** Se `PRAGMA user_version` for MAIOR que a última
   migração conhecida, recusar ("base criada por uma versão mais nova do Poupy;
   atualize o app"). NUNCA rebaixar nem migrar para trás.
4. **Só então migrar.** `aplicar_migracoes` leva bases antigas para frente.
5. **Rede final:** conferir que as tabelas esperadas existem (`categoria`,
   `gasto`).

INVARIANTE: validar identidade (passos 1-3) ANTES de aplicar migrações. Se as
migrações rodassem primeiro num arquivo alheio, criariam as tabelas do Poupy
DENTRO do arquivo do usuário, sujando-o antes de o app perceber que não era um
banco Poupy.

Distinção criar vs. abrir: ao CRIAR uma base nova, o arquivo é novo/vazio —
grava-se o `application_id` do Poupy e aplicam-se as migrações. Ao ABRIR um
arquivo existente, ele passa pelas camadas acima antes de qualquer escrita.

### Trocar de base (sem tela de configurações)

DECISÃO DE DESIGN: o onboarding é o ÚNICO ponto em que o usuário escolhe a base.
NÃO existe tela de configurações nem botão de engrenagem para troca de base; NÃO
há troca de conexão "a quente" com a UI carregada. Isso mantém o app simples e
evita UI de gerência de base que não foi pedida.

Para trocar de base, apontar para uma cópia ou restaurar um backup, o fluxo é
manual e NÃO-DESTRUTIVO: fechar o app -> apagar o `config.json` (ou mover/apagar
o `.db` atual) -> reabrir o app, que cai no onboarding, onde se cria uma base
nova OU se abre um `.db` existente (inclusive o de outro local, cópia ou
backup). A base antiga permanece intacta onde estava, e o usuário pode voltar a
ela abrindo aquele arquivo de novo pelo onboarding.

### Fora de escopo (decisões de design - NÃO implementar)

- SEM tela de configurações / botão de engrenagem para troca de base: o
  onboarding é o único ponto de escolha de base — criar OU abrir arquivo (ver
  acima).
- SEM função de "migrar/mover dados": trocar de base nunca move nem apaga a base
  antiga. Abrir um `.db` existente APONTA o ponteiro para ele — não copia nem
  importa nada.
- SEM botão de exportar/importar backup: backup = o usuário copia o arquivo
  `.db` manualmente com o app fechado.
- Replicar uma base = copiar o arquivo `.db` com o app fechado e abri-lo pelo
  onboarding (apagando o `config.json` ou o `.db` atual). NÃO criar UI dedicada
  para isso.

### Invariantes e cuidados técnicos de SQLite/WAL

- **Modo WAL + checkpoint ao fechar**: usar `PRAGMA journal_mode=WAL`. Ao
  encerrar o processo, executar checkpoint (`PRAGMA wal_checkpoint(TRUNCATE)`) e
  fechar a conexão de forma limpa, para que o arquivo `.db` fique completo e
  íntegro. Isso torna o modelo "fechar o app + copiar o arquivo" um backup
  confiável.
- **Arquivos sidecar do WAL**: o SQLite gera `<arquivo>.db-wal` e
  `<arquivo>.db-shm` ao lado do `.db` escolhido, em runtime; o usuário nunca os
  traz nem copia. A detecção de "base existente" deve olhar SOMENTE o arquivo
  `.db`. Qualquer cópia de dados deve ocorrer com o app fechado (ou após
  checkpoint e fechamento da conexão).
- **Validação de escrita**: verificar permissão de escrita na PASTA que contém o
  `.db` (é lá que o WAL será criado) antes de gravar o ponteiro; tratar caminhos
  de forma cross-platform (`pathlib.Path`).
- **Validação da base ao abrir**: ver a subseção "Validação da base ao abrir"
  acima — validar identidade (SQLite íntegro + banco Poupy + versão não-futura)
  ANTES de aplicar as migrações de schema (`PRAGMA user_version`).
- **Config ausente/corrompido ou base sumida**: se `config.json` sumir ou
  estiver ilegível (ex.: o usuário levou só o `.exe` para outra máquina), ou se
  o arquivo `.db` apontado não existir mais, cair naturalmente no fluxo de
  primeira execução (sem recriar base silenciosamente).
- **Pasta em nuvem (Google Drive / OneDrive / Dropbox)**: suportada como destino
  de backup. Existe o risco de corromper o SQLite ao abrir a mesma base
  sincronizada em duas máquinas ao mesmo tempo; como a escolha de pasta agora é
  só no onboarding (rara), não há UI dedicada de aviso nem bloqueio. No máximo,
  mencionar o risco no texto do onboarding. Não implementar lock distribuído.
- **Índice de data e filtro por mês**: os filtros por mês usam
  `substr(data, 1, 7) = ?`, que NÃO aproveita o índice `idx_gasto_data` (criado
  sobre a data inteira) e faz varredura. DECISÃO DE DESIGN: manter assim — no
  volume de um app pessoal o custo é irrelevante e a consulta fica mais simples.
  NÃO trocar por filtro de range (`data >= 'YYYY-MM-01' AND data < proximo_mes`)
  por antecipação; só reconsiderar se algum dia o volume realmente pesar.

### Distribuição (executável único) - implicações

- Alvo de distribuição: um executável único (`Poupy.exe`), sem instalador e sem
  desinstalador. Atualização = substituir o `.exe`; os dados permanecem intactos
  porque vivem no arquivo `.db` (a base) + ponteiro em `%APPDATA%\Poupy`.
- Driver do SQLite embutido: nesta stack o `sqlite3` é da biblioteca padrão do
  Python e o PyInstaller já o embute no bundle - NÃO há módulo nativo extra para
  reempacotar (ao contrário de Electron, que exigiria rebuild do módulo nativo,
  ou .NET single-file, que embute o provider). Nenhum cuidado especial de driver.
- Tensão a reconciliar com o empacotamento atual: o alvo "arquivo único" mapeia
  para o modo `onefile` do PyInstaller, enquanto a receita atual (`poupy.spec`,
  ver README) usa `onedir` (recomendado para apps Qt, inicialização mais rápida).
  Ao implementar a distribuição single-file, decidir explicitamente entre
  `onefile` (um `.exe`, startup mais lento por extração em temp) e manter
  `onedir`, e alinhar README e `poupy.spec` com a decisão. Não trocar o modo por
  antecipação sem essa decisão.
- `.exe` não assinado aciona o SmartScreen do Windows na primeira execução; isso
  deve estar documentado no README ("Mais informações -> Executar assim mesmo").

## Interface e UX

- Janela principal: um cabeçalho com o navegador de mês, um número de destaque com o total gasto no mês selecionado, a lista de lançamentos do mês e os gráficos
- Navegação por mês: setas para mês anterior/seguinte, limitadas ao intervalo de meses que possuem registros (do primeiro lançamento até o mês atual); um dropdown lista os meses disponíveis, derivado dos ano-meses distintos no banco. Abre no mês atual por padrão
- Novo gasto: um botão "Novo gasto" (e atalho de teclado) abre um pop-up modal (`QDialog`) que pede Valor, Categoria, Descrição (opcional) e Data (default: hoje). Confirmar salva; cancelar descarta
- Categoria no formulário: um dropdown com as categorias existentes. Criar, renomear e excluir categorias ficam numa tela de Categorias à parte
- Editar/excluir: selecionar um lançamento na lista abre o mesmo pop-up já preenchido; excluir pede confirmação
- Gráficos, reagindo ao mês/período selecionado: gastos por categoria (pizza ou barras) e evolução mensal do total gasto (linha ou barras) ao longo dos meses registrados
- Valores exibidos como moeda; internamente sempre centavos inteiros

## Estratégia

1. Para cada funcionalidade, escrever um plano com critérios de sucesso a serem marcados antes de codar, incluindo testes
2. Executar o plano, garantindo que todos os critérios sejam atendidos antes de seguir
3. Fazer testes de integração com `pytest` e `pytest-qt`, corrigindo defeitos, e confirmar que os dados persistem após reiniciar o app
4. Considerar uma funcionalidade concluída apenas quando estiver testada, compilando e rodando

## Padrões de Código

1. Usar as versões mais recentes das bibliotecas e abordagens idiomáticas atuais
2. Manter simples - NUNCA superengenharia, SEMPRE simplificar, SEM programação defensiva desnecessária. Sem recursos além do que foi pedido. Na dúvida entre uma solução simples e uma elaborada, escolher a simples
3. Em caso de ambiguidade ou informação faltante, PERGUNTAR antes de codar; nunca presumir requisitos nem inventar escopo
4. Se um comando ou pedido do usuário estiver errado, for inconsistente com este documento ou tecnicamente inviável, apontar isso e sugerir a correção essencial antes de prosseguir; fazer apenas sugestões essenciais, sem ruído
5. Dinheiro é SEMPRE armazenado e calculado como centavos inteiros, NUNCA ponto flutuante. Formatar como moeda apenas na exibição
6. Type hints em tudo; `mypy` em modo strict. Evitar `Any`; deixar os tipos pegarem os erros cedo
7. Manter a UI separada da lógica e dos dados: a UI nunca executa SQL, toda comunicação com o banco passa pela camada de serviço/repositório tipada
8. Ser conciso. Manter o README mínimo. IMPORTANTE: nunca usar emojis na UI, no código, nos commits ou na documentação

## Plan

A base como arquivo `.db` está implementada: o onboarding cria uma base nova OU
abre um `.db` existente, com validação em camadas ao abrir (identidade antes de
migrar), conforme a seção "Armazenamento de dados e base ativa" acima (fonte de
verdade). O histórico faseado do trabalho está em @docs/PLAN.md.
