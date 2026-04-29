# Game Assistant

**Push-to-talk AI assistant for gamers.** Hold a key, ask a question, get a voice answer — right on top of your game.

**游戏AI语音助手** — 按住按键说话，AI语音回答，覆盖在游戏画面上。支持国内AI服务。

---

## Download / 下载

> **[Download Latest Release](../../releases/latest)** — `GameAssistant.exe` (Windows 10/11)

No installation needed. Extract the zip, edit `config.yaml` with your API key, and run.

无需安装。解压后在 `config.yaml` 中填入API密钥，双击运行即可。

---

## Features / 功能

| Feature | Description |
|---|---|
| **Push-to-Talk** | Hold a key to record your voice, release to get an AI answer / 按住说话，松开获得回答 |
| **Voice Response** | AI answers are spoken aloud via TTS / AI回答通过语音播放 |
| **Game Overlay** | Transparent text overlay on top of your game / 透明文字覆盖在游戏上方 |
| **Multi-Provider** | Choose your AI: DeepSeek, SiliconFlow, OpenAI, Groq, Ollama, or any custom API / 支持多种AI |
| **Custom Keybinds** | Bind any key via the Settings GUI — click the button, press your key / 自定义按键绑定 |
| **Screen Capture** | Optional: AI can see your screen to give better advice / 可选：AI截图分析画面 |
| **Bilingual** | Works in Chinese, English, Japanese, or auto-detect / 支持中英日多语言 |

---

## How It Works / 工作流程

```
Hold Key → Speak → Release → AI Thinks → Voice Answer + Overlay Text
按住按键 →  说话  →  松开   →  AI思考   →  语音回答 + 文字覆盖
```

```
┌─────────────────────────────────────────────┐
│                  Your Game                   │
│                                             │
│                                             │
│                                             │
│         ● Listening...                      │  ← Status indicator
│     You: Where's the boss?                  │  ← Your question
│  ┌───────────────────────────────────┐      │
│  │ Go north through the fog gate.    │      │  ← AI response overlay
│  │ The boss arena is past the two    │      │     (auto-hides)
│  │ knights on the bridge.            │      │
│  └───────────────────────────────────┘      │
└─────────────────────────────────────────────┘
```

---

## AI Providers / AI服务商

Choose the one that works best for you:

| Provider | Cost | China | Sign Up |
|---|---|---|---|
| **DeepSeek** | ~1 yuan/M tokens | Yes | [platform.deepseek.com](https://platform.deepseek.com) |
| **SiliconFlow** | Free tier | Yes | [siliconflow.cn](https://siliconflow.cn) |
| **OpenAI** | Paid | Needs VPN | [platform.openai.com](https://platform.openai.com) |
| **Groq** | Free tier | Needs VPN | [console.groq.com](https://console.groq.com) |
| **Ollama** | Free (local GPU) | Yes | [ollama.com](https://ollama.com) |
| **Custom** | Varies | Varies | Any OpenAI-compatible API |

> For Chinese users / 国内用户推荐: **DeepSeek** (便宜好用) or **SiliconFlow** (有免费额度)

---

## Quick Start / 快速开始

### Option A: Download the .exe (easiest)

1. Download `GameAssistant.exe` from [Releases](../../releases/latest)
2. Run it — a tray icon appears
3. Right-click tray icon → **Settings**
4. Pick your AI provider, enter API key, bind your push-to-talk key
5. Save, start gaming, hold your key to talk

### Option B: Run from source

```bash
git clone https://github.com/Shuhuai233/game-assistant.git
cd game-assistant
pip install -r requirements.txt
python main.py
```

### Option C: Build your own .exe

```bash
git clone https://github.com/Shuhuai233/game-assistant.git
cd game-assistant
pip install -r requirements.txt
pip install pyinstaller
build.bat
# Output: dist/GameAssistant.exe
```

---

## Settings / 设置

Double-click the tray icon (or right-click → Settings) to open the settings dialog:

### AI Provider Tab
- Select provider from dropdown
- Enter API key
- Change model name or endpoint URL

### Key Bindings Tab
- Click the button, then press the key you want
- Bind push-to-talk, screenshot, and quit keys
- Works with any key: F keys, mouse buttons, tilde, etc.

### Audio / Voice Tab
- Choose STT engine (Faster Whisper or FunASR)
- Select language (Chinese / English / Japanese / Auto)
- Pick TTS voice (male/female voices per language)
- Toggle screen capture on/off

### Game Tab
- Set game name
- Customize the system prompt (tell AI what game you're playing and how to help)

---

## Default Controls / 默认按键

| Key | Action |
|---|---|
| `Caps Lock` (hold) | Push-to-talk / 按住说话 |
| `F8` | Screenshot + ask AI / 截图提问 |
| `Ctrl+Shift+Q` | Quit / 退出 |

All keys are rebindable in Settings. / 所有按键可在设置中自定义。

---

## Project Structure / 项目结构

```
game-assistant/
├── main.py              # Entry point (routes to GUI or CLI)
├── app.py               # System tray + overlay GUI
├── overlay.py           # Transparent overlay window
├── settings_dialog.py   # Settings GUI with tabs
├── config.yaml          # User configuration
├── config_loader.py     # Config parser
├── llm_client.py        # LLM provider abstraction (all use OpenAI-compatible API)
├── stt_engine.py        # Speech-to-text (faster-whisper / FunASR)
├── tts_engine.py        # Text-to-speech (Edge TTS / pyttsx3)
├── audio_recorder.py    # Push-to-talk microphone recording
├── screen_capture.py    # Screenshot → base64 for vision models
├── requirements.txt     # Python dependencies
├── game_assistant.spec  # PyInstaller build spec
├── build.bat            # One-click build script (Windows)
└── .github/workflows/   # Auto-build on release
```

---

## Requirements / 系统要求

- **Windows 10/11**
- Microphone
- Internet connection (for AI API + Edge TTS)
- No GPU needed (STT runs on CPU, just slower)

---

## CLI Mode / 命令行模式

If you prefer terminal over GUI:

```bash
python main.py --cli          # Run in terminal
python main.py --setup        # First-time setup wizard
python main.py --rebind       # Rebind keys from terminal
```

---

## License

MIT
