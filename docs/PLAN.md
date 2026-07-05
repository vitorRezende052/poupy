# Plano de implementação: base como arquivo `.db`

Plano faseado para evoluir a seção "Armazenamento de dados e base ativa" do
`CLAUDE.md`. A base ativa (versão pasta) já está implementada; esta feature muda
o modelo para **base = um arquivo `.db`** e permite que o usuário **abra um
arquivo `.db` existente** pelo onboarding (além de criar um novo), com
**validação robusta ao abrir** (identidade antes de migrar).

Cada fase tem critérios de sucesso a marcar antes de seguir (ver "Estratégia" no
`CLAUDE.md`). As fases são incrementais e independentes o suficiente para revisão
isolada.

Estado atual a substituir: a base é uma PASTA e o `poupy.db` é um nome fixo
dentro dela (`connection.py:caminho_banco(base) = base / "poupy.db"`); o
`config.json` guarda a pasta; o onboarding usa `QFileDialog.getExistingDirectory`
e só cria base; `abrir_conexao` migra ANTES de validar o schema; não há
`application_id` nem `integrity_check`. (Não há tela de configurações e, por
decisão de design, não haverá — ver "Fora de escopo".)

## Fase 1 - Base = arquivo `.db` (mudança de modelo)

Mover o conceito de base de "pasta que contém `poupy.db`" para "o próprio arquivo
`.db`, com nome livre e em qualquer pasta". Os sidecars do WAL (`-wal`/`-shm`)
são gerados pelo SQLite ao lado do arquivo escolhido.

- [ ] `config.py`: `active_data_path` passa a ser o caminho do ARQUIVO `.db`
      (não da pasta). Ajustar docstrings; `gravar_config`/`ler_config` continuam
      iguais (só muda o que o caminho aponta, absoluto via `resolve()`).
- [ ] `db/connection.py`: remover `caminho_banco(base)`; `abrir_conexao` passa a
      receber o caminho do arquivo `.db` e abri-lo diretamente.
- [ ] `base_existe(db_path) -> bool` checa a existência do ARQUIVO `.db`
      (ignora os sidecars `-wal`/`-shm`).
- [ ] `validar_escrita(db_path) -> bool` verifica permissão de escrita na PASTA
      que contém o `.db` (`db_path.parent`) — é lá que o WAL será criado —,
      criando a pasta se necessário, cross-platform (`pathlib`).
- [ ] `__main__.py` e `onboarding.py` passam a tratar `active_data_path`/`base`
      como caminho de arquivo `.db`.
- Testes: `config` faz round-trip de um caminho de arquivo; `base_existe`
  distingue arquivo presente de ausente e ignora sidecars; `validar_escrita`
  distingue pasta gravável de somente-leitura a partir do caminho do arquivo.

## Fase 2 - `application_id` + validação em camadas (identidade antes de migrar)

Endurecer a abertura para aceitar com segurança um `.db` trazido pelo usuário e
rejeitar arquivos que não são bancos Poupy, SEM sujá-los.

- [ ] Definir a constante `POUPY_APPLICATION_ID` (inteiro de 32 bits fixo) e
      gravá-la (`PRAGMA application_id`) na CRIAÇÃO de uma base nova.
- [ ] `abrir_conexao(db_path)` distingue dois casos, ambos habilitando WAL:
      - **Base nova** (arquivo recém-criado/vazio: `application_id == 0` e sem
        tabelas de usuário): gravar `application_id` do Poupy e aplicar migrações.
      - **Base existente**: rodar as camadas de validação abaixo, depois migrar.
- [ ] Camadas de validação de uma base existente, NESTA ORDEM (identidade ANTES
      de migrar):
      1. `PRAGMA integrity_check` - é um SQLite íntegro? Senão, recusar.
      2. `PRAGMA application_id` == `POUPY_APPLICATION_ID` - é um banco Poupy?
         Senão, recusar (arquivo de outro programa).
      3. `PRAGMA user_version` <= última migração conhecida - não é de versão
         futura? Se for maior, recusar (base de app mais novo); NUNCA rebaixar.
      4. Só então `aplicar_migracoes` (leva bases antigas para frente).
      5. `_validar_schema` como rede final (tabelas `categoria`/`gasto`).
