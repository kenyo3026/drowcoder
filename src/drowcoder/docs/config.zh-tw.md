# 配置管理

## 概述

`config` 模組提供配置檔案管理功能，讓你可以輕鬆編輯、查看和驗證配置檔。它會根據你的平台自動選擇合適的編輯器，並支援 YAML 和 JSON 兩種格式。

## 功能

- **配置檔案操作**：編輯、顯示、驗證和設定預設配置檔
- **多格式支援**：支援 YAML（`.yaml`、`.yml`）和 JSON（`.json`）格式
- **智慧編輯器選擇**：根據你的平台和環境自動選擇合適的編輯器
- **配置驗證**：驗證 YAML/JSON 語法和必要欄位
- **CLI 整合**：與命令列介面完美整合

## 配置命令

### 編輯命令

在預設編輯器中開啟配置檔，方便你直接編輯。

```bash
drowcoder config edit
drowcoder config edit --config ./custom_config.yaml
```

**行為**：
- 如果配置檔不存在，會詢問你是否要建立新檔
- 自動選擇適合你平台的編輯器
- 會優先使用 `EDITOR` 或 `VISUAL` 環境變數指定的編輯器

### 顯示命令

顯示配置檔的內容，方便你快速查看設定。

```bash
drowcoder config show                    # 顯示預設配置檔 (~/.drowcoder/config.yaml)
drowcoder config show --config ./custom_config.yaml
```

**輸出**：將完整的配置檔內容顯示在終端機上。

### 驗證命令

檢查配置檔的格式和必要欄位是否正確。支援 YAML 和 JSON 兩種格式。

```bash
drowcoder config validate
drowcoder config validate --config ./custom_config.yaml
drowcoder config validate --config ./custom_config.json
```

**驗證項目**：
- YAML/JSON 語法是否正確
- 根層級必須是字典格式
- `models` 區段必須存在且為非空清單
- 每個模型必須有 `model` 和 `api_key` 欄位

### 設定預設配置命令

將指定的配置檔內容複製到 `~/.drowcoder/config.yaml`，作為預設配置。支援 YAML 和 JSON 輸入檔。

```bash
drowcoder config set /path/to/config.yaml
drowcoder config set /path/to/config.json
```

**行為**：
- 讀取並驗證指定的配置檔（YAML 或 JSON 都可以）
- 將內容複製到 `~/.drowcoder/config.yaml`（統一儲存為 YAML 格式）
- 如果預設配置目錄不存在會自動建立
- 顯示清楚的成功或錯誤訊息

## API 參考

### Platform

用於平台識別的常數。

```python
@dataclass(frozen=True)
class Platform:
    WINDOWS: str = 'Windows'
    DARWIN: str = 'Darwin'
    LINUX: str = 'Linux'
```

**類別方法**：
- `get_default_editor() -> str`：取得平台特定的預設編輯器

### Editor

用於文字編輯器選擇的常數和工具。

```python
@dataclass(frozen=True)
class Editor:
    NOTEPAD: str = 'notepad'
    VIM: str = 'vim'
    NANO: str = 'nano'
```

**類別方法**：
- `get_preferred() -> str`：根據環境和平台取得首選編輯器

**優先順序**：
1. `EDITOR` 環境變數（主要）
2. `VISUAL` 環境變數（備用）
3. 平台特定的預設值

### ConfigCommand

配置命令類型的常數。

```python
@dataclass(frozen=True)
class ConfigCommand:
    EDIT: str = 'edit'
    SHOW: str = 'show'
    VALIDATE: str = 'validate'
    SET: str = 'set'
```

### ConfigMain

主要的配置管理類別，提供所有配置檔操作的 API。

#### `edit(config_path: Union[str, Path]) -> int`

在編輯器中開啟配置檔，方便你直接編輯。

**參數**：
- **`config_path`** (Union[str, Path])：配置檔路徑

