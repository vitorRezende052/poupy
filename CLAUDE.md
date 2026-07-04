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
- Banco: SQLite via módulo `sqlite3` da stdlib, um único arquivo local na máquina do usuário (`poupy.db`, sem dependência extra). O caminho da pasta de dados NÃO é fixo em `AppDataLocation`: é definido pelo usuário e resolvido pela camada de base ativa descrita em "Armazenamento de dados e base ativa". Mudanças de schema tratadas com migrações simples e versionadas via `PRAGMA user_version`
- Estrutura (`src/` layout): `poupy/ui` (telas e widgets Qt), `poupy/services` (lógica de negócio), `poupy/db` (conexão, repositórios e migrações), `poupy/models` (dataclasses tipadas). Ponto de entrada em `poupy/__main__.py`
- Ambiente e dependências: `uv` (`uv init`, `uv add`, `uv run`). Lint e formatação com `ruff`. Tipos com `mypy` em modo strict. Testes com `pytest` e `pytest-qt`
- Empacotamento e distribuição: `PyInstaller` para as três plataformas

## Armazenamento de dados e base ativa

Esta seção é a fonte de verdade sobre onde os dados vivem e como o app escolhe
com qual base trabalhar. Ela substitui qualquer suposição anterior de que o
`poupy.db` fica sempre em `AppDataLocation`.

### Conceitos

- **Base**: uma pasta que contém o arquivo `poupy.db` (e, no futuro, backups e
  anexos). O app opera sobre UMA base ativa por vez.
- **Ponteiro da base ativa**: um `config.json` gravado no diretório de
  configuração do sistema operacional, FORA da pasta de dados, apontando para a
  pasta da base ativa.

### Invariante crítico: o ponteiro fica no diretório de config do SO

- O `config.json` é gravado no diretório de configuração do SO, obtido via
  `QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)`
  (nunca com caminho fixo no código). Isso resolve para:
  - **Windows** (foco principal): `%APPDATA%\Poupy\config.json`
  - **Linux**: `~/.config/poupy/config.json`
  - **macOS**: `~/Library/Application Support/Poupy/config.json`
- Conteúdo mínimo: `{ "activeDataPath": "<caminho absoluto da pasta de dados>" }`.
- INVARIANTE: o ponteiro NUNCA pode ficar dentro da pasta de dados. Se ficasse,
  cai-se num paradoxo ovo-e-galinha: o app precisaria já saber onde estão os
  dados para ler o ponteiro que diz onde estão os dados. Por isso o ponteiro
  mora no diretório de config do SO e a pasta de dados é separada.
- Distinção clara: diretório de config do SO = casa do `config.json` (ponteiro);
  pasta de dados (escolhida pelo usuário) = casa do `poupy.db` (base).

### Primeira execução (onboarding)

Disparar o fluxo de primeira execução quando `activeDataPath` estiver ausente
(config inexistente, ilegível ou sem a chave). Passos:

1. Exibir uma explicação breve: os dados ficam guardados localmente; o usuário é
   responsável pelo backup (basta copiar a pasta da base).
2. Oferecer um local padrão sensato JÁ PREENCHIDO, sem obrigar o usuário a
   decidir do zero: `Documentos/Poupy` (derivar `Documentos` de
   `QStandardPaths.DocumentsLocation`).
3. Oferecer um botão que abre o seletor NATIVO de pastas
   (`QFileDialog.getExistingDirectory`) para escolher outro local.
4. Ao confirmar: validar permissão de escrita na pasta -> criar/abrir a base
   (`poupy.db`, aplicando migrações) -> gravar `activeDataPath` no `config.json`.

### Troca de base (tela de configurações)

Na tela de configurações (aberta pelo botão de engrenagem ⚙️), a seção
"Armazenamento de dados" deve:

- Mostrar a pasta atual da base e um botão "Abrir no explorador"
  (`QDesktopServices.openUrl(QUrl.fromLocalFile(...))`).
