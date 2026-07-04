# Plano de implementação: base ativa

Plano faseado para implementar a seção "Armazenamento de dados e base ativa" do
`CLAUDE.md`. Cada fase tem critérios de sucesso a marcar antes de seguir (ver
"Estratégia" no `CLAUDE.md`). As fases são incrementais e independentes o
suficiente para revisão isolada.

Estado atual a substituir: `db/connection.py:caminho_banco()` usa
`AppDataLocation` direto; `__main__.py` abre a conexão fixa; não há WAL nem
checkpoint; não há config nem onboarding. (Não há tela de configurações e, por
decisão de design, não haverá — ver "Fora de escopo".)

## Fase 1 - Camada de configuração (ponteiro)

Criar `poupy/config.py` com a leitura/escrita do `config.json` no diretório de
config do SO.

INVARIANTE: o ponteiro fica no diretório de config do SO, FORA da pasta de dados
(senão vira paradoxo ovo-e-galinha - o app não teria como descobrir onde estão os
dados). Caminhos por plataforma: Windows `%APPDATA%\Poupy\config.json`; Linux
`~/.config/poupy/config.json`; macOS `~/Library/Application Support/Poupy/config.json`.

- [x] `caminho_config() -> Path` usa `QStandardPaths.AppConfigLocation`, cria o
      diretório e retorna `<dir>/config.json`.
- [x] `ler_config() -> Config | None` retorna a dataclass com `active_data_path`
      ou `None` quando o arquivo falta, é ilegível ou não tem a chave.
- [x] `gravar_config(active_data_path: Path) -> None` grava
      `{ "activeDataPath": "<abs>" }` (JSON, caminho absoluto).
- [x] Config ausente/corrompido nunca lança para o chamador: retorna `None`.
- Testes: round-trip grava/le; arquivo inexistente -> `None`; JSON invalido ->
  `None`; chave ausente -> `None`.

## Fase 2 - Resolução da base + WAL + checkpoint no encerramento

Mover a responsabilidade de "onde fica o `poupy.db`" para a base ativa e
garantir shutdown limpo.

- [x] `db/connection.py`: `abrir_conexao` passa a receber a pasta da base e
      abrir `<base>/poupy.db`; remover a dependência de `AppDataLocation` em
      `caminho_banco()` (ou substituir por `caminho_banco(base: Path)`).
- [x] Habilitar `PRAGMA journal_mode=WAL` ao abrir.
- [x] Adicionar `fechar_conexao(conn)` que executa
      `PRAGMA wal_checkpoint(TRUNCATE)` e `conn.close()`.
- [x] `__main__.py` usa `fechar_conexao` no encerramento (substitui `conn.close()`).
- [x] `base_existe(pasta) -> bool` checa SOMENTE a presença de `poupy.db`
      (ignora `-wal`/`-shm`).
- [x] `validar_escrita(pasta) -> bool` verifica permissão de escrita de forma
      cross-platform (`pathlib`).
- [x] Validar a base ao abrir: confirmar que o `poupy.db` é um banco Poupy
      legível e aplicar as migrações (`PRAGMA user_version`) quando um app mais
      novo abrir uma base antiga.
- Testes: WAL ativo apos abrir; checkpoint deixa `-wal` vazio/removido; migracoes
  aplicadas ao abrir base do zero E ao abrir base antiga; `base_existe` ignora
  sidecars; `validar_escrita` distingue pasta gravavel de somente-leitura.

## Fase 3 - Onboarding (primeira execução)

Bootstrap que decide entre onboarding e abrir a base antes de montar a janela.

- [x] `__main__.py`: abrir o `QDialog` de onboarding antes da `MainWindow`
      quando não há base ativa utilizável — `ler_config()` retorna `None` OU o
      `poupy.db` apontado não existe mais. NUNCA recriar silenciosamente um
      `poupy.db` vazio: sempre re-perguntar via onboarding.
- [x] Diálogo explica dados locais + responsabilidade de backup; campo de pasta
      pré-preenchido com `DocumentsLocation/Poupy`; botão que abre
      `QFileDialog.getExistingDirectory`.
- [x] Confirmar: `validar_escrita` -> criar/abrir base (aplica migrações) ->
      `gravar_config`. Só então segue para a `MainWindow`.
- [x] Cancelar o onboarding encerra o app sem gravar config.
- [x] Onboarding cobre: config ausente OU corrompido (`ler_config() == None`,
      ex.: usuário levou só o `.exe` para outra máquina, sem o `config.json`) E
      config válido cujo `poupy.db` sumiu (pasta apagada, HD externo/nuvem
      indisponível) — sem recriar base silenciosamente.
- Testes (pytest-qt): sem config dispara o diálogo; config corrompido dispara o
  diálogo; config válido com `poupy.db` inexistente dispara o diálogo (sem
  recriar base); confirmar grava config e cria `poupy.db`; pasta sem permissão
  bloqueia a confirmação com aviso.

## Fase 4 - Distribuição single-exe e README

- [x] Publicar como executável único (`Poupy.exe`), sem instalador e sem
      desinstalador. Atualização = substituir o `.exe`; os dados permanecem
      intactos porque vivem em pasta separada (a base) + ponteiro em `%APPDATA%`.
- [x] Decidir `onefile` vs. `onedir` no `poupy.spec` e alinhar README à decisão
      (ver a tensão registrada na spec). `sqlite3` da stdlib já é embutido pelo
      PyInstaller; sem módulo nativo extra.
- [x] README reflete a spec: base/local dos dados, backup (fechar + copiar
      pasta), trocar de pasta de forma manual e não-destrutiva pelo onboarding
      (fechar app -> mover/apagar `poupy.db` ou `config.json` -> reabrir), uso em
      outro computador, atualização (substituir `.exe`), aviso do SmartScreen.
      (Reconferir após as fases anteriores.)

## Fora de escopo (NÃO implementar)

- SEM tela de configurações / botão de engrenagem para troca de base: o
  onboarding é o único ponto de escolha de pasta.
- SEM função de "migrar/mover dados": trocar de base nunca move nem apaga a base
  antiga.
- SEM botão de exportar/importar backup: backup = o usuário copia a pasta
  manualmente com o app fechado.
- Replicar uma base = copiar a pasta com o app fechado e apontar o app para a
  cópia pelo onboarding (apagando o `config.json` ou o `poupy.db` atual). NÃO
  criar UI dedicada para isso.

## Critério de conclusão global

Feature concluída quando: `uv run pytest`, `uv run ruff check` e `uv run mypy`
passam; o app roda do zero disparando onboarding; apagar/mover o `poupy.db` (ou
o `config.json`) e reabrir dispara o onboarding de novo sem recriar base
silenciosamente; e os dados persistem após reiniciar o app apontando para a
mesma base.
