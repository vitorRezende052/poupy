# -*- mode: python ; coding: utf-8 -*-
"""Receita de empacotamento do Poupy (PyInstaller, modo onefile).

Gera um unico executavel (no Windows, dist/Poupy.exe), sem instalador. O
sqlite3 e da biblioteca padrao do Python e ja e embutido pelo PyInstaller;
nao ha modulo nativo extra para reempacotar.

O PyInstaller nao faz cross-compile: o executavel gerado e sempre o da
plataforma onde o comando roda. Rode com:

    uv run pyinstaller poupy.spec --noconfirm

A saida fica em dist/ (no Windows, dist/Poupy.exe).
"""

from pathlib import Path

raiz = Path(SPECPATH)  # noqa: F821 -- injetado pelo PyInstaller
pacote = raiz / "src" / "poupy"

a = Analysis(  # noqa: F821
    [str(pacote / "__main__.py")],
    pathex=[str(raiz / "src")],
    datas=[(str(pacote / "ui" / "style.qss"), "poupy/ui")],
)

pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Poupy",
    console=False,
)
