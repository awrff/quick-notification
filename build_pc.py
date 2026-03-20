#!/usr/bin/env python3
"""PC端打包脚本 - 使用PyInstaller打包成可执行文件，并生成安装程序"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


def get_project_root():
    return Path(__file__).parent.resolve()


def clean_build_files(pc_dir: Path):
    """清理构建文件"""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        dir_path = pc_dir / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"已清理: {dir_path}")


def find_inno_setup():
    """查找 Inno Setup Compiler"""
    possible_paths = [
        Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return shutil.which("ISCC")


def generate_spec_file(pc_dir: Path, project_root: Path) -> Path:
    """动态生成 spec 文件"""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project_root = Path(r"{project_root}")
assets_path = project_root / "assets"
src_path = Path(r"{pc_dir}") / "src"

a = Analysis(
    [str(src_path / "sms_receiver" / "main.py")],
    pathex=[str(src_path)],
    binaries=[],
    datas=[
        (str(assets_path), "assets"),
    ],
    hiddenimports=[
        "customtkinter",
        "websockets",
        "PIL",
        "pystray",
        "six.moves.tkinter",
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="QuickNotification",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(assets_path / "quick-notification.ico"),
)
'''
    spec_file = pc_dir / "QuickNotification.spec"
    with open(spec_file, "w", encoding="utf-8") as f:
        f.write(spec_content)
    return spec_file


def build_exe(pc_dir: Path, project_root: Path) -> bool:
    """使用 PyInstaller 打包 exe"""
    print("\n[1/3] 开始打包 EXE...")
    
    os.chdir(pc_dir)

    venv_python = pc_dir / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        print("错误: 虚拟环境不存在，请先运行以下命令创建虚拟环境:")
        print("  cd pc")
        print("  uv venv")
        print("  .venv\\Scripts\\activate")
        print("  uv pip install -e .")
        return False

    result = subprocess.run(
        [str(venv_python), "-c", "import PyInstaller"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("正在安装PyInstaller...")
        env = os.environ.copy()
        env["UV_HTTP_TIMEOUT"] = "120"
        subprocess.run(["uv", "pip", "install", "pyinstaller"], cwd=str(pc_dir), check=True, env=env)
    else:
        print("PyInstaller已安装")

    spec_file = generate_spec_file(pc_dir, project_root)
    print(f"生成 spec 文件: {spec_file}")

    cmd = [
        str(venv_python), "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]

    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("打包失败!")
        return False

    output_file = pc_dir / "dist" / "QuickNotification.exe"
    if output_file.exists():
        file_size = output_file.stat().st_size / (1024 * 1024)
        print(f"输出文件: {output_file}")
        print(f"文件大小: {file_size:.2f} MB")
        return True
    else:
        print("错误: 未找到输出文件")
        return False


def build_installer(pc_dir: Path, project_root: Path) -> bool:
    """使用 Inno Setup 生成安装程序"""
    print("\n[2/3] 开始生成安装程序...")

    iss_file = pc_dir / "installer.iss"
    if not iss_file.exists():
        print("错误: 未找到 installer.iss 文件")
        return False

    iscc_path = find_inno_setup()
    if not iscc_path:
        print("错误: 未找到 Inno Setup Compiler")
        print("请从以下地址下载并安装 Inno Setup:")
        print("  https://jrsoftware.org/isdl.php")
        return False

    print(f"使用 Inno Setup: {iscc_path}")

    cmd = [str(iscc_path), str(iss_file)]
    print(f"执行命令: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=str(pc_dir))

    if result.returncode != 0:
        print("生成安装程序失败!")
        return False

    output_dir = project_root / "installer_output"
    if output_dir.exists():
        installers = list(output_dir.glob("QuickNotificationSetup*.exe"))
        if installers:
            installer = installers[0]
            file_size = installer.stat().st_size / (1024 * 1024)
            print(f"\n安装程序: {installer}")
            print(f"文件大小: {file_size:.2f} MB")
            return True

    print("错误: 未找到安装程序输出文件")
    return False


def build_pc(skip_installer: bool = False):
    """打包PC端"""
    pc_dir = get_project_root() / "pc"
    project_root = get_project_root()

    print("=" * 50)
    print("PC端打包脚本")
    print("=" * 50)

    os.chdir(pc_dir)

    print("\n[0/3] 清理旧的构建文件...")
    clean_build_files(pc_dir)

    if not build_exe(pc_dir, project_root):
        return False

    if skip_installer:
        print("\n[2/3] 跳过安装程序生成")
        print("\n[3/3] 打包完成!")
        return True

    if not build_installer(pc_dir, project_root):
        return False

    print("\n[3/3] 打包完成!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PC端打包脚本")
    parser.add_argument("--skip-installer", action="store_true", help="只打包exe，不生成安装程序")
    args = parser.parse_args()
    
    success = build_pc(skip_installer=args.skip_installer)
    sys.exit(0 if success else 1)
