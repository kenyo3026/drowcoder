# 執行工具

## 概述

`execute` 工具提供安全的 shell 命令執行，具有超時保護、忽略檔案驗證和結構化結果輸出。它設計用於執行測試、建置專案、檢查系統狀態或任何 shell 操作。

## 功能

- **安全執行**：超時保護和 .drowignore 檔案驗證
- **結構化輸出**：傳回退出代碼、執行時間和格式化輸出
- **跨平台**：支援 Unix 和 Windows 系統
- **環境控制**：自訂環境變數和工作目錄支援
- **錯誤處理**：包含超時偵測的全面錯誤報告

## 參數

### 必要參數

- **`cmd`** (string)：要執行的 bash/shell 命令。可以是任何有效的 shell 命令，包括：
  - 檔案操作（ls、cp、mv、rm）
  - 建置命令（npm install、pip install、make）
  - 測試命令（pytest、npm test、go test）
  - 系統命令（ps、df、top）
  - Git 操作（git status、git commit）

### 可選參數

- **`cwd`** (string | Path)：命令執行的工作目錄（預設為當前目錄）
- **`timeout_seconds`** (int)：超時秒數（0 = 無超時，預設：0）
- **`shell`** (bool)：使用 shell=True 執行（預設：True）
- **`env`** (dict)：要與 os.environ 合併的環境變數
- **`encoding`** (string)：文字編碼（預設："utf-8"）
- **`combine_stdout_stderr`** (bool)：將 stderr 合併到 stdout（預設：True）
- **`enable_ignore`** (bool)：啟用 .drowignore 驗證（預設：True）
- **`shell_policy`** (string)：.drowignore 的 shell 解析政策（"auto"、"unix"、"powershell"，預設："auto"）

## 使用範例

### 基本命令執行

```python
from drowcoder.tools import ExecuteTool

tool = ExecuteTool()

response = tool.execute(
    cmd="ls -la",
    cwd="/path/to/directory"
)
```

### 帶超時的命令

```python
response = tool.execute(
    cmd="npm test",
    timeout_seconds=300,  # 5 分鐘超時
    cwd="./project"
)
```

### 帶自訂環境的命令

```python
response = tool.execute(
    cmd="python script.py",
    env={"PYTHONPATH": "/custom/path", "DEBUG": "1"}
)
```

## 回應格式

工具傳回一個 `ToolResponse`，包含：

- **`success`**：如果命令已執行則為 `True`（無論退出代碼為何）
- **`content`**：帶有命令執行詳情的格式化字串
- **`error`**：如果執行失敗則為錯誤訊息
- **`metadata.cmd_response`**：詳細的 `CmdResponse` 物件，包含：
  - `cmd`：執行的命令
  - `cwd`：工作目錄
  - `exit_code`：程序退出代碼（如果執行前失敗則為 None）
  - `output`：合併的 stdout/stderr 輸出
  - `error`：錯誤文字（如果有）
  - `pid`：程序 ID
  - `duration_ms`：執行時間（毫秒）
  - `timed_out`：命令是否超時

## 安全功能

### .drowignore 驗證

當 `enable_ignore=True` 時，工具會根據 `.drowignore` 模式驗證命令，以防止未授權的檔案存取。嘗試存取被阻止路徑的命令將被拒絕，退出代碼為 1。

### 超時保護

可以透過執行時間限制命令，以防止掛起的程序。當發生超時時：
- 程序被終止
- `timed_out` 標記設為 `True`
- 錯誤訊息包含超時資訊

## 錯誤處理

工具處理各種錯誤情況：

- **命令被阻止**：傳回退出代碼 1 和錯誤訊息
- **超時**：終止程序並報告超時
- **執行失敗**：捕獲錯誤輸出和退出代碼
- **無效路徑**：如果工作目錄不存在則傳回錯誤

## 最佳實踐

1. **總是設定超時**：對於可能長時間執行的命令，設定適當的超時
2. **使用 .drowignore**：保持 `enable_ignore=True` 以確保安全
3. **檢查退出代碼**：驗證回應元資料中的 `exit_code`，而不僅僅是 `success`
4. **處理超時**：檢查 `timed_out` 標記以處理超時情況
5. **指定工作目錄**：對於需要特定目錄上下文的命令，使用 `cwd` 參數

## 相關文件

- 參閱 [base.md](base.md) 了解架構詳情

