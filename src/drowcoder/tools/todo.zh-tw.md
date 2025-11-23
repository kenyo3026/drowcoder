# 待辦事項工具

## 概述

`todo` 工具為編碼會話提供全面的任務管理系統。它支援帶有狀態追蹤的結構化待辦事項、合併和替換操作，以及具有自動檢查點管理的持久化儲存。

## 功能

- **結構化待辦事項**：帶有 id、content 和 status 欄位的待辦事項
- **狀態管理**：追蹤任務的 pending、in_progress、completed 和 cancelled 狀態
- **合併操作**：更新現有待辦事項或新增新的待辦事項
- **持久化儲存**：具有 JSON 儲存的自動檢查點管理
- **驗證**：內建待辦事項結構和狀態值驗證

## 參數

### 必要參數

- **`merge`** (bool)：是否與現有待辦事項合併（`True`）或替換它們（`False`）
- **`todos`** (List[Dict])：待辦事項陣列，每個包含：
  - **`id`** (string)：待辦事項的唯一識別碼
  - **`content`** (string)：待辦事項的描述/內容
  - **`status`** (string)：當前狀態 - 其中之一：`"pending"`、`"in_progress"`、`"completed"`、`"cancelled"`

### 可選參數

- **`as_type`**：輸出格式類型（預設：`PRETTY_STR`）
- **`filter_empty_fields`** (bool)：過濾輸出中的空欄位（預設：True）
- **`filter_metadata_fields`** (bool)：過濾元資料欄位（預設：False）

## 待辦事項狀態類型

- **`pending`**：尚未開始
- **`in_progress`**：目前正在進行
- **`completed`**：成功完成
- **`cancelled`**：不再需要

## 使用範例

### 建立初始待辦事項清單

```python
from drowcoder.tools import TodoTool

tool = TodoTool(checkpoint="./checkpoints")

response = tool.execute(
    merge=False,  # 替換任何現有的待辦事項
    todos=[
        {"id": "1", "content": "實作用戶認證", "status": "in_progress"},
        {"id": "2", "content": "新增密碼重設功能", "status": "pending"},
        {"id": "3", "content": "編寫單元測試", "status": "pending"}
    ]
)
```

### 更新待辦事項狀態（合併）

```python
response = tool.execute(
    merge=True,  # 與現有待辦事項合併
    todos=[
        {"id": "1", "content": "實作用戶認證", "status": "completed"},
        {"id": "2", "content": "新增密碼重設功能", "status": "in_progress"}
    ]
)
```

### 新增新待辦事項（合併）

```python
response = tool.execute(
    merge=True,
    todos=[
        {"id": "4", "content": "更新文件", "status": "pending"},
        {"id": "5", "content": "部署到預備環境", "status": "pending"}
    ]
)
```

### 替換所有待辦事項

```python
response = tool.execute(
    merge=False,  # 替換所有現有的待辦事項
    todos=[
        {"id": "1", "content": "新任務 1", "status": "pending"},
        {"id": "2", "content": "新任務 2", "status": "pending"}
    ]
)
```

## 回應格式

工具傳回一個 `TodoToolResponse`，包含：

- **`success`**：如果待辦事項更新成功則為 `True`
- **`content`**：帶有指導的成功訊息
- **`error`**：如果更新失敗則為錯誤訊息
- **`todos`**：`TodoItem` 物件清單（更新後的所有待辦事項）
- **`metadata`**：`TodoToolResponseMetadata`，包含：
  - `checkpoint_path`：檢查點檔案路徑
  - `merge`：待辦事項是合併還是替換

## 合併與替換行為

### 合併模式（`merge=True`）

- 使用匹配的 ID 更新現有待辦事項
- 新增不存在的新待辦事項
- 保留不在更新清單中的現有待辦事項
- 維持現有待辦事項的順序

### 替換模式（`merge=False`）

- 用新清單替換所有現有待辦事項
- 不在新清單中的先前待辦事項將被移除
- 在開始全新的任務清單時使用

## 最佳實踐

### 何時使用此工具

主動使用於：
1. 複雜的多步驟任務（3+ 個不同步驟）
2. 需要仔細規劃的非平凡任務
3. 使用者明確請求待辦事項清單
4. 使用者提供的多個任務
5. 收到新指令後 - 將需求捕獲為待辦事項
6. 完成任務後 - 標記完成並新增後續任務
7. 開始新任務時 - 標記為 in_progress

### 何時不使用

跳過用於：
1. 單一、直接的任務
2. 沒有組織效益的平凡任務
3. 可在 < 3 個簡單步驟內完成的任務
4. 純粹的對話/資訊請求
5. 操作動作（linting、測試、搜尋程式碼庫）

### 任務管理準則

1. **狀態更新**：在您工作時即時更新狀態
2. **立即標記完成**：完成後立即將任務標記為已完成
3. **一次進行中**：一次只有一個任務處於 in_progress 狀態
4. **開始前完成**：在開始新任務前完成當前任務
5. **特定任務**：建立特定、可操作的待辦事項
6. **分解複雜任務**：將複雜任務分解為可管理的步驟

## 初始化需求

`TodoTool` 需要在初始化期間提供 `checkpoint` 路徑：

```python
tool = TodoTool(checkpoint="./checkpoints")
```

檢查點路徑用於在 `todos.json` 檔案中儲存待辦事項。

## 驗證

工具驗證：
- 待辦事項必須是至少包含 2 個項目的清單
- 每個待辦事項必須是字典
- 必要欄位：`id`、`content`、`status`
- 所有欄位必須是字串
- 狀態必須是有效的狀態值之一

## 錯誤處理

工具處理各種錯誤情況：

- **無效結構**：如果待辦事項不符合要求則傳回錯誤
- **無效狀態**：如果狀態值無效則傳回錯誤
- **檢查點錯誤**：如果檢查點檔案操作失敗則傳回錯誤
- **JSON 錯誤**：如果檢查點檔案包含無效 JSON 則傳回錯誤

## 實作詳情

- **檢查點儲存**：待辦事項儲存在 `{checkpoint}/todos.json`
- **JSON 格式**：待辦事項序列化為帶有縮排的 JSON
- **基於 ID 的合併**：合併基於待辦事項 ID 匹配
- **順序保留**：合併期間保留現有待辦事項順序
- **回呼支援**：在待辦事項更新時觸發回呼事件

## 相關文件

- 參閱 [base.md](base.md) 了解架構詳情