- [ ] INVARIANTE de código: nenhuma escrita/migração ocorre antes de a identidade
      (passos 1-3) passar. Um `.db` alheio é recusado sem ganhar tabelas do Poupy.
- [ ] Erros distinguíveis pelo chamador (ex.: subclasses/mensagens diferentes)
      para: não é SQLite, não é Poupy, versão futura.
- Testes: base nova cria e grava `application_id`; base antiga (schema v0) migra
  ao abrir; base de versão futura é recusada; arquivo corrompido é recusado;
  `.db` de outro programa (com tabelas) é recusado E permanece intacto (sem
  tabelas do Poupy adicionadas); reabrir base Poupy válida não re-grava nem
  duplica dados.

## Fase 3 - Onboarding: criar OU abrir `.db` existente

O onboarding continua sendo o ÚNICO ponto de escolha de base. Ganha um segundo
caminho: abrir um arquivo `.db` já existente.

- [ ] Manter o fluxo de CRIAR base inalterado: campo pré-preenchido com
      `Documentos/Poupy` (via `DocumentsLocation`) + `getExistingDirectory`;
      cria `poupy.db` dentro da pasta escolhida.
- [ ] Adicionar botão "Abrir arquivo .db existente..." que abre
      `QFileDialog.getOpenFileName` (filtro `*.db`) e aponta direto para um
      arquivo `.db` já existente (qualquer nome/pasta).
- [ ] Confirmar CRIAR: `validar_escrita` -> `abrir_conexao(<pasta>/poupy.db)`
      (cria e grava `application_id`) -> `gravar_config(<arquivo>)`.
- [ ] Confirmar ABRIR: `abrir_conexao(<arquivo escolhido>)` (valida em camadas) ->
      `gravar_config(<arquivo>)`. Só então segue para a `MainWindow`.
- [ ] Mensagens de aviso específicas ao abrir: "não é um banco válido", "não é um
      banco do Poupy", "base criada por uma versão mais nova do Poupy".
- [ ] Cancelar o onboarding encerra o app sem gravar config.
- [ ] Boot (`__main__.py`): `active_data_path` é um arquivo; `base_existe`
      confere o arquivo; se sumiu (apagado, HD externo/nuvem indisponível),
      cair no onboarding SEM recriar base silenciosamente.
- Testes (pytest-qt): sem config dispara o diálogo; config apontando para `.db`
  inexistente dispara o diálogo (sem recriar); criar grava config e cria o `.db`
  com `application_id`; abrir um `.db` Poupy válido grava config e abre; abrir um
  `.db` de outro programa mostra "não é Poupy" e NÃO altera o arquivo; abrir um
  `.db` de versão futura mostra o aviso e bloqueia.

## Fase 4 - Docs e README

- [ ] README reflete o modelo de arquivo: a base é um arquivo `.db`; backup =
      fechar o app e copiar o arquivo; trocar de base pelo onboarding (criar novo
      OU abrir um `.db` existente); usar um `.db` de outra máquina/cópia/backup;
      atualização (substituir `.exe`); aviso do SmartScreen.
- [ ] Reconferir o `CLAUDE.md` após as fases (definição de base, onboarding com
      as duas opções, validação em camadas) e alinhar qualquer menção residual a
      "pasta da base".

## Fora de escopo (NÃO implementar)

- SEM tela de configurações / botão de engrenagem: o onboarding é o único ponto
  de escolha de base (criar OU abrir arquivo).
- SEM troca de base "a quente" com a UI carregada: para trocar, fecha-se o app e
  reabre-se, caindo no onboarding.
- SEM função de "migrar/mover dados": abrir um `.db` existente APONTA o ponteiro
  para ele - não copia nem importa nada; a base antiga fica intacta.
- SEM botão de exportar/importar backup: backup = o usuário copia o arquivo `.db`
  com o app fechado.

## Critério de conclusão global

Feature concluída quando: `pytest`, `ruff check` e `mypy` passam; o app roda do
zero disparando onboarding; CRIAR uma base nova funciona; ABRIR um `.db` Poupy
existente funciona; abrir um `.db` de outro programa é recusado SEM sujar o
arquivo; abrir um `.db` de versão futura é recusado; apagar/mover o `.db` (ou o
`config.json`) e reabrir dispara o onboarding de novo sem recriar base
silenciosamente; e os dados persistem após reiniciar o app apontando para o mesmo
arquivo `.db`.
