# Quick Message

一个跨平台短信转发应用，支持安卓端自动捕获短信并转发到PC端显示。

## 项目结构

```
quick-otc/
├── pc/                              # PC端
│   ├── pyproject.toml               # Python项目配置 (uv + hatch)
│   └── src/sms_receiver/
│       ├── __init__.py              # 入口文件
│       ├── app.py                   # 主应用逻辑
│       ├── config.py                # 配置管理和消息存储
│       ├── server.py                # WebSocket服务器
│       └── ui.py                    # UI组件
│
└── mobile/                          # 安卓端
    ├── build.gradle.kts             # 根项目配置
    ├── settings.gradle.kts          # 项目设置
    ├── gradle.properties            # Gradle属性
    └── app/
        ├── build.gradle.kts         # App模块配置
        ├── proguard-rules.pro       # 混淆规则
        └── src/main/
            ├── AndroidManifest.xml  # 清单文件
            ├── java/com/smsforwarder/
            │   ├── MainActivity.kt      # 主界面 - 服务器扫描和连接
            │   ├── SmsReceiver.kt       # 短信广播接收器 - 监听系统短信
            │   ├── SmsData.kt           # 数据模型 - JSON序列化
            │   └── WebSocketService.kt  # WebSocket前台服务 - 保持连接和转发
            └── res/                    # 资源文件
                ├── layout/activity_main.xml
                ├── drawable/             # 按钮背景和图标
                ├── values/
                │   ├── strings.xml
                │   ├── themes.xml
                │   └── colors.xml        # 亮色模式颜色
                └── values-night/
                    ├── themes.xml
                    └── colors.xml        # 深色模式颜色
```

## 技术架构

### 通信协议
- **WebSocket**: 双向实时通信，PC端作为服务器，安卓端作为客户端
- **UDP广播**: PC端自动广播端口号，安卓端自动发现
- **动态端口**: PC端随机分配端口，避免冲突
- **重试机制**: 连接失败自动重试，最多3次
- **超时设置**: 10秒超时，自动断开无响应连接

### 数据格式
```json
{
    "sender": "发送者号码",
    "content": "短信内容",
    "timestamp": "2024-01-01 12:00:00"
}
```

### PC端技术栈
- **Python 3.10+**: 运行环境
- **uv + venv**: 包管理和虚拟环境
- **websockets**: WebSocket服务器实现
- **CustomTkinter**: 现代GUI框架，支持深色/浅色主题
- **pystray**: 系统托盘支持
- **Pillow**: 图标绘制

### 安卓端技术栈
- **Kotlin**: 开发语言
- **Android SDK 34**: 目标SDK
- **Java-WebSocket**: WebSocket客户端库
- **Gson**: JSON序列化
- **DatagramSocket**: UDP广播接收
- **Material Design**: 深色/浅色主题支持

## 安装和使用

### PC端

#### 环境要求
- Python 3.10+
- uv 包管理器

#### 安装步骤

```bash
cd pc

# 创建虚拟环境
uv venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 激活虚拟环境 (Linux/macOS)
source .venv/bin/activate

# 安装依赖
uv pip install -e .

# 运行应用
quick-message
```

启动后会显示现代GUI界面，WebSocket服务器随机分配端口并自动广播。

### 安卓端

#### 环境要求
- Android Studio Hedgehog (2023.1.1) 或更高版本
- JDK 17+
- Android SDK 34

#### 安装步骤

1. 用 Android Studio 打开 `mobile` 目录
2. 等待 Gradle 同步完成
3. 连接安卓手机（开启USB调试）或启动模拟器
4. 点击 Run 按钮安装应用
5. 授予应用所需的权限：
   - 短信权限 (RECEIVE_SMS, READ_SMS)
   - 网络权限 (INTERNET, ACCESS_NETWORK_STATE)
   - 通知权限 (POST_NOTIFICATIONS，Android 13+)

### 连接配置

1. **确保设备在同一网络**
   - PC和安卓手机连接到同一个WiFi网络

2. **自动扫描服务器**
   - 打开"Quick Message"应用
   - 点击圆形连接按钮
   - 应用会自动搜索局域网内的PC服务器
   - 找到服务器后会自动连接
   - 状态显示"已连接"表示成功

