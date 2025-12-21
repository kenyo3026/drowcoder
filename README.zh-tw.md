# Drowcoder

一個專注於程式設計的 AI 助手 🤖，支援統一整合的內建 tools 和 MCP（Model Context Protocol）

> [!NOTE]
> 此專案目前正在持續開發中。功能和 API 可能會頻繁變更。

## ✨ 核心特色

- **🔧 內建工具**：7 個程式設計工具（load、search、search_and_replace、write、bash、todo、attempt_completion）
- **🌐 MCP 整合**：支援 Streamable HTTP 和 Stdio 兩種傳輸方式
- **🔀 統一調度器**：同時使用內建工具和 MCP 伺服器
- **📦 可擴展**：繼承 `BaseTool` 即可添加自訂工具
- **💾 檢查點系統**：狀態持久化，支援跨會話恢復
- **⚙️ 靈活配置**：YAML 配置檔，支援角色型模型管理
- **🚀 多種使用方式**：CLI、開發模式或函式庫

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

如果不想安裝，可以直接使用：

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
from drowcoder import DrowAgent

# 建立代理
agent = DrowAgent(
    workspace="/path/to/project",
    tools=None,  # 使用預設內建工具
    mcps=None,   # 可選：MCP 伺服器配置
    model="gpt-4",
    api_key="your-api-key"
)

# 初始化
agent.init()

# 處理指令
agent.receive("您的指令")
agent.complete()
```

> [!NOTE]
> 更詳細的 API 使用方式請參閱 [examples/basic_usage.py](examples/basic_usage.py)

## 📚 文件

### 快速開始

1. **查看範例**：參考 [examples/basic_usage.py](examples/basic_usage.py)
2. **學習使用**：閱讀 [docs/usage.md](docs/usage.md) 入門指南
3. **探索工具**：查看 [src/drowcoder/tools/](src/drowcoder/tools/) 中的工具文件

### 核心模組

- **[進入點](src/drowcoder/docs/main.md)** - CLI 進入點（main、cli、develop、debug）
- **[代理](src/drowcoder/docs/agent.md)** - 代理核心邏輯
- **[檢查點](src/drowcoder/docs/checkpoint.md)** - 狀態管理系統
- **[配置](src/drowcoder/docs/config.md)** - 配置管理
- **[模型](src/drowcoder/docs/model.md)** - 模型分發器和角色管理
- **[詳細輸出](src/drowcoder/docs/verbose.md)** - 輸出格式化

### 工具與架構

- **[工具調度器架構](src/drowcoder/tools/README.md)** - 統一調度系統說明
- **[基礎工具](src/drowcoder/tools/tools/base.md)** - 工具架構和基礎類別
- **內建工具**：
  - **[載入](src/drowcoder/tools/tools/load.md)** - 檔案載入
  - **[搜尋](src/drowcoder/tools/tools/search.md)** - 內容搜尋
  - **[搜尋與替換](src/drowcoder/tools/tools/search-and-replace.md)** - 文字替換
  - **[寫入](src/drowcoder/tools/tools/write.md)** - 檔案寫入
  - **[Bash](src/drowcoder/tools/tools/bash.md)** - 命令執行
  - **[待辦事項](src/drowcoder/tools/tools/todo.md)** - 任務管理
  - **[嘗試完成](src/drowcoder/tools/tools/attempt-completion.md)** - 任務完成信號
- **[MCP 整合](src/drowcoder/tools/mcps/README.md)** - Model Context Protocol 支援

## 🏗️ 專案結構

```
drowcoder/
├── src/drowcoder/          # 主要套件
│   ├── main.py            # 核心邏輯
│   ├── cli.py             # 生產環境 CLI
│   ├── develop.py         # 開發環境 CLI
│   ├── debug.py           # 除錯模式
│   ├── agent.py           # AI 代理核心
│   ├── checkpoint.py      # 檢查點管理
│   ├── config.py          # 配置載入器
│   ├── model.py           # 模型分發器
│   ├── verbose.py         # 輸出格式化
│   ├── docs/              # 模組文件
│   │   ├── main.md        # 進入點
│   │   ├── agent.md       # 代理系統
│   │   ├── checkpoint.md  # 檢查點系統
│   │   ├── config.md      # 配置
│   │   ├── model.md       # 模型分發器
│   │   └── verbose.md     # 輸出格式化
│   ├── tools/             # 工具系統
│   │   ├── README.md      # 工具架構概述
│   │   ├── dispatcher.py  # 統一調度器
│   │   ├── runtime.py     # 工具執行環境
│   │   ├── tools/         # 內建工具
│   │   │   ├── base.py    # 基礎工具類別
│   │   │   ├── dispatcher.py  # 工具調度器
│   │   │   ├── *.py       # 工具實作
│   │   │   ├── *.yaml     # 工具配置
│   │   │   ├── *.md       # 工具文件
│   │   │   ├── tests/     # 工具測試
│   │   │   └── utils/     # 工具工具程式
│   │   └── mcps/          # MCP 整合
│   │       ├── README.md  # MCP 文件
│   │       ├── base.py    # MCP 基礎客戶端
│   │       ├── dispatcher.py  # MCP 調度器
│   │       ├── streamable_http.py  # HTTP 傳輸
│   │       ├── stdio.py   # Stdio 傳輸
│   │       └── utils.py   # MCP 工具程式
│   ├── prompts/           # 系統提示
│   │   └── system.py      # 系統提示模板
│   └── utils/             # 工具程式
│       ├── logger.py      # 日誌工具
│       ├── mixin.py       # Mixin 類別
│       └── unique_id.py   # ID 生成
├── docs/                  # 使用者文件
│   └── usage.md           # 使用指南
├── examples/              # 使用範例
│   └── basic_usage.py     # 基本範例
├── scripts/               # 工具腳本
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
  - [工具調度器架構](src/drowcoder/tools/README.md) - 統一工具系統概述
  - [內建工具](src/drowcoder/tools/tools/) - 個別工具文件
  - [MCP 整合](src/drowcoder/tools/mcps/README.md) - MCP 伺服器整合指南
- 💡 **查看範例**：參考 [examples/](examples/) 目錄
- 🔧 **開發**：查看上方的 [開發](#-開發) 章節

## 📄 授權

此專案採用 GPL-3.0 授權條款，詳見 [LICENSE](LICENSE) 檔案。

