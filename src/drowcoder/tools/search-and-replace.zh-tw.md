# 搜尋與替換工具

## 概述

`search_and_replace` 工具提供檔案內容搜尋和替換功能，具有精確行匹配、多行模式支援、預覽/套用模式和多種輸出樣式（預設、git_diff、git_conflict）。

## 功能

- **精確行匹配**：單行和多行精確字串匹配
- **靈活替換**：一對多、多對一和刪除操作
- **預覽模式**：在套用前安全預覽變更
- **多種輸出樣式**：預設、git diff 和 git conflict 格式
- **行範圍目標**：可選的開始/結束行約束
- **大小寫敏感性控制**：可配置的大小寫敏感匹配

## 參數

### 必要參數

- **`file`** (string | Path)：要搜尋的目標檔案或目錄路徑
- **`search`** (string)：要尋找的精確行。使用 `'\n'` 表示連續的多行模式
- **`replace`** (string | List[str])：替換內容。可以是多行字串或空字串以進行刪除

### 可選參數

- **`file_pattern`** (string)：要匹配的檔案模式（預設：`"*"`）
- **`case_sensitive`** (bool)：搜尋是否區分大小寫（預設：True）
- **`start_line`** (int)：搜尋範圍的開始行號（可選）
- **`end_line`** (int)：搜尋範圍的結束行號（可選）
- **`mode`** (string)：執行模式 - `"preview"` 或 `"apply"`（預設：`"apply"`）
- **`output_style`** (string)：輸出樣式 - `"default"`、`"git_diff"` 或 `"git_conflict"`（預設：`"default"`）
- **`output_file`** (string | Path)：可選的輸出檔案路徑（用於套用模式）

## 使用範例

### 單行替換

```python
from drowcoder.tools import SearchAndReplaceTool

tool = SearchAndReplaceTool()

response = tool.execute(
    file="./src/main.py",
    search="import os",
    replace="import os\nimport sys"
)
```

### 多行替換

```python
response = tool.execute(
    file="./config.py",
    search="DEBUG = True\nLOG_LEVEL = 'info'",
    replace="DEBUG = False\nLOG_LEVEL = 'debug'"
)
```

### 預覽模式（安全測試）

```python
response = tool.execute(
    file="./src/utils.py",
    search="old_function()",
    replace="new_function()",
    mode="preview",
    output_style="git_diff"
)
```

### 不區分大小寫的替換

```python
response = tool.execute(
    file="./README.md",
    search="Python",
    replace="Python 3.11",
    case_sensitive=False
)
```

### 行範圍替換

```python
response = tool.execute(
    file="./src/main.py",
    search="TODO",
    replace="DONE",
    start_line=10,
    end_line=50
)
```

### 刪除（空替換）

```python
response = tool.execute(
    file="./config.py",
    search="deprecated_option = True",
    replace=""  # 刪除匹配的行
)
```

## 回應格式

工具傳回一個 `SearchAndReplaceToolResponse`，包含：

- **`success`**：如果操作成功完成則為 `True`
- **`content`**：摘要訊息或格式化輸出（取決於模式）
- **`error`**：如果操作失敗則為錯誤訊息
- **`file_responses`**：`FileResponse` 物件清單，每個包含：
  - `file_path`：處理的檔案路徑
  - `matches`：帶有匹配詳情的 `LineMatch` 物件清單
  - `has_matches`：表示是否找到匹配的布林值
  - `total_matches`：找到的匹配數量

## 執行模式

### 預覽模式

在預覽模式（`mode="preview"`）中，工具：
- 顯示將進行的變更，而不修改檔案
- 根據 `output_style` 輸出格式化內容
- 將預覽資訊記錄到記錄器
- 不寫入任何檔案

### 套用模式

在套用模式（`mode="apply"`）中，工具：
- 實際使用替換修改檔案
- 將變更寫入目標檔案
- 如果指定了 `output_file`，可以寫入不同的輸出檔案
- 傳回已修改檔案的摘要

## 輸出樣式

### 預設樣式

傳回完整的修改檔案內容：

```python
response = tool.execute(
    file="./src/main.py",
    search="old_code",
    replace="new_code",
    output_style="default"
)
```

### Git Diff 樣式

傳回 git diff 格式以便檢視：

```diff
diff --git a/src/main.py b/src/main.py
@@ -10,1 +10,1 @@
-old_code
+new_code
```

### Git Conflict 樣式

傳回 git conflict 標記以便 VS Code 渲染：

```
<<<<<<< HEAD
old_code
=======
new_code
>>>>>>> incoming
```

## 匹配行為

### 單行匹配

匹配精確的行內容（去除空白後）：

```python
# 匹配："  import os  "（空白被去除）
search="import os"
```

### 多行匹配

精確匹配連續的行：

```python
# 匹配連續的行：
search="line1\nline2\nline3"
```

### 大小寫敏感性

當 `case_sensitive=False` 時，匹配不區分大小寫：

```python
# 匹配："Python"、"python"、"PYTHON"
search="Python"
case_sensitive=False
```

## 最佳實踐

1. **先使用預覽**：在套用前始終預覽變更，特別是批量替換
2. **在單一檔案上測試**：在套用到目錄前在單一檔案上測試模式
3. **使用行範圍**：如果可能，使用 `start_line` 和 `end_line` 縮小替換範圍
4. **檢查匹配**：檢視 `file_responses` 以驗證找到預期的匹配
5. **備份重要檔案**：在套用大型替換前建立備份
6. **使用 Git Diff 樣式**：使用 `git_diff` 輸出樣式檢視變更

## 錯誤處理

工具處理各種錯誤情況：

- **檔案未找到**：如果目標檔案或目錄不存在則傳回錯誤
- **無匹配**：傳回成功但 `file_responses` 清單為空
- **相同的搜尋/替換**：傳回成功並顯示「無需變更」訊息
- **檔案讀取錯誤**：記錄無法讀取的檔案警告，但繼續處理

## 實作詳情

- **精確匹配**：使用精確字串匹配（非正則表達式）以進行精確控制
- **逐行處理**：逐行處理檔案以準確追蹤行號
- **多行支援**：透過匹配連續行處理多行模式
- **替換順序**：從下到上套用替換以維持行號

## 相關文件

- 參閱 [base.md](base.md) 了解架構詳情

