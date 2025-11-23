# 詳細輸出系統

## 概述

`verbose` 模組為 drowcoder 代理提供靈活的訊息輸出系統。它提供多種輸出樣式，從簡單文字到豐富的格式化顯示，允許使用者自訂代理訊息、工具呼叫和回應的顯示方式。

## 功能

- **多種輸出樣式**：四種不同的樣式（simple、compact、pretty、rich_pretty）
- **豐富格式化**：使用顏色、面板和結構化佈局增強視覺效果
- **工具呼叫視覺化**：使用巢狀顯示特殊處理工具呼叫
- **內容截斷**：自動截斷長內容，可配置限制
- **Markdown 支援**：自動 markdown 偵測和渲染
- **可擴展架構**：易於新增自訂詳細輸出實作

## 詳細輸出樣式

### Simple 樣式

最小輸出，列印原始訊息字典。

```python
from drowcoder import VerboserFactory

verboser = VerboserFactory.get('simple')
verboser.verbose_message({'role': 'user', 'content': 'Hello'})
```

**使用案例**：除錯或需要原始訊息資料時。

### Compact 樣式

最小輸出，帶有表情符號指示器和截斷內容。

```python
verboser = VerboserFactory.get('compact')
verboser.verbose_message({'role': 'assistant', 'content': 'Response...'})
```

**輸出範例**：
```
🤖 回應內容...
🔧 execute_cmd: 命令輸出...
```

**使用案例**：快速概覽，無需詳細格式化。

### Pretty 樣式

使用 ANSI 顏色代碼的格式化輸出和結構化佈局。

```python
verboser = VerboserFactory.get('pretty')
verboser.verbose_message({
    'role': 'assistant',
    'content': 'Hello!',
    'tool_calls': [...]
})
```

**功能**：
- 顏色編碼的角色（system、user、assistant、tool）
- 結構化函數呼叫格式化
- 內容截斷與長度指示器
- 可配置長度限制

**配置選項**：
- `max_content_length`：最大內容長度（預設：1000）
- `max_tool_result_length`：最大工具結果長度（預設：500）
- `max_arg_length`：最大參數長度（預設：100）
- `show_colors`：啟用/停用顏色（預設：True）

### Rich Pretty 樣式（預設）

使用 Rich 函式庫的增強格式化，具有進階視覺功能。

```python
verboser = VerboserFactory.get('rich_pretty')
verboser.verbose_message({
    'role': 'tool',
    'name': 'execute',
    'content': '命令輸出...'
})
```

**功能**：
- Rich 函式庫整合以進行進階格式化
- 巢狀工具呼叫顯示與樹狀結構
- 自動 markdown 渲染
- 程式碼的語法高亮
- 基於面板的佈局
- 工具呼叫關係的狀態追蹤

**配置選項**：
- `max_content_length`：最大內容長度（預設：1000）
- `max_tool_result_length`：最大工具結果長度（預設：500）
- `max_arg_length`：最大參數長度（預設：100）
- `console`：自訂 Rich Console 實例（可選）
- `show_nested`：啟用巢狀工具呼叫顯示（預設：True）
- `debug_mode`：啟用除錯日誌（預設：False）

## 使用方式

### 基本使用

```python
from drowcoder import VerboserFactory, VerboseStyle

# 使用預設樣式建立詳細輸出器
verboser = VerboserFactory.get()

# 使用特定樣式建立詳細輸出器
verboser = VerboserFactory.get('rich_pretty')

# 使用自訂配置建立詳細輸出器
verboser = VerboserFactory.get(
    'pretty',
    max_content_length=2000,
    show_colors=False
)
```

### 與代理一起使用

詳細輸出系統自動與 `DrowAgent` 整合：

```python
from drowcoder import DrowAgent, VerboseStyle

# 使用預設樣式（rich_pretty）
agent = DrowAgent(
    workspace='./project',
    verbose_style=VerboseStyle.RICH_PRETTY
)

# 使用 compact 樣式
agent = DrowAgent(
    workspace='./project',
    verbose_style='compact'
)

# 直接使用字串
agent = DrowAgent(
    workspace='./project',
    verbose_style='pretty'
)
```

### 自訂詳細輸出器配置

```python
from drowcoder import VerboserFactory
from rich.console import Console

# 建立自訂 Rich 控制台
custom_console = Console(force_terminal=True, width=120)

# 使用自訂控制台建立詳細輸出器
verboser = VerboserFactory.get(
    'rich_pretty',
    console=custom_console,
    max_content_length=5000,
    show_nested=True,
    debug_mode=True
)
```

## API 參考

### VerboseStyle

詳細輸出樣式值的常數。

```python
@dataclass(frozen=True)
class VerboseStyle:
    SIMPLE: str = 'simple'
    PRETTY: str = 'pretty'
    COMPACT: str = 'compact'
    RICH_PRETTY: str = 'rich_pretty'
```

**類別方法**：
- `get_values() -> List[str]`：取得所有可用的樣式值
- `is_valid(style: str) -> bool`：檢查樣式字串是否有效

