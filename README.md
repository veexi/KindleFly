# KindleFly 🚀

> 📬 **一款高颜值、全自动的 Kindle 电子书本地推送工具**  
> 支持 Windows 系统托盘后台静默运行、定时扫描指定目录、谷歌 Gmail 安全推送以及 MD5 文件防重复防漏推送保护。

---

## ✨ 软件特色

*   🎨 **现代极简 GUI 界面**：采用 CustomTkinter 现代深色主题设计，操作界面流畅且富有科技感。
*   🕵️‍♂️ **后台静默扫描**：支持一键最小化至 Windows 系统托盘，默默在后台守护并定时扫描文件夹，不占任务栏空间。
*   🔒 **谷歌 Gmail 深度优化**：预设 Gmail SMTP 安全参数，并内置详细的 Gmail「应用专用密码 (App Password)」图文生成指南，支持一键连接测试。
*   🚫 **双重防重复保护**：推送前对电子书进行 MD5 指纹计算，建立本地 `sent_books.json` 数据库，即便书籍被重命名或移动，也**绝不重复推送**，避免邮件轰炸。
*   🚀 **单次手动扫描**：除了定时自动监控，提供「立即扫描推送」按钮，随时手动强行唤醒扫描，秒级触达。
*   ⏳ **智能频控与避让**：发送多本书籍时，自动留出 3 秒的邮件安全冷却时间，若发生网络波动或失败，自动避让 10 秒后重试。

---

## 📂 项目结构

```text
KindleFly/
├── assets/
│   ├── app_icon.png        # GUI 主界面图标 & 系统托盘图标
│   └── app_icon.ico        # 编译后 Windows 资源管理器 .exe 运行图标
├── config_manager.py       # JSON 配置文件存储与读取 (Base64 加密发信授权码)
├── history_manager.py      # 已成功推送的电子书 MD5 指纹数据库
├── email_sender.py         # 封装 SMTP (支持 SSL/TLS 协议) 的邮件推送客户端
├── service.py              # 后台守护线程逻辑 (高响应度可随时打断的定时扫描轮询)
├── main.py                 # 主 GUI 界面实现与 pystray 托盘线程交互
├── requirements.txt        # 依赖列表
└── README.md               # 项目使用指南
```

---

## 🛠️ 快速上手指引

想要完美运行 KindleFly 推送，需要完成以下三步配置：

### 第一步：将您的 Gmail 邮箱加入亚马逊白名单（认可列表）

亚马逊出于个人隐私保护，只接收经您认可的邮箱发出的书籍文件：
1.  登录亚马逊官网，进入右上角「账户与列表」 -> **「管理我的内容和设备 (Manage Your Content and Devices)」**。
2.  点击顶部导航栏的 **「首选项 (Preferences)」**，向下滚动找到 **「个人文档设置 (Personal Document Settings)」**。
3.  在 **「已认可的个人文档电子邮箱列表 (Approved Personal Document E-mail List)」** 下，点击「添加新的认可电子邮箱」，将您的发信邮箱（如 `yourname@gmail.com`）添加进去。
4.  *顺便在此页面记下您 Kindle 设备的专属接收邮箱（如 `xxx@kindle.com` 或 `xxx@free.kindle.com`）。*

### 第二步：生成谷歌 Gmail 的「应用专用密码 (App Password)」

目前谷歌邮箱已彻底关闭「不够安全的应用」直连，使用传统的邮箱密码是无法连接 SMTP 的，必须生成 16 位的应用密码：
1.  登录您的 **[谷歌账号安全性中心 (Google Account Security)](https://myaccount.google.com/security)**。
2.  确保已开启 **「两步验证 (2-Step Verification)」**。
3.  在搜索框中搜索 **「应用专用密码 (App Passwords)」** 并进入。
4.  在应用类型中随便取个名字（如 `KindleFly`），点击 **「创建」**。
5.  页面会弹出一个黄框，显示 **16 位字母密码**。复制该密码（填入软件时请去除所有空格）。

### 第三步：运行与配置 KindleFly

1.  双击运行 **`KindleFly.exe`**。
2.  进入 **📧 Gmail 发信配置** 标签页：
    *   填入您的 Gmail 发信邮箱。
    *   填入 16 位的 Gmail 应用专用密码。
    *   点击 **「测试连接」**，成功后点击 **「保存发信配置」**。
3.  进入 **⚙ 目录与 Kindle 推送配置** 标签页：
    *   输入您的 Kindle 接收邮箱。
    *   点击「选择文件夹」，选择您在本地存放电子书的监控文件夹路径。
    *   滑动滑块选择自动扫描的间隔时间（推荐 10-20 分钟）。
    *   勾选需要推送的电子书类型（如 EPUB, PDF）。
    *   点击 **「保存推送设置」**。
4.  回到 **📊 控制面板**，打开侧边栏最下方的 **「开启服务」** 开关。
5.  **开始推送**：只需将匹配后缀的电子书扔进您监控的文件夹，后台服务就会自动为您送达 Kindle，并在主界面展示实时运行日志！

---

## 💻 源码编译说明 (开发者)

如果您想对软件进行二次开发或自己打包，请参考以下流程：

### 1. 搭建环境

```bash
# 建议在项目目录下创建虚拟环境
python -m venv .venv
# 激活虚拟环境 (Windows CMD)
.venv\Scripts\activate
# 安装依赖
pip install -r requirements.txt
```

### 2. 打包编译

KindleFly 使用 `PyInstaller` 编译为单一的、带图标的 Windows 纯绿色无黑框可执行程序：

```bash
pyinstaller --noconfirm --onefile --windowed --add-data "assets;assets" --icon "assets/app_icon.ico" main.py
```

编译完成后，您可以在生成的 `dist` 目录下找到打包好的 `main.exe`，重命名为 `KindleFly.exe` 即可在任意没有 Python 环境的 Windows 电脑上运行！

---

## 🔒 隐私与安全性声明

KindleFly **不会收集或上传**您的任何敏感信息。您的 Gmail 邮箱及应用专用密码在本地是通过 **Base64** 隐藏编码并以纯本地 JSON (`config.json`) 形式存储在您的软件同级目录下，绝不会经由第三方服务器，保障了您个人发信箱的安全。