**傳回**：退出代碼（0 表示成功，1 表示失敗）

**行為**：
- 如果配置檔不存在，會詢問你是否要建立新檔
- 在首選編輯器中開啟檔案
- 傳回編輯器程序的退出代碼

**範例**：
```python
from drowcoder.config import ConfigMain

exit_code = ConfigMain.edit('./config.yaml')
```

#### `show(config_path: Union[str, Path, None] = None) -> int`

顯示配置檔的內容。如果沒有指定路徑，會顯示預設配置檔 `~/.drowcoder/config.yaml`。

**參數**：
- **`config_path`** (Union[str, Path, None])：配置檔路徑（選填，預設為 `~/.drowcoder/config.yaml`）

**傳回**：退出代碼（0 表示成功，1 表示失敗）

**範例**：
```python
from drowcoder.config import ConfigMain

# 顯示預設配置檔
exit_code = ConfigMain.show()

# 顯示指定配置檔
exit_code = ConfigMain.show('./config.yaml')
```

#### `set(config_path: Union[str, Path]) -> int`

設定預設配置檔，將指定配置檔的內容複製到 `~/.drowcoder/config.yaml`。支援 YAML 和 JSON 輸入檔。

**參數**：
- **`config_path`** (Union[str, Path])：配置檔路徑（YAML 或 JSON）

**傳回**：退出代碼（0 表示成功，1 表示失敗）

**行為**：
- 檢查配置檔是否存在
- 讀取 YAML 或 JSON 格式的配置檔
- 驗證配置結構和必要欄位
- 將內容複製到 `~/.drowcoder/config.yaml`（統一儲存為 YAML 格式）
- 如果預設配置目錄不存在會自動建立

**範例**：
```python
from drowcoder.config import ConfigMain

# 從 YAML 檔設定預設配置
exit_code = ConfigMain.set('./config.yaml')

# 從 JSON 檔設定預設配置
exit_code = ConfigMain.set('./config.json')
```

#### `validate(config_path: Union[str, Path]) -> int`

驗證配置檔是否正確。支援 YAML 和 JSON 兩種格式。

**參數**：
- **`config_path`** (Union[str, Path])：配置檔路徑（YAML 或 JSON）

**傳回**：退出代碼（0 表示有效，1 表示無效）

**驗證規則**：
- 檔案必須存在
- 必須是有效的 YAML 或 JSON
- 根層級必須是字典
- 必須有 `models` 區段
- `models` 必須是非空清單
- 每個模型必須有：
  - `model` 欄位（模型識別碼）
  - `api_key` 欄位（API 金鑰）

**範例**：
```python
from drowcoder.config import ConfigMain

# 驗證 YAML 配置檔
exit_code = ConfigMain.validate('./config.yaml')

# 驗證 JSON 配置檔
exit_code = ConfigMain.validate('./config.json')

if exit_code == 0:
    print("配置有效！")
```

## 編輯器選擇

### 環境變數

編輯器選擇遵循 Unix 慣例：

1. **EDITOR**（主要）：最常見的環境變數
   ```bash
   export EDITOR=vim
   ```

2. **VISUAL**（備用）：替代環境變數
   ```bash
   export VISUAL=nano
   ```

3. **平台預設值**：回退到平台特定的預設值
   - Windows：`notepad`
   - macOS/Darwin：`vim`
   - Linux：`vim`

### 平台預設值

```python
from drowcoder.config import Platform

# 取得當前平台的預設編輯器
editor = Platform.get_default_editor()
# Windows: 'notepad'
# macOS/Linux: 'vim'
```

### 首選編輯器

```python
from drowcoder.config import Editor

# 取得首選編輯器（先檢查環境變數）
editor = Editor.get_preferred()
# 檢查順序：EDITOR -> VISUAL -> 平台預設值
```

## 配置檔格式

配置檔可以使用 YAML（`.yaml`、`.yml`）或 JSON（`.json`）格式撰寫，兩種格式支援相同的結構和欄位。

