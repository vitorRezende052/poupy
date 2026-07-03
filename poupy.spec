# -*- mode: python ; coding: utf-8 -*-
"""Receita de empacotamento do Poupy (PyInstaller, modo onedir).

Funciona em Windows, Linux e macOS: o PyInstaller gera o executavel da
plataforma onde e executado (nao ha cross-compile). Rode com:

    uv run pyinstaller poupy.spec --noconfirm

A saida fica em dist/Poupy/ (no Windows, dist/Poupy/Poupy.exe).
"""

from pathlib import Path

raiz = Path(SPECPATH)  # noqa: F821 -- injetado pelo PyInstaller
pacote = raiz / "src" / "poupy"

a = Analysis(
    [str(pacote / "__main__.py")],
    pathex=[str(raiz / "src")],
    datas=[(str(pacote / "ui" / "style.qss"), "poupy/ui")],
)

pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Poupy",
    console=False,
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    name="Poupy",
)
