# 寫入工具

## 概述

`write` 工具提供進階檔案寫入功能，具有多種操作（建立、覆寫、附加、前置）、預覽/套用模式、多種輸出樣式（預設、git_diff、git_conflict）和全面的安全驗證。

## 功能

- **多種操作**：建立、覆寫、附加和前置模式
- **預覽模式**：在套用前安全預覽變更
- **多種輸出樣式**：預設、git diff 和 git conflict 格式
- **安全驗證**：對潛在問題的全面檢查
- **備份支援**：覆寫前自動建立備份
- **目錄建立**：自動建立父目錄
- **權限保留**：選項保留檔案權限

## 參數

### 必要參數

- **`file_path`** (string | Path)：要寫入的目標檔案路徑
- **`content`** (string)：要寫入檔案的內容

### 可選參數

- **`mode`** (string)：執行模式 - `"preview"` 或 `"apply"`（預設：`"apply"`）
- **`output_style`** (string)：輸出樣式 - `"default"`、`"git_diff"` 或 `"git_conflict"`（預設：`"default"`）
- **`operation`** (string)：寫入操作類型 - `"create"`、`"overwrite"`、`"append"` 或 `"prepend"`（預設：`"overwrite"`）
- **`output_file`** (string | Path)：可選的輸出檔案路徑（用於套用模式）
- **`encoding`** (string)：文字編碼（預設：`"utf-8"`）
- **`backup`** (bool)：是否在覆寫前建立備份（預設：True）
- **`create_dirs`** (bool)：如果父目錄不存在是否建立它們（預設：True）
- **`preserve_permissions`** (bool)：是否保留檔案權限（預設：True）

## 寫入操作

### 建立

建立新檔案。如果檔案已存在則失敗。

```python
from drowcoder.tools import WriteTool

tool = WriteTool()

response = tool.execute(
    file_path="./new_file.txt",
    content="新檔案內容",
    operation="create"
)
```

### 覆寫

替換整個檔案內容（預設操作）。

```python
response = tool.execute(
    file_path="./existing_file.txt",
    content="新內容",
    operation="overwrite"
)
```

### 附加

將內容新增到檔案末尾。

```python
response = tool.execute(
    file_path="./log.txt",
    content="新日誌條目",
    operation="append"
)
```

### 前置

將內容新增到檔案開頭。

```python
response = tool.execute(
    file_path="./config.py",
    content="# 更新的配置\n",
    operation="prepend"
)
```

## 執行模式

### 預覽模式

顯示將進行的變更而不修改檔案：

```python
response = tool.execute(
    file_path="./src/main.py",
    content="新內容",
    mode="preview",
    output_style="git_diff"
)
```

### 套用模式

實際將變更寫入檔案：

```python
response = tool.execute(
    file_path="./src/main.py",
    content="新內容",
    mode="apply"
)
```

## 輸出樣式

### 預設樣式

傳回完整的檔案內容：

```python
response = tool.execute(
    file_path="./file.txt",
    content="內容",
    output_style="default"
)
```

### Git Diff 樣式

傳回 git diff 格式以便檢視：

```diff
diff --git a/file.txt b/file.txt
--- a/file.txt
+++ b/file.txt
@@ -1,1 +1,1 @@
-舊內容
+新內容
```

### Git Conflict 樣式

傳回 git conflict 標記以便 VS Code 渲染：

```
<<<<<<< HEAD
舊內容
=======
新內容
>>>>>>> incoming
```

## 使用範例

### 建立新檔案

```python
response = tool.execute(
    file_path="./src/new_module.py",
    content="def hello():\n    print('Hello')\n",
    operation="create",
    mode="apply"
)
```

### 帶備份的覆寫

```python
response = tool.execute(
    file_path="./config.yaml",
    content="新配置",
    operation="overwrite",
    backup=True,  # 自動建立備份
    mode="apply"
)
```

### 附加到日誌檔案

```python
response = tool.execute(
    file_path="./app.log",
    content="[INFO] 應用程式已啟動\n",
    operation="append",
    mode="apply"
)
```

### 預覽變更

```python
response = tool.execute(
    file_path="./src/main.py",
    content="更新的程式碼",
    mode="preview",
    output_style="git_diff"
)
```

## 回應格式

工具傳回一個 `WriteToolResponse`，包含：

- **`success`**：如果寫入操作成功完成則為 `True`
- **`content`**：摘要訊息或格式化輸出（取決於模式）
- **`error`**：如果操作失敗則為錯誤訊息
- **`file_responses`**：`FileResponse` 物件清單，每個包含：
  - `file_path`：處理的檔案路徑
  - `change`：帶有原始/新內容的 `FileChange` 物件
  - `success`：檔案操作是否成功
  - `error`：如果操作失敗則為錯誤訊息
  - `backup_path`：備份檔案路徑（如果已建立）

## 安全功能

### 驗證警告

工具針對以下情況提供警告：
- 寫入當前目錄樹外
- 在現有檔案上進行 CREATE 操作
- 大型內容大小（>1MB）
- 大型行數（>10,000 行）
- 二進位內容偵測（null 位元組）
- 檔案權限問題

### 備份建立

當 `backup=True` 且覆寫現有檔案時：
- 修改前自動建立備份
- 備份檔案命名為 `{filename}.backup` 或 `{filename}.backup.{n}`
- 備份路徑包含在回應元資料中

### 目錄建立

當 `create_dirs=True` 時：
- 如果父目錄不存在則自動建立它們
- 確保在嘗試寫入前檔案路徑可寫入

## 最佳實踐

1. **先使用預覽**：在套用前始終預覽變更，特別是重要檔案
2. **啟用備份**：對覆寫操作保持 `backup=True`
3. **檢查警告**：在套用變更前檢視驗證警告
4. **使用適當的操作**：為您的使用案例選擇正確的操作類型
5. **處理大型檔案**：對非常大的檔案（>1MB）要謹慎
6. **驗證成功**：檢查 `success` 和 `file_responses` 以驗證操作

## 錯誤處理

工具處理各種錯誤情況：

- **檔案存在（CREATE）**：如果在建立操作期間檔案存在則傳回錯誤
- **無變更**：如果內容相同則傳回成功並顯示「無需變更」
- **權限錯誤**：如果檔案/目錄不可寫入則傳回錯誤
- **無效操作**：如果操作類型無效則傳回錯誤
- **無效模式/樣式**：如果模式或 output_style 無效則傳回錯誤

## 實作詳情

- **行尾正規化**：自動正規化行尾（`\r\n` → `\n`）
- **內容比較**：在寫入前檢查內容是否相同（用於覆寫）
- **原子操作**：在可能的情況下以原子方式執行檔案操作
- **編碼支援**：預設使用 UTF-8 編碼，可配置
- **回呼支援**：在寫入完成時觸發回呼事件

## 相關文件

- 參閱 [base.md](base.md) 了解架構詳情