### 基本結構（YAML）

```yaml
models:
  - name: model_name
    api_key: YOUR_API_KEY
    model: model_identifier
    temperature: 0
    roles:
      - chatcompletions
      - postcompletions: "task description"
```

### 基本結構（JSON）

```json
{
  "models": [
    {
      "name": "model_name",
      "api_key": "YOUR_API_KEY",
      "model": "model_identifier",
      "temperature": 0,
      "roles": [
        "chatcompletions",
        "postcompletions: task description"
      ]
    }
  ]
}
```

### 必要欄位

- **根層級**：必須是字典格式
- **`models`**：必須是非空清單
- **每個模型**：
  - `model`：模型識別碼（必填）
  - `api_key`：API 金鑰（必填）

### 可選欄位

- `name`：模型名稱識別碼
- `temperature`：溫度設定
- `max_tokens`：最大 token 數
- `system_prompt`：系統提示
- `roles`：角色指派清單

## 使用範例

### 程式化使用

```python
from drowcoder.config import ConfigMain, ConfigCommand

# 編輯配置
ConfigMain.edit('./config.yaml')

# 顯示配置
ConfigMain.show('./config.yaml')

# 驗證配置
result = ConfigMain.validate('./config.yaml')
if result == 0:
    print("有效！")
else:
    print("配置無效")
```

### CLI 使用

```bash
# 編輯配置
drowcoder config edit

# 顯示配置（預設：~/.drowcoder/config.yaml）
drowcoder config show

# 顯示指定配置檔
drowcoder config show --config ./custom_config.yaml

# 驗證配置
drowcoder config validate

# 設定預設配置（將內容複製到 ~/.drowcoder/config.yaml）
drowcoder config set ./config.yaml
drowcoder config set ./config.json

# 使用自訂配置路徑
drowcoder config edit --config ./custom_config.yaml
```

### 自訂編輯器

```bash
# 透過環境變數設定編輯器
export EDITOR=code  # VS Code
drowcoder config edit

# 或使用 VISUAL
export VISUAL=nano
drowcoder config edit
```

## 與主模組整合

配置管理已整合到主 CLI：

```python
from drowcoder.config import ConfigMain, ConfigCommand

# 在 main.py 中
if args.command == 'config':
    if args.config_action == ConfigCommand.EDIT:
        return ConfigMain.edit(config_path)
    elif args.config_action == ConfigCommand.SHOW:
        return ConfigMain.show(config_path)
    elif args.config_action == ConfigCommand.VALIDATE:
        return ConfigMain.validate(config_path)
```

## 錯誤處理

### 檔案未找到

當你嘗試編輯不存在的檔案時：
- 會詢問你是否要建立新檔
- 如果你確認，就會自動建立檔案
- 如果你拒絕，會傳回錯誤代碼

### 編輯器未找到

如果找不到指定的編輯器：
- 會顯示錯誤訊息
- 建議你設定 `EDITOR` 環境變數
- 傳回錯誤代碼

### 驗證錯誤

驗證時會提供清楚的錯誤訊息：
- ❌ YAML/JSON 語法錯誤
- ❌ 缺少必要欄位
- ❌ 結構不符合規範
- ✅ 配置有效（會顯示模型數量）

## 最佳實踐

1. **設定環境變數**：設定 `EDITOR` 或 `VISUAL` 讓編輯器選擇更一致
2. **使用前先驗證**：執行代理前記得先驗證配置是否正確
3. **保護 API 金鑰**：不要把 API 金鑰提交到版本控制系統
4. **使用清楚的命名**：幫模型取個有意義的名稱，方便識別
5. **變更後驗證**：修改配置後記得驗證一下，確保格式正確

## 相關文件

- 查看 [model.md](model.md) 了解模型配置的詳細說明
- 查看 [checkpoint.md](checkpoint.md) 了解檢查點系統的運作方式