- Oferecer "Usar outra pasta..." que abre o seletor nativo de pastas.
- Ao escolher uma pasta, DETECTAR o conteúdo pela presença de `poupy.db` e
  informar o usuário de forma inequívoca:
  - **Pasta vazia (sem `poupy.db`)**: avisar que uma base nova, do zero, será
    criada ali; deixar claro que a base atual continua salva na pasta antiga.
  - **Pasta com `poupy.db`**: avisar que uma base existente foi encontrada e
    será aberta. Este é o mecanismo oficial de "abrir/replicar base existente".
- Deixar SEMPRE explícito que a troca é NÃO-DESTRUTIVA: a base anterior
  permanece intacta na pasta antiga, e o usuário pode voltar a ela apontando o
  app de volta para aquela pasta.
- Ao confirmar: validar permissão de escrita -> fazer checkpoint e FECHAR a
  conexão SQLite atual -> gravar o novo `activeDataPath` no `config.json` ->
  reiniciar o app (ou, no mínimo, recriar a camada de dados) para trocar a
  conexão com segurança. NÃO fazer troca "a quente" com a UI já carregada sobre
  a conexão antiga.

### Fora de escopo (decisões de design - NÃO implementar)

- SEM função de "migrar/mover dados": trocar de base nunca move nem apaga a base
  antiga.
- SEM botão de exportar/importar backup: backup = o usuário copia a pasta
  manualmente com o app fechado.
- Replicar uma base = copiar a pasta e apontar o app para a cópia via "Usar
  outra pasta...". NÃO criar UI dedicada para isso.

### Invariantes e cuidados técnicos de SQLite/WAL

- **Modo WAL + checkpoint ao fechar**: usar `PRAGMA journal_mode=WAL`. Ao
  encerrar o processo, executar checkpoint (`PRAGMA wal_checkpoint(TRUNCATE)`) e
  fechar a conexão de forma limpa, para que o `poupy.db` fique completo e
  íntegro. Isso torna o modelo "fechar o app + copiar a pasta" um backup
  confiável.
- **Arquivos sidecar do WAL**: `poupy.db-wal` e `poupy.db-shm` existem em
  runtime. A detecção de "base existente" deve olhar SOMENTE o `poupy.db`.
  Qualquer cópia de dados deve ocorrer com o app fechado (ou após checkpoint e
  fechamento da conexão).
- **Validação da pasta escolhida**: verificar permissão de escrita antes de
  gravar o ponteiro; tratar caminhos de forma cross-platform (`pathlib.Path`).
- **Validação da base ao abrir**: confirmar que o `poupy.db` é um banco Poupy
  legível; aplicar as migrações de schema (`PRAGMA user_version`) se um app mais
  novo abrir uma base antiga.
- **Config ausente ou corrompido**: se `config.json` sumir ou estiver ilegível
  (ex.: o usuário levou só o `.exe` para outra máquina), cair naturalmente no
  fluxo de primeira execução.
- **Pasta em nuvem (Google Drive / OneDrive / Dropbox)**: suportada como destino
  de backup, mas o app deve APENAS AVISAR contra abrir a mesma base sincronizada
  em duas máquinas ao mesmo tempo (risco de corrupção do SQLite). Não implementar
  bloqueio nem lock distribuído; apenas o aviso.

### Distribuição (executável único) - implicações

- Alvo de distribuição: um executável único (`Poupy.exe`), sem instalador e sem
  desinstalador. Atualização = substituir o `.exe`; os dados permanecem intactos
  porque vivem em pasta separada (a base) + ponteiro em `%APPDATA%\Poupy`.
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
8. Ser conciso. Manter o README mínimo. IMPORTANTE: nunca usar emojis, exceto o ícone de engrenagem (⚙️) usado para representar as configurações na UI

## Plan

A nova feature a ser implementada é o **armazenamento de dados e base ativa**,
especificado na seção acima. O plano de implementação faseado, com critérios de
sucesso e testes por fase, está em @docs/PLAN.md — seguir esse plano ao implementar.
