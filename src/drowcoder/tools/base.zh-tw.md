# 基礎工具架構

## 概述

`base` 模組為 drowcoder 系統中的所有工具提供基礎架構。它定義抽象基礎類別、通用資料結構和統一介面，確保所有工具實作的一致性。

## 架構元件

### BaseTool（抽象基礎類別）

所有工具都繼承自 `BaseTool`，它提供：

- **統一初始化**：一致的配置和設定模式
- **標準介面**：通用的 `execute()` 方法簽名
- **回應處理**：內建支援多種輸出格式
- **日誌整合**：自動記錄器設定和管理
- **回呼支援**：工具操作的事件通知系統
- **驗證**：內建初始化狀態檢查

### ToolResponse

所有工具執行的標準回應格式：

```python
@dataclass
class ToolResponse:
    tool_name: Optional[str] = None
    success: Optional[bool] = None
    content: Any = None
    error: Optional[str] = None
    metadata: Optional[ToolResponseMetadata] = None
```

**回應欄位**：
- `tool_name`：產生回應的工具識別碼
- `success`：表示執行成功的布林值
- `content`：實際結果資料（類型因工具而異）
- `error`：如果執行失敗則為錯誤訊息
- `metadata`：額外的執行元資料

**輸出格式**：
- `INTACT`：原樣傳回回應物件
- `DICT`：轉換為字典
- `STR`：轉換為字串表示
- `PRETTY_STR`：轉換為格式化字串（預設）

### ToolConfig

所有工具的基礎配置：

```python
@dataclass
class ToolConfig:
    logger: Optional[logging.Logger] = None
    callback: Optional[Callable] = None
    checkpoint: Optional[Union[str, Path]] = None
```

**配置選項**：
- `logger`：自訂記錄器實例（如果未提供則自動建立）
- `callback`：在工具事件時呼叫的函數
- `checkpoint`：需要持久化的工具的根路徑

## 設計原則

### 1. 統一介面

所有工具實作相同的 `execute()` 方法簽名：

```python
def execute(
    self,
    as_type: Union[str, _IntactType] = ToolResponseType.PRETTY_STR,
    filter_empty_fields: bool = True,
    filter_metadata_fields: bool = True,
    **kwargs,
) -> ToolResponse:
```

### 2. 一致的錯誤處理

所有工具遵循相同的錯誤處理模式：
- 錯誤時傳回 `success=False` 的 `ToolResponse`
- 包含描述性錯誤訊息
- 適當記錄錯誤

### 3. 靈活的輸出格式化

工具透過 `as_type` 參數支援多種輸出格式：
- `INTACT`：用於程式化存取
- `DICT`：用於結構化資料處理
- `STR`：用於簡單字串輸出
- `PRETTY_STR`：用於人類可讀的格式化輸出

### 4. 可擴展性

工具可以擴展基礎類別以新增：
- 自訂回應元資料類別
- 工具特定的驗證邏輯
- 專業的初始化需求

## 使用模式

### 建立新工具

1. **繼承自 BaseTool**：
```python
class MyTool(BaseTool):
    name = 'my_tool'
```

2. **實作 execute() 方法**：
```python
def execute(self, **kwargs) -> Any:
    self._validate_initialized()
    dumping_kwargs = self._parse_dump_kwargs(locals())

    try:
        # 工具邏輯在此
        return MyToolResponse(
            success=True,
            content=result,
        ).dump(**dumping_kwargs)
    except Exception as e:
        return MyToolResponse(
            success=False,
            error=str(e),
        ).dump(**dumping_kwargs)
```

3. **定義自訂回應類別**（可選）：
```python
@dataclass
class MyToolResponse(ToolResponse):
    tool_name: str = 'my_tool'
    custom_field: Optional[str] = None
```

## 優點

- **一致性**：所有工具行為可預測
- **可維護性**：通用模式減少程式碼重複
- **可測試性**：統一介面簡化測試
- **可擴展性**：易於遵循既定模式新增新工具
- **類型安全**：資料類別提供結構和驗證

## 相關工具

drowcoder 系統中的所有工具都建立在此基礎上：
- `attempt_completion`：任務完成信號
- `execute`：命令執行
- `load`：檔案載入
- `search`：內容搜尋
- `search_and_replace`：文字替換
- `todo`：任務管理
- `write`：檔案寫入

