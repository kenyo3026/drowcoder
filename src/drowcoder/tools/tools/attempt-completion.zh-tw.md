# 嘗試完成工具

## 概述

`attempt_completion` 工具是一個特殊用途的工具，用於向代理發出停止迭代並將任務標記為完成的信號。此工具對於控制代理的持續迭代迴圈至關重要。

## 目的

**[完成信號]** 此工具停止代理迭代迴圈並將任務標記為完成。

drowcoder 代理以持續迭代模式運作，這意味著它將持續工作直到明確告知停止。此工具提供該明確的停止信號。

## 何時使用

在以下情況呼叫此工具：
- 所有使用者請求的任務都已完成
- 實作已驗證並正常運作
- 沒有剩餘的任務或未解決的問題需要處理

**重要**：代理將持續迭代，直到呼叫此工具（最多 max_iterations）。僅提供文字摘要不足以停止 - 您必須明確呼叫此工具。

## 參數

### 必要參數

- **`result`** (string)：簡要描述已完成的工作以及為什麼認為任務已完成。

## 使用範例

```python
from drowcoder.tools import AttemptCompletionTool

tool = AttemptCompletionTool()

response = tool.execute(
    result="成功實作用戶認證系統，包含登入、登出和會話管理功能。所有測試通過。"
)
```

## 回應格式

工具傳回一個 `ToolResponse`，包含：

- **`success`**：如果成功發出完成信號則為 `True`
- **`content`**：確認訊息：「任務成功完成：{result}」
- **`error`**：成功時為 `None`，失敗時為錯誤訊息

## 實作詳情

- **最簡單的工具**：這是系統中最簡單的工具，僅作為完成信號
- **無副作用**：工具不執行任何檔案操作或系統變更
- **回呼支援**：如果已配置，會觸發「task_completed」回呼事件

## 整合

此工具由代理的 `_is_task_completed()` 方法偵測，該方法檢查 `attempt_completion` 工具呼叫以確定何時停止迭代。

偵測邏輯簡單且易於維護：

```python
def _is_task_completed(self, message) -> bool:
    """
    檢查代理是否已將任務標記為完成。

    如果呼叫了 attempt_completion 工具則傳回 True。
    """
    if not hasattr(message, 'tool_calls') or not message.tool_calls:
        return False

    return any(
        tool_call.function.name == 'attempt_completion'
        for tool_call in message.tool_calls
    )
```

## 架構與設計理念

### 設計原則

完成機制設計遵循幾個關鍵原則：

#### 1. 完全解耦

- 系統提示從不提及特定工具名稱
- 工具可以重新命名而不更改提示
- 可以無縫新增新的完成工具

#### 2. 自我文件化

- 工具描述承載知識
- LLM 從工具描述中學習，而非從提示中學習
- 更易於維護和擴展

#### 3. 標準合規

我們使用**標準 OpenAI 工具格式**，不使用自訂元資料，因為：

- **標準合規**：保持與 OpenAI API 規格的相容性
- **簡單性**：更易於理解和維護
- **自我文件化**：帶有 `[COMPLETION SIGNAL]` 標記的工具描述已足夠
- **靈活性**：如果需要，可以輕鬆擴展偵測邏輯，而無需更改工具格式

### 分層架構

完成機制遵循三層架構：

```
┌─────────────────────────────────────┐
│  系統提示層                         │
│  - 通用完成概念                     │
│  - 迭代政策                         │
│  - 行為準則                         │
│  - 不提及特定工具名稱                │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│  工具描述層                         │
│  - 特定工具功能                      │
│  - [COMPLETION SIGNAL] 標記         │
│  - 自我文件化說明                    │
│  - 標準 OpenAI 格式                 │
└─────────────────────────────────────┘
            ↓
┌─────────────────────────────────────┐
│  程式碼層                           │
│  - 簡單的基於名稱的偵測              │
│  - 清晰且易於維護                   │
│  - 需要時易於擴展                   │
└─────────────────────────────────────┘
```

### 可擴展性

要新增另一個完成工具（例如 `task_done`），只需：

1. 建立帶有 `[COMPLETION SIGNAL]` 標記的工具 YAML
2. 更新 `_is_task_completed()` 以檢查新工具名稱：

```python
# 在 agent.py 中
def _is_task_completed(self, message) -> bool:
    if not hasattr(message, 'tool_calls') or not message.tool_calls:
        return False

    completion_tools = ['attempt_completion', 'task_done']  # 在此新增新工具
    return any(
        tool_call.function.name in completion_tools
        for tool_call in message.tool_calls
    )
```

**此方法的優點**：
- ✅ 不需要自訂元資料（OpenAI 標準格式）
- ✅ 系統提示保持通用
- ✅ 需要時易於擴展

### 關鍵設計決策

1. **簡單的基於名稱的偵測**：直接工具名稱檢查清晰且易於維護
2. **標準格式**：僅使用 OpenAI 工具格式（無自訂元資料）
3. **自包含工具描述**：工具描述包含所有必要資訊
4. **通用系統提示**：系統提示從不提及特定工具名稱

## 最佳實踐

1. **完成時總是呼叫**：永遠不要僅依賴文字摘要 - 總是呼叫此工具
2. **提供清晰的結果**：在 `result` 參數中包含簡潔但描述性的摘要
3. **完成前驗證**：在呼叫前確保所有任務實際已完成
4. **使用適當的時機**：在驗證後呼叫，而非之前

## 相關文件

- 參閱 [base.md](base.md) 了解架構詳情

