# 模型分發器

## 概述

`model` 模組為 drowcoder 代理提供模型配置分發功能。它根據模型的角色（chatcompletions 和 postcompletions）組織模型，並準備它們以與 LiteLLM 完成 API 一起使用。

## 功能

- **基於角色的分發**：根據模型的角色（chatcompletions、postcompletions）組織模型
- **配置轉換**：可選與 ConfigMorpher 整合以進行進階配置處理
- **靈活的角色指派**：支援簡單的角色字串和角色-任務字典
- **多重角色支援**：模型可以同時指派給多個角色

## 模型角色

### ChatCompletions 角色

指派給 `chatcompletions` 角色的模型用於主要代理對話和工具呼叫。

```yaml
models:
  - name: gemini
    model: gemini/gemini-2.5-flash
    roles:
      - chatcompletions
```

### PostCompletions 角色

指派給 `postcompletions` 角色的模型用於主完成後的後處理任務，例如檢視變更或產生摘要。

```yaml
models:
  - name: gemini
    model: gemini/gemini-2.5-flash
    roles:
      - postcompletions: "檢視 git diff 變更並將變更檢查點到 'gitdiff.md'"
```

## 使用方式

### 基本使用

```python
from drowcoder.model import ModelDispatcher

# 模型配置（可來自 YAML 或 JSON）
models_config = [
    {
        'name': 'gemini',
        'model': 'gemini/gemini-2.5-flash',
        'temperature': 0,
        'roles': ['chatcompletions', 'postcompletions']
    }
]

# 建立分發器
dispatcher = ModelDispatcher(models_config, morph=True)

# 依角色存取模型
chat_models = dispatcher.for_chatcompletions
post_models = dispatcher.for_postcompletions
```

### 使用 ConfigMorpher

```python
from config_morpher import ConfigMorpher
from drowcoder.model import ModelDispatcher
import litellm

# 載入配置（YAML 或 JSON）
config = ConfigMorpher.from_yaml('config.yaml')  # 或 from_json('config.json')
models_config = config.fetch('models')

# 建立帶轉換的分發器
dispatcher = ModelDispatcher(models_config, morph=True)

# 與 LiteLLM 一起使用
completion_kwargs = dispatcher.for_chatcompletions.morph(
    litellm.completion,
    start_from='models[0]'
)
```

### 角色指派範例

#### 簡單角色字串

```python
models = [
    {
        'name': 'model1',
        'model': 'gpt-4',
        'roles': ['chatcompletions']  # 簡單字串
    }
]
```

#### 帶任務的角色

```python
models = [
    {
        'name': 'model1',
        'model': 'gpt-4',
        'roles': [
            'chatcompletions',
            {'postcompletions': '檢視並摘要變更'}  # 帶任務的字典
        ]
    }
]
```

#### 多重角色

```python
models = [
    {
        'name': 'model1',
        'model': 'gpt-4',
        'roles': [
            'chatcompletions',
            'postcompletions'  # 同一模型用於兩個角色
        ]
    }
]
```

## API 參考

### ModelRoleType

模型角色類型的常數。

```python
@dataclass(frozen=True)
class ModelRoleType:
    chatcompletions: str = 'chatcompletions'
    postcompletions: str = 'postcompletions'
```

**常數**：
- `chatcompletions`：主要對話和工具呼叫的角色
- `postcompletions`：後處理任務的角色

### ModelDispatcher

用於根據角色組織模型的分發器類別。

#### `__init__(models: List[dict], morph: bool = True)`

初始化模型分發器。

**參數**：
- **`models`** (List[dict])：模型配置字典清單。每個模型應包含：
  - `name`：模型名稱識別碼
  - `model`：LiteLLM 的模型識別碼
  - `roles`：角色指派清單（字串或字典）
  - 其他模型特定配置（temperature、api_key 等）
- **`morph`** (bool)：如果為 `True`，將角色群組轉換為 ConfigMorpher 實例（預設：`True`）

**屬性**：
- `models`：原始模型清單
- `morph`：是否啟用轉換
- `for_chatcompletions`：指派給 chatcompletions 角色的模型（ConfigMorpher 或 dict）
- `for_postcompletions`：指派給 postcompletions 角色的模型（ConfigMorpher 或 dict）

#### `dispatch(morph: bool = True)`

將模型分發到其各自的角色群組。

**參數**：
- **`morph`** (bool)：如果為 `True`，將角色群組轉換為 ConfigMorpher 實例

**流程**：
1. 遍歷模型清單中的每個模型
2. 對於每個模型，檢查 `roles` 欄位
3. 對於角色清單中的每個角色：
   - 如果角色是字串：將模型指派給該角色
   - 如果角色是字典：提取角色名稱和任務，將模型與任務一起指派
4. 為每個角色指派建立模型的淺層副本
5. 將模型按角色分組到 `for_chatcompletions` 和 `for_postcompletions`
6. 如果 `morph=True`，可選將群組轉換為 ConfigMorpher 實例

## 配置格式

