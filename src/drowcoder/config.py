import os
import pathlib
import platform
import subprocess
import yaml
from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Platform:
    WINDOWS: str = 'Windows'
    DARWIN: str = 'Darwin'
    LINUX: str = 'Linux'

    @staticmethod
    def get_default_editor():
        """Get platform-specific default editor"""
        system = platform.system()
        if system == Platform.WINDOWS:
            return Editor.NOTEPAD
        elif system == Platform.DARWIN:
            return Editor.VIM
        else:  # Linux and others
            return Editor.VIM

@dataclass(frozen=True)
class Editor:
    NOTEPAD: str = 'notepad'
    VIM: str = 'vim'
    NANO: str = 'nano'

    @staticmethod
    def get_preferred():
        """Get the preferred text editor based on environment and platform

        Priority order (following Unix conventions):
        1. EDITOR environment variable (primary)
        2. VISUAL environment variable (fallback)
        3. Platform-specific default
        """
        # Check EDITOR first (most common)
        editor = os.environ.get('EDITOR')
        if editor:
            return editor

        # Check VISUAL for compatibility
        editor = os.environ.get('VISUAL')
        if editor:
            return editor

        # Fallback to platform default
        return Platform.get_default_editor()

@dataclass(frozen=True)
class ConfigCommand:
    EDIT     :str='edit'
    SHOW     :str='show'
    VALIDATE :str='validate'

class ConfigMain:
    """Configuration management class"""

    @staticmethod
    def edit(config_path: Union[str, pathlib.Path]):
        """Open config file in editor"""
        config_path = pathlib.Path(config_path).resolve()

        # Ensure config file exists
        if not config_path.exists():
            print(f"Config file not found: {config_path}")
            create = input("Create new config file? (y/N): ").strip().lower()
            if create in ['y', 'yes']:
                config_path.parent.mkdir(parents=True, exist_ok=True)
                config_path.touch()
                print(f"Created config file: {config_path}")
            else:
                return 1

        # Determine editor
        editor = Editor.get_preferred()

        print(f"Opening {config_path} with {editor}...")
        try:
            result = subprocess.run([editor, str(config_path)])
            return result.returncode
        except FileNotFoundError:
            print(f"Editor '{editor}' not found. Please set EDITOR environment variable.")
            return 1
        except Exception as e:
            print(f"Error opening editor: {e}")
            return 1

    @staticmethod
    def show(config_path: Union[str, pathlib.Path]):
        """Display current configuration"""
        config_path = pathlib.Path(config_path).resolve()

        if not config_path.exists():
            print(f"Config file not found: {config_path}")
            return 1

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"Configuration file: {config_path}")
            print("-" * 50)
            print(content)
            return 0
        except Exception as e:
            print(f"Error reading config file: {e}")
            return 1

    @staticmethod
    def validate(config_path: Union[str, pathlib.Path]):
        """Validate configuration file"""
        config_path = pathlib.Path(config_path).resolve()

        if not config_path.exists():
            print(f"Config file not found: {config_path}")
            return 1

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # Basic validation
            if not isinstance(config_data, dict):
                print("❌ Invalid config: Root must be a dictionary")
                return 1

            # Check required fields
            if 'models' not in config_data:
                print("❌ Invalid config: Missing 'models' section")
                return 1

            models = config_data['models']
            if not isinstance(models, list) or len(models) == 0:
                print("❌ Invalid config: 'models' must be a non-empty list")
                return 1

            # Validate each model
            for i, model in enumerate(models):
                if not isinstance(model, dict):
                    print(f"❌ Invalid config: Model {i} must be a dictionary")
                    return 1

                if 'model' not in model:
                    print(f"❌ Invalid config: Model {i} missing 'model' field")
                    return 1

                if 'api_key' not in model:
                    print(f"❌ Invalid config: Model {i} missing 'api_key' field")
                    return 1

            print(f"✅ Configuration is valid: {config_path}")
            print(f"   Found {len(models)} model(s)")
            return 0

        except yaml.YAMLError as e:
            print(f"❌ Invalid YAML syntax: {e}")
            return 1
        except Exception as e:
            print(f"❌ Error validating config: {e}")
            return 1
