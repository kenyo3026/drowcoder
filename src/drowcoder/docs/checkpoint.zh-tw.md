# 檢查點系統

## 概述

`Checkpoint` 類別為 drowcoder 代理提供全面的檢查點管理系統。它能夠持久化儲存代理狀態，包括配置、訊息、日誌和待辦事項，允許會話恢復和狀態追蹤。

## 功能

- **多種儲存類型**：支援 JSON、文字和結構化資料儲存
- **自動目錄管理**：建立和管理檢查點目錄
- **上下文感知儲存**：不同資料類型使用不同的儲存類型（dict、list、text）
- **持久化**：所有代理狀態都可以儲存和恢復
- **上下文管理器支援**：可作為上下文管理器使用，用於自動清理

## 檢查點結構

檢查點目錄包含以下檔案：

```
checkpoint_root/
├── info.json          # 系統和平台資訊
├── config.json        # 代理配置
├── logging.log        # 文字日誌檔案
├── messages.json      # 處理過的訊息（清單）
├── raw_messages.json  # 原始訊息（清單）
└── todos.json         # 待辦事項清單（清單）
```

## 基本使用

### 建立檢查點

```python
from drowcoder import Checkpoint

# 使用預設名稱建立檢查點（基於時間戳記）
checkpoint = Checkpoint()

# 使用自訂路徑建立檢查點
checkpoint = Checkpoint(root='./my_checkpoint')

# 如果存在則不重新初始化來建立檢查點
checkpoint = Checkpoint(
    root='./my_checkpoint',
    force_reinit_if_existence=False
)
```

### 作為上下文管理器使用

```python
with Checkpoint(root='./session') as checkpoint:
    checkpoint.punch_info({'custom_field': 'value'})
    checkpoint.punch_log('會話已開始')
    # 檢查點會自動管理
```

## 檢查點元件

### CheckpointInfo

儲存系統和平台資訊，自動包含時間戳記。

```python
checkpoint.info.punch({
    'custom_info': 'value',
    'version': '1.0.0'
})
```

**預設欄位**：
- `create_datetime`：建立時間戳記
- 來自 `platform.uname()` 的平台資訊

**儲存**：JSON 檔案（`info.json`）

### CheckpointConfig

儲存代理配置。

```python
checkpoint.config.punch({
    'model': 'gpt-4',
    'temperature': 0.7
})
```

**儲存**：JSON 檔案（`config.json`）

### CheckpointLogs

儲存基於文字的日誌條目。

```python
# 附加日誌條目
checkpoint.punch_log('處理已開始')

# 或直接使用
checkpoint.logs.punch('另一個日誌條目', mode='a')
```

**儲存**：文字檔案（`logging.log`）

**模式**：
- `'a'` 或 `TxtPunchMode.append`：附加到檔案
- `'w'` 或 `TxtPunchMode.write`：覆寫檔案

### CheckpointMessages

儲存處理過的訊息（清單格式）。

```python
checkpoint.punch_message({
    'role': 'user',
    'content': 'Hello'
})
```

**儲存**：JSON 檔案（`messages.json`）

### CheckpointRawMessages

儲存原始訊息（清單格式）。

```python
checkpoint.punch_raw_message({
    'role': 'assistant',
    'content': 'Response'
})
```

**儲存**：JSON 檔案（`raw_messages.json`）

### CheckpointToDosList

儲存待辦事項（清單格式）。

```python
checkpoint.punch_todos({
    'id': '1',
    'content': '任務描述',
    'status': 'pending'
})
```

**儲存**：JSON 檔案（`todos.json`）

## 基礎類別

檢查點系統使用多個基礎類別來處理不同的儲存類型：

### CheckpointTxtBase

文字檔案儲存的基礎類別。

```python
@dataclass
class CheckpointTxtBase:
    path: str
    context: Optional[str] = None

    def punch(self, context: str, mode: Union[str, TxtPunchMode]='a'):
        # 附加或寫入文字到檔案
```

### CheckpointDictBase

字典儲存的基礎類別（JSON）。

```python
@dataclass
class CheckpointDictBase:
    path: str
    context: Dict[str, Any] = field(default_factory=dict)

    def punch(self, context: Dict[str, Any]):
        # 更新字典並儲存為 JSON
```

### CheckpointListBase

清單儲存的基礎類別（JSON）。

```python
@dataclass
class CheckpointListBase:
    path: str
    context: List[Any] = field(default_factory=list)

    def punch(self, context: Any):
        # 附加到清單並儲存為 JSON
```

### CheckpointJsonBase

根據上下文類型自動建立 `CheckpointDictBase` 或 `CheckpointListBase` 的工廠類別。

```python
# 自動為 dict 建立 CheckpointDictBase
checkpoint = CheckpointJsonBase('path.json', {'key': 'value'})

# 自動為 list 建立 CheckpointListBase
checkpoint = CheckpointJsonBase('path.json', [1, 2, 3])
```

## API 參考

### Checkpoint 類別

#### `__init__(root=None, force_reinit_if_existence=True, logger=None)`

初始化檢查點。

**參數**：
- **`root`** (str, 可選)：檢查點目錄路徑。如果為 `None`，使用基於時間戳記的名稱
- **`force_reinit_if_existence`** (bool)：如果為 `True`，在建立前移除現有目錄（預設：`True`）
- **`logger`** (Logger, 可選)：用於檢查點操作的記錄器實例

