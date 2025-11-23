# 載入工具

## 概述

`load` 工具提供檔案載入功能，用於將檔案內容讀取為純文字。它支援各種路徑格式，並提供有關載入檔案的詳細元資料。

## 功能

- **靈活的路徑支援**：處理絕對、相對、主目錄和環境變數路徑
- **路徑解析**：自動路徑展開和解析
- **元資料追蹤**：傳回檔案路徑和大小資訊
- **錯誤處理**：針對缺失或無法存取的檔案提供清晰的錯誤訊息

## 參數

### 必要參數

- **`file_path`** (string)：要載入的檔案路徑。支援：
  - 絕對路徑：`/Users/username/file.txt`
  - 相對路徑：`./file.txt`、`../file.txt`
  - 主目錄：`~/file.txt`
  - 環境變數：`$HOME/file.txt`

### 可選參數

- **`ensure_abs`** (bool)：是否將路徑解析為絕對形式（預設：True）
- **`as_type`**：輸出格式類型（預設：`PRETTY_STR`）
- **`filter_empty_fields`** (bool)：過濾輸出中的空欄位（預設：True）
- **`filter_metadata_fields`** (bool)：過濾元資料欄位（預設：False）

## 使用範例

### 使用絕對路徑載入檔案

```python
from drowcoder.tools import LoadTool

tool = LoadTool()

response = tool.execute(
    file_path="/Users/username/project/config.yaml"
)
```

### 使用相對路徑載入檔案

```python
response = tool.execute(
    file_path="./src/main.py",
    ensure_abs=True
)
```

### 使用主目錄載入檔案

```python
response = tool.execute(
    file_path="~/Documents/notes.txt"
)
```

### 使用環境變數載入檔案

```python
response = tool.execute(
    file_path="$HOME/project/README.md"
)
```

## 回應格式

工具傳回一個 `LoadToolResponse`，包含：

- **`success`**：如果檔案載入成功則為 `True`
- **`content`**：檔案內容作為字串
- **`error`**：如果載入失敗則為錯誤訊息
- **`metadata`**：`LoadToolResponseMetadata`，包含：
  - `file_path`：解析後的絕對檔案路徑
  - `file_size`：載入檔案的大小（位元組）

## 錯誤處理

工具處理各種錯誤情況：

- **檔案未找到**：傳回 `success=False` 和錯誤訊息「錯誤：找不到檔案 '{file_path}'。」
- **權限錯誤**：傳回描述存取問題的錯誤訊息
- **無效路徑**：如果無法解析路徑則傳回錯誤

## 最佳實踐

1. **使用絕對路徑**：如果可能，使用絕對路徑或設定 `ensure_abs=True`
2. **檢查成功**：在使用 `content` 前始終驗證 `success` 欄位
3. **處理錯誤**：當 `success=False` 時檢查錯誤訊息
4. **檔案大小**：使用 `metadata.file_size` 在處理大檔案前檢查檔案大小

## 實作詳情

- **編碼**：檔案以 UTF-8 編碼讀取
- **路徑解析**：預設將路徑解析為絕對形式
- **檔案大小**：使用 `stat().st_size` 計算以獲得準確的位元組數
- **回呼支援**：如果已配置，會觸發「file_loaded」回呼事件

## 相關文件

- 參閱 [base.md](base.md) 了解架構詳情