3. **测试转发**
   - 向安卓手机发送一条短信
   - PC端界面会自动显示短信内容

## 功能特性

### PC端
- [x] WebSocket服务器，随机分配端口
- [x] UDP广播端口号，自动发现
- [x] 现代GUI界面，支持深色/浅色主题
- [x] 实时显示短信（发送者、内容、时间戳）
- [x] 消息计数统计
- [x] 清空消息功能
- [x] 设备连接状态显示
- [x] 弹窗通知（可配置）
- [x] 自动复制到剪贴板（可配置）
- [x] 系统托盘支持（可配置最小化到托盘）
- [x] 短信持久化存储（30天循环）
- [x] 消息卡片悬浮操作（复制/删除）
- [x] 最新消息置顶显示

### 安卓端
- [x] 后台服务持续运行
- [x] 自动监听系统短信
- [x] UDP广播接收，自动发现PC服务器
- [x] WebSocket连接管理
- [x] 前台服务通知
- [x] 消息日志显示
- [x] 连接重试机制（最多3次）
- [x] 主动断开不自动重连
- [x] 深色/浅色主题自适应
- [x] 未连接时丢弃消息（不缓存）

## 设置选项

### PC端设置
| 选项 | 说明 |
|------|------|
| 退出到托盘 | 关闭窗口时最小化到系统托盘而非退出 |
| 启用弹窗通知 | 收到短信时在屏幕右下角弹出通知窗口 |
| 自动复制 | 收到短信时自动复制内容到剪贴板 |
| 保存短信 | 保存短信记录到本地（30天循环） |

## 权限说明

### 安卓端权限

| 权限 | 用途 |
|------|------|
| RECEIVE_SMS | 接收系统短信广播 |
| READ_SMS | 读取短信内容 |
| INTERNET | 网络通信 |
| ACCESS_NETWORK_STATE | 网络状态检测 |
| FOREGROUND_SERVICE | 前台服务运行 |
| POST_NOTIFICATIONS | 显示通知 (Android 13+) |

## 常见问题

### Q: 安卓端无法找到PC服务器？
1. 检查PC和手机是否在同一局域网
2. 检查PC防火墙是否允许UDP端口12345和WebSocket端口
3. 确认PC端应用已启动

### Q: 收到短信但没有转发？
1. 检查安卓端是否已连接服务器（状态显示"已连接"）
2. 确认已授予短信权限
3. 查看安卓端消息日志
4. 注意：未连接时收到的短信会被丢弃，不会缓存

### Q: 连接失败后如何重新连接？
连接失败后按钮会自动恢复为连接状态，点击即可重新扫描

### Q: 如何查看历史短信？
PC端默认开启短信保存功能，重启应用后会自动加载历史消息（保留30天）

## 开发说明

### 修改PC端广播端口
编辑 `pc/src/sms_receiver/server.py`，修改广播端口：
```python
sock.sendto(data, ('255.255.255.255', 12345))
```

### 修改安卓端接收端口
编辑 `mobile/app/src/main/java/com/smsforwarder/MainActivity.kt`，修改接收端口：
```kotlin
val socket = DatagramSocket(12345)
```

### 自定义重试次数
编辑 `mobile/app/src/main/java/com/smsforwarder/WebSocketService.kt`，修改 `MAX_RETRIES` 常量：
```kotlin
private const val MAX_RETRIES = 3
```

### 自定义超时时间
编辑 `mobile/app/src/main/java/com/smsforwarder/WebSocketService.kt`，修改 `connectionLostTimeout`：
```kotlin
webSocketClient?.connectionLostTimeout = 10
```

### 自定义消息保存天数
编辑 `pc/src/sms_receiver/config.py`，修改 `MAX_DAYS` 常量：
```python
class MessageStorage:
    MAX_DAYS = 30
```

## 数据存储

### PC端
- 配置文件: `~/.quick-message/config.json`
- 消息记录: `~/.quick-message/messages.json`

### 配置文件格式
```json
{
    "minimize_to_tray": false,
    "popup_notification": true,
    "auto_copy": false,
    "save_messages": true
}
```

## 许可证

MIT License
