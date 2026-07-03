# Empacotamento (Windows)

O executavel e gerado com PyInstaller a partir de `poupy.spec`.

**Importante:** o PyInstaller nao faz cross-compile. O executavel e sempre
o da plataforma onde o comando roda. Para gerar o `.exe`, rode em um
Windows (a receita `poupy.spec` e a mesma nas tres plataformas).

## Pre-requisitos no Windows

Instalar o `uv` (PowerShell):

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

## Gerar o executavel

Na pasta do projeto:

```powershell
uv sync
uv run pyinstaller poupy.spec --noconfirm
```

O resultado (modo onedir) fica em `dist\Poupy\`, com `dist\Poupy\Poupy.exe`
e a pasta `_internal` ao lado. Para distribuir, compacte a pasta
`dist\Poupy` inteira (o `.exe` sozinho nao roda sem o `_internal`).

## Notas

- O banco de dados fica em `%APPDATA%\Poupy\Poupy\poupy.db` (criado no
  primeiro uso); atualizacoes do app preservam os dados.
- Para um unico arquivo `.exe` (mais comodo, porem inicia mais devagar),
  remova o bloco `COLLECT` de `poupy.spec` e passe `a.binaries` e
  `a.datas` direto no `EXE`. O modo onedir e o recomendado para apps Qt.