### VerboserFactory

用於建立詳細輸出器實例的工廠類別。

#### `get(style: str = 'pretty', **kwargs) -> BaseMessageVerboser`

根據樣式建立詳細輸出器實例。

**參數**：
- **`style`** (str)：樣式名稱 - `'simple'`、`'compact'`、`'pretty'` 或 `'rich_pretty'`（預設：`'pretty'`）
- **`**kwargs`**：樣式特定的配置選項

**傳回**：`BaseMessageVerboser` 實例

**引發**：如果樣式未知則引發 `ValueError`

#### `get_available_styles() -> List[str]`

取得所有可用的詳細輸出器樣式名稱。

**傳回**：可用樣式字串清單

### BaseMessageVerboser

所有詳細輸出器的抽象基礎類別。

#### `verbose_message(message: Dict[str, Any]) -> None`

以詳細輸出器的格式顯示訊息。

**參數**：
- **`message`** (Dict[str, Any])：訊息字典，包含以下鍵：
  - `role`：訊息角色（`'system'`、`'user'`、`'assistant'`、`'tool'`）
  - `content`：訊息內容（字串）
  - `tool_calls`：工具呼叫清單（用於助理訊息）
  - `name`：工具名稱（用於工具訊息）
  - `tool_call_id`：工具呼叫 ID（用於工具訊息）
  - `arguments`：工具參數（用於工具訊息）

## 訊息格式範例

### 使用者訊息

```python
message = {
    'role': 'user',
    'content': '什麼是 Python？'
}
verboser.verbose_message(message)
```

### 帶工具呼叫的助理訊息

```python
message = {
    'role': 'assistant',
    'content': '我將搜尋關於 Python 的資訊。',
    'tool_calls': [
        {
            'id': 'call_123',
            'function': {
                'name': 'search',
                'arguments': '{"query": "Python programming"}'
            }
        }
    ]
}
verboser.verbose_message(message)
```

### 工具回應訊息

```python
message = {
    'role': 'tool',
    'tool_call_id': 'call_123',
    'name': 'search',
    'content': 'Python 是一種高階程式語言...',
    'captured_logs': '正在搜尋資料庫...\n找到 10 個結果'
}
verboser.verbose_message(message)
```

## 進階功能

### 巢狀工具呼叫顯示

`rich_pretty` 樣式自動將工具回應巢狀顯示在其對應的工具呼叫下：

```
└── ─── 🤖 Assistant ─────────────────────────────────────────────
    回應內容...

    └── ─── ⚡ Tool ─────────────────────────────────────────────
        Tool Call ID: call_123
        Function: search(query="Python")
        Result: 搜尋結果...
```

### Markdown 渲染

`rich_pretty` 樣式自動偵測並渲染 markdown 內容：

```python
message = {
    'role': 'assistant',
    'content': '''# Python 概述

Python 是一種**高階**程式語言。

## 功能
- 易於學習
- 強大的函式庫
- 優秀的社群
'''
}
verboser.verbose_message(message)
```

### 內容截斷

所有樣式都支援自動內容截斷：

```python
verboser = VerboserFactory.get(
    'pretty',
    max_content_length=100,  # 在 100 個字元處截斷
    max_tool_result_length=200
)
```

## 最佳實踐

1. **選擇適當的樣式**：
   - 使用 `simple` 進行除錯
   - 使用 `compact` 進行最小輸出
   - 使用 `pretty` 進行標準終端輸出
   - 使用 `rich_pretty` 進行增強的視覺體驗（預設）

2. **配置長度限制**：根據終端大小和需求調整截斷限制

3. **開發時使用 Rich Pretty**：`rich_pretty` 樣式提供最佳的視覺體驗，包含巢狀工具呼叫

4. **需要時停用顏色**：在不支援 ANSI 顏色的環境中設定 `show_colors=False`

5. **自訂控制台**：提供自訂 Rich Console 實例以進行進階格式化控制

## 與代理整合

詳細輸出系統完全與 `DrowAgent` 整合：

```python
from drowcoder import DrowAgent, VerboseStyle

agent = DrowAgent(
    workspace='./project',
    verbose_style=VerboseStyle.RICH_PRETTY  # 預設
)

# 訊息會自動使用配置的詳細輸出器顯示
agent.process("您的指令")
```

## 擴展系統

要建立自訂詳細輸出器：

```python
from drowcoder.verbose import BaseMessageVerboser

class CustomVerboser(BaseMessageVerboser):
    def verbose_message(self, message: Dict[str, Any]) -> None:
        # 您的自訂格式化邏輯
        role = message.get('role')
        content = message.get('content', '')
        print(f"[{role.upper()}] {content}")

# 使用自訂詳細輸出器
verboser = CustomVerboser()
verboser.verbose_message({'role': 'user', 'content': 'Hello'})
```

## 相關文件

- 參閱 [checkpoint.md](checkpoint.md) 了解檢查點系統
- 參閱 [../tools/base.md](../tools/base.md) 了解工具架構

