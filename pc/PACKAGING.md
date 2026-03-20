# Quick Notification PC端打包说明

## 环境准备

### 1. 安装依赖

```powershell
cd pc
uv venv
.venv\Scripts\activate
uv pip install -e .
```

### 2. 安装 Inno Setup（用于生成安装程序）

从官网下载并安装：https://jrsoftware.org/isdl.php

安装时选择 "Install for all users" 或默认选项即可。

## 打包方式

### 方式一：一键打包（推荐）

在 pc 目录下运行：

```powershell
cd pc
python build_pc.py
```

这将自动完成：
1. 清理旧的构建文件
2. 使用 PyInstaller 打包 exe
3. 使用 Inno Setup 生成安装程序

生成的文件：
- `pc/dist/QuickNotification.exe` - 可执行文件
- `installer/QuickNotificationSetup.exe` - 安装程序

### 方式二：只打包 exe（不生成安装程序）

```powershell
cd pc
python build_pc.py --skip-installer
```

### 方式三：手动打包

```powershell
cd pc

# 打包 exe
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm QuickNotification.spec

# 生成安装程序（需要安装 Inno Setup）
"C:\Program Files\Inno Setup 6\ISCC.exe" installer.iss
```

## 配置文件清理

安装程序已配置为在卸载时自动清理用户配置文件：

- 清理目录：`%USERPROFILE%\.quick-notification`
- 清理文件：`config.json`、`messages.json`

这是通过 Inno Setup 脚本中的以下配置实现的：

```iss
[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\.quick-notification"

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    // 删除用户配置目录
    DelTree(ExpandConstant('{userappdata}\.quick-notification'), True, True, True);
  end;
end;
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `pc/build_pc.py` | 主打包脚本 |
| `pc/QuickNotification.spec` | PyInstaller 配置文件 |
| `pc/installer.iss` | Inno Setup 安装脚本 |

## 自定义配置

### 修改应用版本

编辑以下文件中的版本号：
- `pc/pyproject.toml` - `version = "0.1.0"`
- `pc/installer.iss` - `AppVersion=0.1.0`

### 修改安装目录

编辑 `pc/installer.iss`：
```iss
DefaultDirName={autopf}\Quick Notification
```

### 添加开始菜单项

编辑 `pc/installer.iss` 的 `[Icons]` 部分。

## 常见问题

### Q: 打包后运行报错找不到模块？

确保 `QuickNotification.spec` 中的 `hiddenimports` 包含所有需要的模块。

### Q: 安装程序中文乱码？

Inno Setup 脚本已配置中文支持：
```iss
[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
```

### Q: 卸载后配置文件还在？

检查配置文件是否存储在其他位置。当前配置存储在：
- `Path.home() / ".quick-notification"` (即 `C:\Users\用户名\.quick-notification`)
