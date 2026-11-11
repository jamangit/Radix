# -*- mode: python ; coding: utf-8 -*-
import os

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Packages that load data files, native libraries or submodules dynamically: PyInstaller cannot
# see all of that by reading the imports, so they are collected whole.
COLLECTED = [
    "faster_whisper",
    "ctranslate2",
    "onnxruntime",
    "tokenizers",
    "huggingface_hub",
    "av",
    "pysilero_vad",
    "wordfreq",
    "simplemma",
    "stopwordsiso",
    "lingua",
    "argon2",
    "_argon2_cffi_bindings",
    "websockets",
    "httptools",
]

datas = [(os.path.join(SPECPATH, "..", "web", "out"), "web")]
binaries = []
hiddenimports = collect_submodules("uvicorn") + collect_submodules("wordmeter_api")

for package in COLLECTED:
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

a = Analysis(
    ["desktop_entry.py"],
    pathex=[os.path.join(SPECPATH, "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "ruff", "mypy"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="wordmeter-engine", console=True)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="wordmeter-engine")