**屬性**：
- `checkpoint_root` (Path)：檢查點目錄路徑
- `info` (CheckpointInfo)：系統資訊儲存
- `config` (CheckpointConfig)：配置儲存
- `logs` (CheckpointLogs)：日誌檔案儲存
- `messages` (CheckpointMessages)：處理過的訊息儲存
- `raw_messages` (CheckpointRawMessages)：原始訊息儲存
- `todos` (CheckpointToDosList)：待辦事項清單儲存

#### `init_checkpoint(root=None, force_reinit_if_existence=True)`

初始化或重新初始化檢查點目錄。

**參數**：
- **`root`** (str, 可選)：檢查點目錄路徑
- **`force_reinit_if_existence`** (bool)：如果存在則移除現有目錄

#### `punch_info(*args, **kwargs)`

將資訊新增到 `info.json`。

```python
checkpoint.punch_info({'key': 'value'})
```

#### `punch_log(*args, **kwargs)`

將日誌條目新增到 `logging.log`。

```python
checkpoint.punch_log('日誌訊息', mode='a')
```

#### `punch_message(*args, **kwargs)`

將訊息新增到 `messages.json`。

```python
checkpoint.punch_message({'role': 'user', 'content': 'Hello'})
```

#### `punch_raw_message(*args, **kwargs)`

將原始訊息新增到 `raw_messages.json`。

```python
checkpoint.punch_raw_message({'role': 'assistant', 'content': 'Hi'})
```

#### `punch_todos(*args, **kwargs)`

將待辦事項新增到 `todos.json`。

```python
checkpoint.punch_todos({'id': '1', 'content': '任務', 'status': 'pending'})
```

## 使用範例

### 基本檢查點建立

```python
from drowcoder import Checkpoint

# 建立檢查點
checkpoint = Checkpoint(root='./my_session')

# 儲存配置
checkpoint.punch_config({
    'model': 'gpt-4',
    'temperature': 0.7,
    'max_tokens': 2000
})

# 記錄事件
checkpoint.punch_log('代理已初始化')
checkpoint.punch_log('處理使用者請求')

# 儲存訊息
checkpoint.punch_message({
    'role': 'user',
    'content': '什麼是 Python？'
})
```

### 會話恢復

```python
import json
from pathlib import Path
from drowcoder import Checkpoint

# 載入現有檢查點
checkpoint_path = Path('./previous_session')
if checkpoint_path.exists():
    checkpoint = Checkpoint(
        root=str(checkpoint_path),
        force_reinit_if_existence=False
    )

    # 載入先前的訊息
    with open(checkpoint.checkpoint_root / 'messages.json') as f:
        messages = json.load(f)

    # 從中斷處繼續
    print(f"恢復會話，包含 {len(messages)} 條訊息")
```

### 上下文管理器使用

```python
with Checkpoint(root='./session') as checkpoint:
    checkpoint.punch_info({'session_id': '12345'})
    checkpoint.punch_log('會話已開始')

    try:
        # 代理操作
        checkpoint.punch_message({'role': 'user', 'content': 'Hello'})
    except Exception as e:
        checkpoint.punch_log(f'發生錯誤：{e}')
        raise
```

### 自訂檢查點元件

```python
from drowcoder.checkpoint import CheckpointJsonBase, CheckpointTxtBase

# 建立自訂 JSON 檢查點
custom_json = CheckpointJsonBase(
    path='./custom.json',
    context={'custom': 'data'}
)
custom_json.punch({'new': 'value'})

# 建立自訂文字檢查點
custom_txt = CheckpointTxtBase(
    path='./custom.txt',
    context='初始內容'
)
custom_txt.punch('額外內容', mode='a')
```

## 與代理整合

檢查點系統自動與 `DrowAgent` 整合：

```python
from drowcoder import DrowAgent, Checkpoint

# 代理自動建立和使用檢查點
agent = DrowAgent(
    checkpoint='./agent_session',
    workspace='./project'
)

# 檢查點在內部用於儲存：
# - 系統訊息
# - 使用者/助理訊息
# - 工具呼叫和回應
# - 配置
```

## 錯誤處理

檢查點系統會針對各種失敗情況引發 `CheckpointError`：

```python
from drowcoder.checkpoint import CheckpointError, Checkpoint

try:
    checkpoint = Checkpoint(root='/invalid/path')
    checkpoint.punch_log('Test')
except CheckpointError as e:
    print(f"檢查點錯誤：{e}")
```

## 最佳實踐

1. **使用描述性路徑**：使用有意義的檢查點目錄名稱以便識別
2. **處理錯誤**：在 try-except 區塊中包裝檢查點操作
3. **定期清理**：定期清理舊的檢查點目錄
4. **上下文管理器**：使用上下文管理器進行自動資源管理
5. **分離檢查點**：為不同的會話或實驗使用不同的檢查點
6. **版本控制**：考慮將檢查點目錄排除在版本控制之外（使用 `.gitignore`）

## 檔案格式詳情

### JSON 檔案

所有 JSON 檔案使用：
- **縮排**：4 個空格
- **編碼**：UTF-8
- **ASCII**：`ensure_ascii=False`（支援 Unicode）

### 文字檔案

文字檔案使用：
- **編碼**：UTF-8
- **模式**：預設為附加（`'a'`），可覆寫（`'w'`）

## 相關文件

- 參閱 [../tools/base.md](../tools/base.md) 了解工具架構

