# Drowcoder

> ⚠️ **開發狀態**：此專案目前處於早期開發階段。功能和 API 可能會大幅變更。

一個功能強大的 AI 代理工具，具有豐富的工具集和靈活的配置選項。

## 🚀 安裝

### 方法 1：開發模式安裝（推薦）

適合開發和測試：

```bash
# 複製儲存庫
git clone https://github.com/kenyo3026/drowcoder.git
cd drowcoder

# 以可編輯模式安裝（CLI 工具將自動可用）
pip install -e .

# 驗證安裝
drowcoder --help
```

### 方法 2：直接 Git 安裝

```bash
pip install git+https://github.com/kenyo3026/drowcoder.git
```

### 方法 3：本地開發

如果您想在不安裝的情況下使用：

```bash
git clone https://github.com/kenyo3026/drowcoder.git
cd drowcoder

# 開發模式
python -m src.drowcoder.develop --help

# 或使用範例
python examples/basic_usage.py
```

## 🎯 使用方式

### CLI 工具（安裝後）

```bash
# 基本使用
drowcoder --help

# 指定工作區
drowcoder --workspace /path/to/your/project

# 使用特定配置
drowcoder --config /path/to/config.yaml
```

### 函式庫使用

```python
from drowcoder import DrowAgent, AgentRole

# 建立代理
agent = DrowAgent(role=AgentRole.CODER)

# 初始化
agent.initialize()

# 使用代理
response = agent.process("您的指令")
```

## 📚 文件

### 快速開始

1. **查看範例**：參閱 [examples/basic_usage.py](examples/basic_usage.py)
2. **學習使用**：閱讀 [docs/usage.md](docs/usage.md) - 入門使用指南
3. **探索工具**：瀏覽 [src/drowcoder/tools/](src/drowcoder/tools/) 中的工具文件

### 核心模組

- **[進入點](src/drowcoder/docs/main.md)** - CLI 進入點（main、cli、develop、debug）
- **[代理](src/drowcoder/docs/agent.md)** - 代理進入腳本
- **[檢查點](src/drowcoder/docs/checkpoint.md)** - 用於狀態管理的檢查點系統
- **[配置](src/drowcoder/docs/config.md)** - 配置檔案管理
- **[模型](src/drowcoder/docs/model.md)** - 模型分發器和角色管理
- **[詳細輸出](src/drowcoder/docs/verbose.md)** - 訊息輸出格式化系統

### 工具

- **[基礎工具](src/drowcoder/tools/base.md)** - 工具架構和基礎類別
- **[嘗試完成](src/drowcoder/tools/attempt-completion.md)** - 任務完成信號
- **[Bash](src/drowcoder/tools/bash.md)** - 命令執行
- **[載入](src/drowcoder/tools/load.md)** - 檔案載入
- **[搜尋](src/drowcoder/tools/search.md)** - 內容搜尋
- **[搜尋與替換](src/drowcoder/tools/search-and-replace.md)** - 文字替換
- **[待辦事項](src/drowcoder/tools/todo.md)** - 任務管理
- **[寫入](src/drowcoder/tools/write.md)** - 檔案寫入

## 🏗️ 專案結構

```
drowcoder/
├── src/drowcoder/          # 主要套件
│   ├── main.py            # 核心邏輯
│   ├── cli.py             # 生產環境 CLI
│   ├── develop.py         # 開發環境 CLI
│   ├── debug.py           # 除錯模式
│   ├── agent.py           # AI 代理核心
│   ├── docs/              # 模組文件
│   │   ├── agent.md       # 代理進入腳本
│   │   ├── checkpoint.md  # 檢查點系統
│   │   ├── config.md      # 配置管理
│   │   ├── main.md        # 進入點
│   │   ├── model.md       # 模型分發器
│   │   └── verbose.md     # 輸出格式化
│   ├── tools/             # 工具集合
│   │   ├── *.md           # 個別工具文件
│   │   └── *.py           # 工具實作
│   └── prompts/           # 系統提示
├── docs/                  # 使用者文件
│   └── usage.md           # 使用指南
├── examples/              # 使用範例
├── configs/               # 配置檔案
├── checkpoints/           # 檢查點（開發用）
└── pyproject.toml         # 套件配置
```

## 🔧 開發

### 開發環境設定

```bash
# 複製並進入專案
git clone https://github.com/kenyo3026/drowcoder.git
cd drowcoder

# 安裝開發依賴
pip install -e .

# 以開發模式執行
python -m src.drowcoder.develop
```

### 不同的執行方法

| 方法 | 命令 | 檢查點位置 | 用途 |
|--------|---------|-------------------|---------|
| **CLI 工具** | `drowcoder` | `~/.drowcoder/checkpoints/` | 生產使用 |
| **開發模式** | `python -m src.drowcoder.develop` | `./checkpoints/` | 開發測試 |
| **套件匯入** | `from drowcoder import DrowAgent` | 自訂 | 函式庫使用 |
| **範例腳本** | `python examples/basic_usage.py` | `./checkpoints/` | 學習參考 |

## 💡 需要協助？

- 🐛 **回報問題**：[GitHub Issues](https://github.com/kenyo3026/drowcoder/issues)
- 📖 **文件**：
  - [使用者指南](docs/usage.md) - 入門和使用指南
  - [核心模組](src/drowcoder/docs/) - 核心模組的技術文件
  - [工具](src/drowcoder/tools/) - 個別工具文件
- 💡 **查看範例**：參閱 [examples/](examples/) 目錄
- 🔧 **開發**：參閱上方的 [開發](#-開發) 章節

## 📄 授權

此專案採用 GPL-3.0 授權條款 - 詳見 [LICENSE](LICENSE) 檔案。