配置檔可以使用 YAML 或 JSON 格式，兩種格式支援相同的結構。

### YAML 配置範例

```yaml
models:
  - name: gemini
    api_key: YOUR_API_KEY
    model: gemini/gemini-2.5-flash
    temperature: 0
    roles:
      - chatcompletions
      - postcompletions: "檢視 git diff 變更並將變更檢查點到 'gitdiff.md'"
```

### 模型字典結構

```python
{
    'name': str,              # 模型名稱識別碼
    'model': str,             # LiteLLM 的模型識別碼
    'api_key': str,           # API 金鑰（可選）
    'temperature': float,     # 溫度設定（可選）
    'max_tokens': int,        # 最大 token 數（可選）
    'system_prompt': str,     # 系統提示（可選）
    'roles': [                # 角色指派清單
        str | dict            # 角色字串或角色-任務字典
    ]
}
```

## 與主模組整合

ModelDispatcher 在主執行流程中使用：

```python
from config_morpher import ConfigMorpher
from drowcoder.model import ModelDispatcher
import litellm

# 載入配置（YAML 或 JSON）
config_morpher = ConfigMorpher.from_yaml('config.yaml')  # 或 from_json('config.json')
models_config = config_morpher.fetch('models')

# 建立分發器
models = ModelDispatcher(models_config, morph=True)

# 準備 chatcompletions 的完成參數
completion_kwargs = models.for_chatcompletions.morph(
    litellm.completion,
    start_from='models[0]'
)

# 準備 postcompletions 的完成參數（如果有）
if models.for_postcompletions:
    postcompletion_kwargs = models.for_postcompletions.morph(
        litellm.completion,
        start_from='models[0]'
    )

    # 取得完成後任務
    postcompletion_task = models.for_postcompletions.fetch(
        'models[0].roles.postcompletions'
    )
```

## 角色指派邏輯

### 字串角色指派

當角色指定為字串時：

```python
roles: ['chatcompletions']
```

模型被指派給該角色，沒有關聯的任務。

### 字典角色指派

當角色指定為字典時：

```python
roles: [{'postcompletions': '任務描述'}]
```

模型被指派給角色（鍵），並帶有關聯的任務（值）。

### 多重角色指派

模型可以指派給多個角色：

```python
roles: [
    'chatcompletions',
    {'postcompletions': '檢視變更'}
]
```

這會為每個角色建立獨立的模型實例，允許相同的模型配置用於不同目的。

## 轉換行為

當 `morph=True`（預設）時，分發器將角色群組轉換為 `ConfigMorpher` 實例：

```python
dispatcher = ModelDispatcher(models, morph=True)

# 這些是 ConfigMorpher 實例
chat_models = dispatcher.for_chatcompletions  # ConfigMorpher
post_models = dispatcher.for_postcompletions  # ConfigMorpher

# 可以使用 ConfigMorpher 方法
completion_kwargs = chat_models.morph(litellm.completion, start_from='models[0]')
```

當 `morph=False` 時，角色群組保持為字典：

```python
dispatcher = ModelDispatcher(models, morph=False)

# 這些是字典
chat_models = dispatcher.for_chatcompletions  # dict
post_models = dispatcher.for_postcompletions  # dict
```

## 使用範例

### 單一模型，單一角色

```python
models = [
    {
        'name': 'gpt-4',
        'model': 'gpt-4',
        'roles': ['chatcompletions']
    }
]

dispatcher = ModelDispatcher(models)
# dispatcher.for_chatcompletions 包含模型
# dispatcher.for_postcompletions 為空
```

### 單一模型，多重角色

```python
models = [
    {
        'name': 'gemini',
        'model': 'gemini/gemini-2.5-flash',
        'roles': [
            'chatcompletions',
            {'postcompletions': '檢視變更'}
        ]
    }
]

dispatcher = ModelDispatcher(models)
# for_chatcompletions 和 for_postcompletions 都包含模型實例
```

### 多重模型，不同角色

```python
models = [
    {
        'name': 'gpt-4',
        'model': 'gpt-4',
        'roles': ['chatcompletions']
    },
    {
        'name': 'claude',
        'model': 'claude-3-opus',
        'roles': [{'postcompletions': '產生摘要'}]
    }
]

dispatcher = ModelDispatcher(models)
# for_chatcompletions 包含 gpt-4
# for_postcompletions 包含 claude
```

## 最佳實踐

1. **使用描述性名稱**：使用有意義的模型名稱以便識別
2. **需要時分離角色**：如果 chatcompletions 和 postcompletions 有不同的需求，使用不同的模型
3. **重用模型**：如果適當，同一模型可以指派給多個角色
4. **啟用轉換**：保持 `morph=True`（預設）以與 ConfigMorpher 和 LiteLLM 整合
5. **記錄任務**：使用 postcompletions 時，提供清晰的任務描述

## 相關文件

- 參閱 [checkpoint.md](checkpoint.md) 了解檢查點系統
- 參閱 [verbose.md](verbose.md) 了解詳細輸出系統

