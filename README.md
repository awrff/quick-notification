# SMS Forwarder - 短信转发器

一个跨平台短信转发应用，支持安卓端自动捕获短信并转发到PC端显示。

## 项目结构

```
quick-otc/
├── pc/                              # PC端
│   ├── pyproject.toml               # Python项目配置 (uv + hatch)
│   └── src/sms_receiver/
│       └── __init__.py              # WebSocket服务器 + TUI界面
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
            │   ├── MainActivity.kt      # 主界面 - 服务器配置和连接
            │   ├── SmsReceiver.kt       # 短信广播接收器 - 监听系统短信
            │   ├── SmsData.kt           # 数据模型 - JSON序列化
            │   └── WebSocketService.kt  # WebSocket前台服务 - 保持连接和转发
            └── res/                    # 资源文件
                ├── layout/activity_main.xml
                ├── values/strings.xml
                └── values/themes.xml
```

## 技术架构

### 通信协议
- **WebSocket**: 双向实时通信，PC端作为服务器，安卓端作为客户端

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
- **Textual**: 终端用户界面(TUI)框架

### 安卓端技术栈
- **Kotlin**: 开发语言
- **Android SDK 34**: 目标SDK
- **Java-WebSocket**: WebSocket客户端库
- **Gson**: JSON序列化

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

# 运行服务
sms-receiver
```

启动后会在终端显示TUI界面，WebSocket服务器监听 `ws://0.0.0.0:8765`

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
   - 通知权限 (POST_NOTIFICATIONS，Android 13+)

### 连接配置

1. **获取PC的IP地址**
   ```bash
   # Windows
   ipconfig

   # Linux/macOS
   ifconfig
   ```
   找到局域网IP，例如 `192.168.1.100`

2. **确保设备在同一网络**
   - PC和安卓手机连接到同一个WiFi网络

3. **配置安卓App**
   - 打开"短信转发器"应用
   - 在服务器地址输入框输入：`192.168.1.100:8765`
   - 点击"连接服务器"按钮
   - 状态显示"已连接到服务器"表示成功

4. **测试转发**
   - 向安卓手机发送一条短信
   - PC端终端界面会自动显示短信内容

## 功能特性

### PC端
- [x] WebSocket服务器，监听8765端口
- [x] 终端TUI界面，实时显示短信
- [x] 显示发送者、内容、时间戳
- [x] 消息计数统计
- [x] 清空消息功能 (按 `c` 键)
- [x] 退出程序 (按 `q` 键)

### 安卓端
- [x] 后台服务持续运行
- [x] 自动监听系统短信
- [x] WebSocket连接管理
- [x] 断线消息队列缓存
- [x] 前台服务通知
- [x] 消息日志显示

## 权限说明

### 安卓端权限

| 权限 | 用途 |
|------|------|
| RECEIVE_SMS | 接收系统短信广播 |
| READ_SMS | 读取短信内容 |
| INTERNET | 网络通信 |
| FOREGROUND_SERVICE | 前台服务运行 |
| POST_NOTIFICATIONS | 显示通知 (Android 13+) |

## 常见问题

### Q: 安卓端无法连接PC端？
1. 检查PC和手机是否在同一局域网
2. 检查PC防火墙是否允许8765端口
3. 确认PC端服务已启动

### Q: 收到短信但没有转发？
1. 检查安卓端是否已连接服务器
2. 确认已授予短信权限
3. 查看安卓端消息日志

### Q: PC端界面显示异常？
确保终端支持UTF-8编码和真彩色

## 开发说明

### 修改PC端端口
编辑 `pc/src/sms_receiver/__init__.py`，修改 `SMSReceiverApp` 初始化参数：
```python
app = SMSReceiverApp(host="0.0.0.0", port=8765)
```

### 修改安卓端包名
需要同时修改：
- `mobile/app/build.gradle.kts` 中的 `namespace` 和 `applicationId`
- `mobile/app/src/main/AndroidManifest.xml` 中的包名
- 所有Kotlin文件的包声明

## 许可证

MIT License
