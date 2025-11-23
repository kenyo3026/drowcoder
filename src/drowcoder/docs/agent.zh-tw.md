# 代理進入腳本

## 概述

`agent.py` 腳本提供了一個簡單的進入點，用於直接執行 drowcoder 代理。它是 `DrowAgent` 的輕量級包裝器，處理基本配置載入並提供代理互動的互動式迴圈。

## 功能

- **簡單進入點**：快速啟動代理，無需完整的 CLI 設定
- **配置載入**：從 YAML 檔案載入配置
- **互動式迴圈**：代理對話的持續互動迴圈
- **基本參數解析**：命令列參數用於配置、工作區和檢查點

## 使用方式

### 基本使用

```bash
# 使用預設配置執行
python src/agent.py

# 指定自訂配置
python src/agent.py --config ./configs/config.yaml

# 指定工作區
python src/agent.py --workspace ./my_project

# 指定檢查點
python src/agent.py --checkpoint ./my_checkpoint
```

### 命令列參數

- **`-c, --config`**：配置檔案路徑（預設：`../configs/config.yaml`）
- **`-w, --workspace`**：工作區目錄路徑（可選）
- **`--checkpoint`**：檢查點目錄路徑（可選，未提供時自動產生）

## 程式碼結構

```python
import argparse
import litellm
from config_morpher import ConfigMorpher

from drowcoder.agent import DrowAgent
from drowcoder.checkpoint import CHECKPOINT_DEFAULT_NAME

if __name__ == '__main__':
    # 解析參數
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default='../configs/config.yaml')
    parser.add_argument("-w", "--workspace", default=None, type=str)
    parser.add_argument("--checkpoint", default=None)
    args = parser.parse_args()

    # 載入配置
    config_morpher = ConfigMorpher.from_yaml(args.config)

    # 準備完成參數
    completion_kwargs = config_morpher.morph(
        litellm.completion,
        start_from='models.[name=claude-4-sonnet]'
    )

    # 從配置取得工具
    tools = config_morpher.fetch('tools', None)

    # 建立代理
    agent = DrowAgent(
        workspace=args.workspace,
        tools=tools,
        checkpoint=args.checkpoint or f'../checkpoints/{CHECKPOINT_DEFAULT_NAME()}',
        verbose_style='pretty',
        **completion_kwargs,
    )

    # 初始化並執行互動式迴圈
    agent.init()
    while True:
        agent.receive()
        agent.complete()
```

## 配置

腳本期望一個具有以下結構的 YAML 配置檔案：

```yaml
models:
  - name: claude-4-sonnet
    api_key: YOUR_API_KEY
    model: anthropic/claude-sonnet-4-20250514
    temperature: 0
    roles:
      - chatcompletions

tools:
  # 工具配置（可選）
```

## 工作流程

1. **解析參數**：讀取命令列參數以取得配置、工作區和檢查點
2. **載入配置**：使用 ConfigMorpher 載入 YAML 配置檔案
3. **準備完成**：將配置轉換為 LiteLLM 完成參數
4. **建立代理**：使用配置初始化 DrowAgent
5. **互動式迴圈**：持續接收使用者輸入並完成代理回應

## 與主模組的差異

此腳本比主 CLI 模組（`src/drowcoder/main.py`）更簡單：

| 功能 | agent.py | main.py |
|---------|----------|---------|
| **複雜度** | 簡單 | 功能完整 |
| **CLI 選項** | 基本 | 全面 |
| **配置命令** | 無 | 有（edit/show/validate） |
| **互動模式** | 總是 | 可選 |
| **完成後處理** | 無 | 有 |
| **模型選擇** | 硬編碼 | 靈活 |

## 使用案例

### 開發和測試

在開發過程中快速測試代理功能：

```bash
python src/agent.py --config ./test_config.yaml
```

### 簡單互動式會話

用於不需要完整 CLI 功能的簡單互動式代理會話：

```bash
python src/agent.py --workspace ./project
```

### 自訂腳本

可作為自訂代理腳本的基礎：

```python
# 基於 agent.py 的自訂代理腳本
from drowcoder.agent import DrowAgent
from config_morpher import ConfigMorpher

config = ConfigMorpher.from_yaml('config.yaml')
completion_kwargs = config.morph(litellm.completion, start_from='models[0]')

agent = DrowAgent(
    workspace='./project',
    **completion_kwargs
)
agent.init()
# 自訂邏輯在此
```

## 限制

- **硬編碼模型選擇**：使用 `models.[name=claude-4-sonnet]` - 無法透過 CLI 配置
- **無配置管理**：不支援 config edit/show/validate 命令
- **總是互動式**：總是執行在互動式迴圈模式
- **無完成後處理**：不支援完成後任務
- **固定詳細輸出樣式**：使用 `'pretty'` 樣式（不可配置）

## 何時使用

**使用 `agent.py` 當**：
- 您需要快速、簡單的方式來啟動代理
- 您正在開發或測試
- 您不需要進階 CLI 功能
- 您想要最小的進入點

**使用 `main.py`（透過 CLI）當**：
- 您需要完整的 CLI 功能
- 您想要配置管理命令
- 您需要靈活的模型選擇
- 您想要完成後支援
- 您需要生產就緒的功能

## 相關文件

- 參閱 [checkpoint.md](checkpoint.md) 了解檢查點系統
- 參閱 [model.md](model.md) 了解模型配置
- 參閱 [config.md](config.md) 了解配置管理
- 參閱 [verbose.md](verbose.md) 了解輸出格式化

