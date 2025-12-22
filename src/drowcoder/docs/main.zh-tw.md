# 進入點

## 概述

drowcoder 套件為不同的使用案例提供多個進入點。所有進入點都基於 `Main` 類別，它提供核心執行邏輯。每個進入點針對特定場景自訂預設配置和行為。

## 架構

```
Main (基礎類別)
├── CliMain (生產環境)
├── DevMain (開發環境)
└── DebugMain (除錯)
```

所有進入點都繼承自 `Main` 並自訂：
- 預設配置路徑
- 預設檢查點位置
- 執行行為（用於除錯模式）

## 主模組

`main.py` 模組提供核心 `Main` 類別和 `MainArgs` 資料類別，所有進入點都基於此。

### MainArgs

命令列參數的配置資料類別：

```python
@dataclass
class MainArgs:
    query: str = None
    config: str = './config.yaml'
    model: str = None
    interactive: bool = False
    workspace: str = None
    checkpoint: str = None
    checkpoint_root: str = './checkpoints'
    command: str = None
    config_action: str = None
```

### Main 類別

提供以下功能的核心執行類別：

- **配置載入**：載入 YAML 或 JSON 配置
- **模型分發**：使用 ModelDispatcher 進行基於角色的模型組織
- **代理建立**：建立並初始化 DrowAgent
- **執行模式**：支援無頭模式和互動模式
- **完成後處理**：支援完成後任務
- **配置命令**：處理 config edit/show/validate 子命令

### Main.run()

主要執行方法，會依序執行：

1. 解析命令列參數
2. 處理配置子命令（如果有的話）
3. 載入配置並分發模型
4. 建立並初始化代理
5. 在無頭或互動模式下執行
6. 處理完成後任務

## CLI 進入點（生產環境）

**檔案**：`cli.py`
**類別**：`CliMain`
**使用**：`drowcoder`（安裝後）或 `python -m src.drowcoder.cli`

### 功能

- **使用者目錄**：檢查點儲存到 `~/.drowcoder/checkpoints/`
- **使用者配置**：配置位於 `~/.drowcoder/config.yaml`
- **自動設定**：如果缺失則自動建立和配置配置檔案
- **生產就緒**：為終端使用者設計

### 預設路徑

- **配置**：`~/.drowcoder/config.yaml`
- **檢查點根目錄**：`~/.drowcoder/checkpoints/`

### 配置設定

CLI 進入點包含自動配置設定：

```python
def setup_config(yaml_path):
    # 如果缺失則建立配置檔案
    # 如果無效則提示模型和 API 金鑰
    # 傳回配置路徑
```

如果配置檔案缺失或無效，它將：
1. 提示輸入模型識別碼
2. 提示輸入 API 金鑰
3. 建立有效的配置檔案

### 使用方式

```bash
# 安裝後
drowcoder --workspace ./project

# 或直接執行
python -m src.drowcoder.cli --workspace ./project
```

## 開發進入點

**檔案**：`develop.py`
**類別**：`DevMain`
**使用**：`python -m src.drowcoder.develop`

### 功能

- **專案目錄**：檢查點儲存到 `./checkpoints/`（專案根目錄）
- **專案配置**：配置位於 `./configs/config.yaml`（專案根目錄）
- **自動偵測**：透過 `pyproject.toml` 自動尋找專案根目錄
- **開發導向**：為開發和測試設計

### 預設路徑

- **配置**：`{project_root}/configs/config.yaml`
- **檢查點根目錄**：`{project_root}/checkpoints/`

### 專案根目錄偵測

透過搜尋 `pyproject.toml` 自動尋找專案根目錄：

```python
def find_project_root() -> Path:
    # 向上搜尋目錄樹以尋找 pyproject.toml
    # 傳回專案根目錄或當前目錄
```

### 使用方式

```bash
# 從專案根目錄
python -m src.drowcoder.develop --workspace ./project

# 自動偵測專案根目錄
python -m src.drowcoder.develop
```

## 除錯進入點

**檔案**：`debug.py`
**類別**：`DebugMain`
**使用**：`python -m src.drowcoder.debug`

### 功能

- **逐步執行**：在每次迭代後暫停
- **互動控制**：在繼續前等待使用者確認
- **回應檢查**：可選查看回應字典
- **除錯日誌**：增強的除錯日誌
- **與 Dev 相同的預設值**：使用 DevArgs 預設值

