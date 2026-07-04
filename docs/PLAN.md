# Plano de implementação: base ativa

Plano faseado para implementar a seção "Armazenamento de dados e base ativa" do
`CLAUDE.md`. Cada fase tem critérios de sucesso a marcar antes de seguir (ver
"Estratégia" no `CLAUDE.md`). As fases são incrementais e independentes o
suficiente para revisão isolada.

Estado atual a substituir: `db/connection.py:caminho_banco()` usa
`AppDataLocation` direto; `__main__.py` abre a conexão fixa; não há WAL nem
checkpoint; não há config, onboarding nem tela de configurações.

## Fase 1 - Camada de configuração (ponteiro)

Criar `poupy/config.py` com a leitura/escrita do `config.json` no diretório de
config do SO.

INVARIANTE: o ponteiro fica no diretório de config do SO, FORA da pasta de dados
(senão vira paradoxo ovo-e-galinha - o app não teria como descobrir onde estão os
dados). Caminhos por plataforma: Windows `%APPDATA%\Poupy\config.json`; Linux
`~/.config/poupy/config.json`; macOS `~/Library/Application Support/Poupy/config.json`.

- [ ] `caminho_config() -> Path` usa `QStandardPaths.AppConfigLocation`, cria o
      diretório e retorna `<dir>/config.json`.
- [ ] `ler_config() -> Config | None` retorna a dataclass com `active_data_path`
      ou `None` quando o arquivo falta, é ilegível ou não tem a chave.
- [ ] `gravar_config(active_data_path: Path) -> None` grava
      `{ "activeDataPath": "<abs>" }` (JSON, caminho absoluto).
- [ ] Config ausente/corrompido nunca lança para o chamador: retorna `None`.
- Testes: round-trip grava/le; arquivo inexistente -> `None`; JSON invalido ->
  `None`; chave ausente -> `None`.

## Fase 2 - Resolução da base + WAL + checkpoint no encerramento

Mover a responsabilidade de "onde fica o `poupy.db`" para a base ativa e
garantir shutdown limpo.

- [ ] `db/connection.py`: `abrir_conexao` passa a receber a pasta da base e
      abrir `<base>/poupy.db`; remover a dependência de `AppDataLocation` em
      `caminho_banco()` (ou substituir por `caminho_banco(base: Path)`).
- [ ] Habilitar `PRAGMA journal_mode=WAL` ao abrir.
- [ ] Adicionar `fechar_conexao(conn)` que executa
      `PRAGMA wal_checkpoint(TRUNCATE)` e `conn.close()`.
- [ ] `__main__.py` usa `fechar_conexao` no encerramento (substitui `conn.close()`).
- [ ] `base_existe(pasta) -> bool` checa SOMENTE a presença de `poupy.db`
      (ignora `-wal`/`-shm`).
- [ ] `validar_escrita(pasta) -> bool` verifica permissão de escrita de forma
      cross-platform (`pathlib`).
- [ ] Validar a base ao abrir: confirmar que o `poupy.db` é um banco Poupy
      legível e aplicar as migrações (`PRAGMA user_version`) quando um app mais
      novo abrir uma base antiga.
- Testes: WAL ativo apos abrir; checkpoint deixa `-wal` vazio/removido; migracoes
  aplicadas ao abrir base do zero E ao abrir base antiga; `base_existe` ignora
  sidecars; `validar_escrita` distingue pasta gravavel de somente-leitura.

## Fase 3 - Onboarding (primeira execução)

Bootstrap que decide entre onboarding e abrir a base antes de montar a janela.

- [ ] `__main__.py`: se `ler_config()` retornar `None`, abrir o `QDialog` de
      onboarding antes da `MainWindow`.
- [ ] Diálogo explica dados locais + responsabilidade de backup; campo de pasta
      pré-preenchido com `DocumentsLocation/Poupy`; botão que abre
      `QFileDialog.getExistingDirectory`.
- [ ] Confirmar: `validar_escrita` -> criar/abrir base (aplica migrações) ->
      `gravar_config`. Só então segue para a `MainWindow`.
- [ ] Cancelar o onboarding encerra o app sem gravar config.
- [ ] `ler_config() == None` cobre config ausente OU corrompido: ambos caem
      naturalmente no onboarding (ex.: usuário levou só o `.exe` para outra
      máquina, sem o `config.json`).
- Testes (pytest-qt): sem config dispara o diálogo; config corrompido dispara o
  diálogo; confirmar grava config e cria `poupy.db`; pasta sem permissão bloqueia
  a confirmação com aviso.

## Fase 4 - Tela de configurações e troca de base

Botão de engrenagem ⚙️ na `MainWindow` abre um `QDialog` de configurações.

- [ ] Seção "Armazenamento de dados": mostra a pasta atual + "Abrir no
      explorador" (`QDesktopServices.openUrl(QUrl.fromLocalFile(...))`).
- [ ] "Usar outra pasta..." abre o seletor nativo e detecta o conteúdo:
      pasta vazia -> avisa que cria base nova do zero; pasta com `poupy.db` ->
      avisa que abre a base existente. Sempre deixar explícito que é NÃO-DESTRUTIVO.
- [ ] Confirmar: `validar_escrita` -> `fechar_conexao` (checkpoint) da base atual
      -> `gravar_config` novo caminho -> reiniciar o app (ou recriar a camada de
      dados). NÃO trocar a conexão "a quente" com a UI carregada.
- [ ] Aviso ao apontar para pasta de nuvem: alertar contra abrir a mesma base em
      duas máquinas ao mesmo tempo (app apenas avisa, sem bloquear).
- Testes (pytest-qt): detecção vazia vs. com base mostra a mensagem correta;
  confirmar grava novo config e não altera a base antiga (não-destrutivo).

## Fase 5 - Distribuição single-exe e README

- [ ] Publicar como executável único (`Poupy.exe`), sem instalador e sem
      desinstalador. Atualização = substituir o `.exe`; os dados permanecem
      intactos porque vivem em pasta separada (a base) + ponteiro em `%APPDATA%`.
- [ ] Decidir `onefile` vs. `onedir` no `poupy.spec` e alinhar README à decisão
      (ver a tensão registrada na spec). `sqlite3` da stdlib já é embutido pelo
      PyInstaller; sem módulo nativo extra.
- [ ] README reflete a spec: base/local dos dados, backup (fechar + copiar
      pasta), troca de base pela engrenagem (não-destrutivo), uso em outro
      computador, atualização (substituir `.exe`), aviso do SmartScreen.
      (Já ajustado; reconferir após as fases anteriores.)

## Fora de escopo (NÃO implementar)

- SEM função de "migrar/mover dados": trocar de base nunca move nem apaga a base
  antiga.
- SEM botão de exportar/importar backup: backup = o usuário copia a pasta
  manualmente com o app fechado.
- Replicar uma base = copiar a pasta e apontar o app para a cópia via "Usar
  outra pasta...". NÃO criar UI dedicada para isso.

## Critério de conclusão global

Feature concluída quando: `uv run pytest`, `uv run ruff check` e `uv run mypy`
passam; o app roda do zero disparando onboarding; a troca de base pela engrenagem
funciona e é não-destrutiva; e os dados persistem após reiniciar o app apontando
para a mesma base.
