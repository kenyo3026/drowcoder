# 搜尋工具

## 概述

`search` 工具提供強大的檔案內容搜尋功能，具有正則表達式模式匹配、檔案模式過濾、工作區邊界檢查和多種輸出格式（樹狀圖和文字）。

## 功能

- **正則表達式模式匹配**：使用標準正則表達式語法搜尋檔案內容
- **檔案模式過濾**：透過 glob 模式過濾檔案（例如，`*.py`、`*.txt`）
- **工作區邊界檢查**：防止在指定工作目錄外進行未授權存取
- **多種輸出格式**：樹狀圖視覺化或傳統文字格式
- **.drowignore 支援**：尊重忽略模式以進行檔案過濾
- **匹配限制**：控制每個檔案顯示的最大匹配數

## 參數

### 必要參數

- **`path`** (string)：要遞迴搜尋的目錄路徑，或要搜尋的特定檔案路徑。可以是相對或絕對路徑。
- **`content_pattern`** (string)：要在檔案內容中搜尋的正則表達式模式。使用標準正則表達式語法（例如，`"TODO"`、`"import.*os"`、`"def\s+\w+"`）。
- **`filepath_pattern`** (string)：要過濾哪些檔案進行搜尋的檔案名稱模式。支援 glob 模式，如 `"*.py"`、`"*.txt"`、`"config.*"`，或 `"*"` 表示所有檔案。

### 可選參數

- **`cwd`** (string)：用於邊界檢查的工作目錄（工作區根目錄）。如果未提供，使用當前工作目錄。除非明確允許，否則搜尋將限制在此工作區內。
- **`max_matches_per_file`** (int)：每個檔案顯示的最大匹配數（預設：10）
- **`enable_search_outside`** (bool)：允許在工作區外搜尋（預設：True）
- **`as_text`** (bool)：當 `as_graph=False` 時傳回格式化文字或原始結果（預設：True）
- **`as_graph`** (bool)：使用樹狀圖格式顯示結果，優先於 `as_text`（預設：True）
- **`only_filename`** (bool)：如果為 `True`，僅傳回檔案名稱和匹配數；如果為 `False`，傳回詳細內容（預設：False）
- **`enable_ignore`** (bool)：啟用 .drowignore 檔案過濾（預設：True）
- **`shell_policy`** (string)：命令解析的 shell 政策（`"auto"`、`"unix"`、`"powershell"`，預設：`"auto"`）

## 使用範例

### 基本內容搜尋

```python
from drowcoder.tools import SearchTool

tool = SearchTool()

response = tool.execute(
    path="./src",
    content_pattern="TODO|FIXME",
    filepath_pattern="*.py"
)
```

### 使用樹狀圖輸出搜尋

```python
response = tool.execute(
    path="./project",
    content_pattern="def\s+\w+",
    filepath_pattern="*.py",
    as_graph=True,
    only_filename=False
)
```

### 快速僅檔案名稱搜尋

```python
response = tool.execute(
    path="./src",
    content_pattern=".*",
    filepath_pattern="*.py",
    only_filename=True  # 快速概覽，無詳細內容
)
```

### 搜尋單一檔案

```python
response = tool.execute(
    path="./src/main.py",
    content_pattern="import",
    filepath_pattern="*"
)
```

## 回應格式

工具傳回一個 `SearchToolResponse`，包含：

- **`success`**：如果搜尋成功完成則為 `True`
- **`content`**：格式化的搜尋結果（樹狀圖或文字格式）
- **`error`**：如果搜尋失敗則為錯誤訊息
- **`metadata`**：`SearchToolResponseMetadata`，包含：
  - `path`：搜尋路徑
  - `content_pattern`：使用的正則表達式模式
  - `filepath_pattern`：使用的檔案模式
  - `files_found`：匹配搜尋的檔案數量
  - `total_matches`：所有檔案中的總匹配數

## 輸出格式

### 樹狀圖格式（預設）

以階層樹狀結構顯示結果，顯示檔案路徑和匹配：

```
project/
    src/
        main.py
          1   | import os
          5   | import sys
        utils.py
          10  | def helper():
```

### 文字格式

帶有檔案路徑和匹配詳情的傳統清單格式：

```
找到 2 個檔案有匹配

# src/main.py (2 個匹配)
  1   | import os
  5   | import sys

# src/utils.py (1 個匹配)
  10  | def helper():
```

## 安全功能

### 工作區邊界檢查

當 `enable_search_outside=False` 時，工具會防止在指定工作區目錄外搜尋。這有助於防止未授權存取系統檔案或其他專案。

### .drowignore 支援

當 `enable_ignore=True` 時，匹配 `.drowignore` 中模式的檔案會自動從搜尋結果中排除。

## 最佳實踐

1. **使用特定模式**：使用特定的正則表達式模式縮小搜尋範圍，避免結果過多
2. **從僅檔案名稱開始**：使用 `only_filename=True` 進行初始探索，然後取得詳情
3. **設定匹配限制**：使用 `max_matches_per_file` 控制輸出大小
4. **尊重工作區**：除非必要，否則保持 `enable_search_outside=False`
5. **使用檔案模式**：結合內容模式和檔案模式以進行高效搜尋

## 錯誤處理

工具處理各種錯誤情況：

- **無效正則表達式**：對無效正則表達式模式引發 `re.error`
- **路徑未找到**：如果搜尋路徑不存在則傳回錯誤
- **工作區外**：如果路徑在工作區外且 `enable_search_outside=False` 則傳回錯誤
- **檔案讀取錯誤**：記錄無法讀取的檔案警告，但繼續搜尋

## 相關文件

- 參閱 [base.md](base.md) 了解架構詳情

