# 配置管理

## 概述

`config` 模組為 drowcoder 提供配置檔案管理工具。它包括用於編輯、顯示和驗證配置檔案的工具，以及基於平台的編輯器選擇。

## 功能

- **配置檔案操作**：編輯、顯示和驗證配置檔案
- **基於平台的編輯器選擇**：根據平台和環境自動選擇適當的編輯器
- **配置驗證**：驗證 YAML 語法和必要欄位
- **CLI 整合**：與命令列介面無縫整合

## 配置命令

### 編輯命令

在預設編輯器中開啟配置檔案。

```bash
drowcoder config edit
drowcoder config edit --config ./custom_config.yaml
```

**行為**：
- 檢查配置檔案是否存在，如果缺失則提示建立
- 在適合平台的編輯器中開啟檔案
- 尊重 `EDITOR` 和 `VISUAL` 環境變數

### 顯示命令

顯示當前配置檔案的內容。

```bash
drowcoder config show
drowcoder config show --config ./custom_config.yaml
```

**輸出**：將完整配置檔案內容列印到 stdout。

### 驗證命令

驗證配置檔案的結構和必要欄位。

```bash
drowcoder config validate
drowcoder config validate --config ./custom_config.yaml
```

**驗證檢查**：
- YAML 語法有效性
- 根必須是字典
- `models` 區段必須存在且為非空清單
- 每個模型必須有 `model` 和 `api_key` 欄位

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
```

### ConfigMain

主要配置管理類別。

#### `edit(config_path: Union[str, Path]) -> int`

在編輯器中開啟配置檔案。

**參數**：
- **`config_path`** (Union[str, Path])：配置檔案路徑

**傳回**：退出代碼（0 表示成功，1 表示失敗）

**行為**：
- 如果配置檔案不存在則建立（需使用者確認）
- 在首選編輯器中開啟檔案
- 傳回編輯器程序的退出代碼

**範例**：
```python
from drowcoder.config import ConfigMain

exit_code = ConfigMain.edit('./config.yaml')
```

#### `show(config_path: Union[str, Path]) -> int`

顯示當前配置檔案內容。

**參數**：
- **`config_path`** (Union[str, Path])：配置檔案路徑

**傳回**：退出代碼（0 表示成功，1 表示失敗）

**範例**：
```python
from drowcoder.config import ConfigMain

exit_code = ConfigMain.show('./config.yaml')
```

#### `validate(config_path: Union[str, Path]) -> int`

驗證配置檔案。

**參數**：
- **`config_path`** (Union[str, Path])：配置檔案路徑

**傳回**：退出代碼（0 表示有效，1 表示無效）

**驗證規則**：
- 檔案必須存在
- 必須是有效的 YAML
- 根必須是字典
- 必須有 `models` 區段
- `models` 必須是非空清單
- 每個模型必須有：
  - `model` 欄位（模型識別碼）
  - `api_key` 欄位（API 金鑰）

**範例**：
```python
from drowcoder.config import ConfigMain

exit_code = ConfigMain.validate('./config.yaml')
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

## 配置檔案格式

### 基本結構

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

### 必要欄位

- **根層級**：必須是字典
- **`models`**：必須是非空清單
- **每個模型**：
  - `model`：模型識別碼（必要）
  - `api_key`：API 金鑰（必要）

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

# 顯示配置
drowcoder config show

# 驗證配置
drowcoder config validate

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

編輯不存在的檔案時：
- 提示使用者建立檔案
- 如果使用者確認則建立檔案
- 如果使用者拒絕則傳回錯誤代碼

### 編輯器未找到

如果找不到指定的編輯器：
- 列印錯誤訊息
- 建議設定 `EDITOR` 環境變數
- 傳回錯誤代碼

### 驗證錯誤

驗證提供清晰的錯誤訊息：
- ❌ 無效的 YAML 語法
- ❌ 缺少必要欄位
- ❌ 無效的結構
- ✅ 有效配置（包含模型數量）

## 最佳實踐

1. **使用環境變數**：設定 `EDITOR` 或 `VISUAL` 以保持一致的編輯器選擇
2. **使用前驗證**：在執行代理前始終驗證配置
3. **版本控制**：考慮將 API 金鑰排除在版本控制之外
4. **使用描述性名稱**：使用有意義的模型名稱以便識別
5. **定期驗證**：在進行變更後驗證配置

## 相關文件

- 參閱 [model.md](model.md) 了解模型配置處理
- 參閱 [checkpoint.md](checkpoint.md) 了解檢查點系統

