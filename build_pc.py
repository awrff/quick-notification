#!/usr/bin/env python3
"""PC端打包脚本 - 使用PyInstaller打包成可执行文件"""

import os
import sys
import shutil
import subprocess
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

    spec_file = pc_dir / "QuickMessage.spec"
    if spec_file.exists():
        spec_file.unlink()
        print(f"已清理: {spec_file}")


def build_pc():
    """打包PC端"""
    pc_dir = get_project_root() / "pc"

    print("=" * 50)
    print("PC端打包脚本")
    print("=" * 50)

    os.chdir(pc_dir)

    print("\n[1/4] 清理旧的构建文件...")
    clean_build_files(pc_dir)

    print("\n[2/4] 检查并安装PyInstaller...")
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

    print("\n[3/4] 开始打包...")
    entry_point = pc_dir / "src" / "sms_receiver" / "__init__.py"

    cmd = [
        str(venv_python), "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "QuickMessage",
        "--distpath", str(pc_dir / "dist"),
        "--workpath", str(pc_dir / "build"),
        "--specpath", str(pc_dir),
        str(entry_point)
    ]

    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("打包失败!")
        return False

    print("\n[4/4] 打包完成!")
    output_file = pc_dir / "dist" / "QuickMessage.exe"
    if output_file.exists():
        file_size = output_file.stat().st_size / (1024 * 1024)
        print(f"输出文件: {output_file}")
        print(f"文件大小: {file_size:.2f} MB")
        return True
    else:
        print("错误: 未找到输出文件")
        return False


if __name__ == "__main__":
    success = build_pc()
    sys.exit(0 if success else 1)
