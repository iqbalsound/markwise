# Build with:  pyinstaller packaging/markwise.spec --noconfirm
import os

from PyInstaller.utils.hooks import collect_submodules, copy_metadata

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
SRC = os.path.join(ROOT, "src")

hidden = collect_submodules("keyring") + collect_submodules("google.genai")
datas = [(os.path.join(SRC, "markwise", "assets"), os.path.join("markwise", "assets"))]
datas += copy_metadata("keyring")

a = Analysis(
    [os.path.join(ROOT, "packaging", "launcher.py")],
    pathex=[SRC],
    datas=datas,
    hiddenimports=hidden,
    excludes=["tkinter"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="MarkWise", console=False)
coll = COLLECT(exe, a.binaries, a.datas, name="MarkWise")
