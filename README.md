# Poupy

App desktop local-first de gastos pessoais (PySide6 + SQLite).

## Desenvolvimento

```sh
uv run poupy          # roda o app
uv run pytest         # testes
uv run ruff check     # lint
uv run mypy           # tipos (strict)
```

Os dados ficam num unico arquivo SQLite em `QStandardPaths.AppDataLocation`.