### 執行流程

1. 接收使用者查詢
2. 執行一個完成步驟
3. 顯示迭代資訊
4. 等待使用者確認：
   - `y`：繼續到下一次迭代
   - `n`：停止除錯
   - `r`：顯示回應字典
5. 重複直到沒有工具呼叫或使用者停止

### 除錯選項

- **繼續 (y)**：進行下一次迭代
- **停止 (n)**：結束除錯會話
- **顯示回應 (r)**：以 YAML 格式顯示回應字典

### 使用方式

```bash
# 啟動除錯模式
python -m src.drowcoder.debug --workspace ./project

# 帶初始查詢
python -m src.drowcoder.debug --query "您的任務"
```

### 範例會話

```
🐛 DrowCoder DEBUG 模式已啟動！
代理將在每次迭代後暫停並等待您的確認。

============================================================
🔍 DEBUG 迭代 1
============================================================

[代理執行一個步驟...]

============================================================
⚠️  偵測到工具呼叫。代理想要繼續。

[DEBUG] (y)繼續 / (n)停止 / (r)顯示回應: r

============================================================
📋 回應字典：
============================================================
[回應字典的 YAML 輸出]

[DEBUG] (y)繼續 / (n)停止 / (r)顯示回應: y

[繼續到下一次迭代...]
```

## 比較表

| 功能 | CLI（生產環境） | Develop | Debug |
|---------|-----------------|---------|-------|
| **檢查點位置** | `~/.drowcoder/checkpoints/` | `./checkpoints/` | `./checkpoints/` |
| **配置位置** | `~/.drowcoder/config.yaml` | `./configs/config.yaml` | `./configs/config.yaml` |
| **自動配置設定** | ✅ 是 | ❌ 否 | ❌ 否 |
| **專案根目錄偵測** | ❌ 否 | ✅ 是 | ✅ 是 |
| **逐步執行** | ❌ 否 | ❌ 否 | ✅ 是 |
| **回應檢查** | ❌ 否 | ❌ 否 | ✅ 是 |
| **使用案例** | 終端使用者 | 開發者 | 除錯 |

## 命令列參數

所有進入點都支援相同的參數（繼承自 `MainArgs`）：

### 主要參數

- **`-q, --query`**：無頭模式 - 直接處理查詢，否則為互動模式
- **`-c, --config`**：配置檔案路徑
- **`-m, --model`**：要使用的模型（覆寫配置）
- **`-i, --interactive`**：強制互動模式
- **`-w, --workspace`**：工作區目錄
- **`--checkpoint`**：檢查點目錄
- **`--checkpoint_root`**：檢查點根目錄

### 子命令

- **`config edit`**：編輯配置檔案
- **`config show`**：顯示當前配置
- **`config validate`**：驗證配置檔案

## 執行模式

### 無頭模式

處理單一查詢並退出：

```bash
drowcoder --query "您的任務" --workspace ./project
```

### 互動模式

持續互動迴圈：

```bash
drowcoder --workspace ./project
# 或
drowcoder --interactive --workspace ./project
```

### 混合模式

處理初始查詢，然後切換到互動模式：

```bash
drowcoder --query "初始任務" --interactive --workspace ./project
```

## 完成後任務

所有進入點（除錯除外）都支援完成後任務：

```yaml
models:
  - name: model
    roles:
      - chatcompletions
      - postcompletions: "檢視變更並建立摘要"
```

主完成後，代理會自動：
1. 執行完成後任務
2. 使用完成後模型（如果不同）
3. 在同一會話中繼續

## 最佳實踐

### 對於終端使用者

- 使用 **CLI 進入點**（`drowcoder`）
- 配置自動設定
- 檢查點在使用者目錄中

### 對於開發者

- 使用 **開發進入點**（`python -m src.drowcoder.develop`）
- 檢查點在專案目錄中
- 易於測試和迭代

### 對於除錯

- 使用 **除錯進入點**（`python -m src.drowcoder.debug`）
- 逐步執行
- 檢查回應
- 了解代理行為

## 相關文件

- 參閱 [checkpoint.md](checkpoint.md) 了解檢查點系統
- 參閱 [model.md](model.md) 了解模型配置
- 參閱 [config.md](config.md) 了解配置管理

