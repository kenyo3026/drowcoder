"""
Refactored write tool using unified tool architecture.

This module provides advanced file writing functionality with:
- Multiple operations: create, overwrite, append, prepend
- Preview and apply modes
- Multiple output styles: default, git_diff, git_conflict
- Safety validation and backup support
- Unified tool interface with BaseTool
"""

import os
import shutil
import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Union

from .base import BaseTool, ToolResponse, ToolResponseMetadata, ToolResponseType, _IntactType


TOOL_NAME = 'write'

@dataclass(frozen=True)
class OutputStyle:
    """Output formatting styles"""
    DEFAULT: str = "default"
    GIT_DIFF: str = "git_diff"
    GIT_CONFLICT: str = "git_conflict"

    @classmethod
    def values(cls):
        """Return all valid style values."""
        return [getattr(cls, attr) for attr in cls.__annotations__.keys()]


@dataclass(frozen=True)
class ExecutionMode:
    """Execution modes"""
    PREVIEW: str = "preview"
    APPLY: str = "apply"

    @classmethod
    def values(cls):
        """Return all valid mode values."""
        return [getattr(cls, attr) for attr in cls.__annotations__.keys()]


@dataclass(frozen=True)
class WriteOperation:
    """Types of write operations"""
    CREATE: str = "create"
    OVERWRITE: str = "overwrite"
    APPEND: str = "append"
    PREPEND: str = "prepend"

    @classmethod
    def values(cls):
        """Return all valid operation values."""
        return [getattr(cls, attr) for attr in cls.__annotations__.keys()]


@dataclass
class FileChange:
    """Represents a file change operation"""
    file_path: Path
    original_content: str
    new_content: str
    operation: str

    @property
    def has_changes(self) -> bool:
        return self.original_content != self.new_content

    @property
    def is_new_file(self) -> bool:
        return not self.file_path.exists()

    @property
    def content_size(self) -> int:
        return len(self.new_content)

    @property
    def line_count(self) -> int:
        return len(self.new_content.split('\n'))


@dataclass
class FileResponse:
    """Response for a single file operation."""
    file_path: Path
    change: Optional[FileChange] = None
    success: bool = False
    error: Optional[str] = None
    backup_path: Optional[Path] = None

    @property
    def has_change(self) -> bool:
        return self.change is not None and self.change.has_changes

    @property
    def operation_type(self) -> str:
        if not self.change:
            return "no_change"
        if self.change.is_new_file:
            return "created"
        elif self.change.operation == WriteOperation.OVERWRITE:
            return "overwritten"
        elif self.change.operation == WriteOperation.APPEND:
            return "appended"
        elif self.change.operation == WriteOperation.PREPEND:
            return "prepended"
        return "modified"


@dataclass
class WriteConfig:
    """Configuration for write operation"""
    content: str
    file_path: Union[str, Path]
    operation: str = WriteOperation.OVERWRITE
    mode: str = "apply"
    output_style: str = "default"
    output_file: Optional[Union[str, Path]] = None
    encoding: str = "utf-8"
    backup: bool = True
    create_dirs: bool = True
    preserve_permissions: bool = True

    def __post_init__(self):
        self.file_path = Path(self.file_path)
        # Normalize content line endings
        self.content = self.content.replace('\r\n', '\n').replace('\r', '\n')
        # Validate operation value
        if self.operation not in WriteOperation.values():
            raise ValueError(f"Invalid operation '{self.operation}'. Must be one of: {WriteOperation.values()}")


@dataclass
class WriteToolResponseMetadata(ToolResponseMetadata, WriteConfig):
    """
    Metadata for write tool response.

    Combines ToolResponseMetadata with WriteConfig to provide
    complete context about the write operation.
    """


@dataclass
class WriteToolResponse(ToolResponse):
    """
    Response from write tool execution.

    Extends ToolResponse with write-specific information.
    Contains file_responses list with per-file write operation details.
    """
    tool_name: str = TOOL_NAME
    file_responses: List[FileResponse] = field(default_factory=list)

    @property
    def total_files_processed(self) -> int:
        return len(self.file_responses)

    @property
    def total_files_changed(self) -> int:
        return sum(1 for fr in self.file_responses if fr.has_change)

    @property
    def total_files_created(self) -> int:
        return sum(1 for fr in self.file_responses if fr.change and fr.change.is_new_file)


class FileProcessor:
    """Handles file content processing and operations"""

    def __init__(self, config: WriteConfig):
        self.config = config

    def prepare_change(self) -> FileChange:
        """Prepare file change based on operation type"""
        file_path = self.config.file_path

        # Read original content
        original_content = self._read_file_safely(file_path)

        # Prepare new content based on operation
        new_content = self._prepare_content(original_content)

        return FileChange(
            file_path=file_path,
            original_content=original_content,
            new_content=new_content,
            operation=self.config.operation
        )

    def _read_file_safely(self, file_path: Path) -> str:
        """Read file content safely"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding=self.config.encoding) as f:
                    return f.read()
            return ""
        except Exception as e:
            self.logger.warning(f"Could not read {file_path}: {e}")
            return ""

    def _prepare_content(self, original_content: str) -> str:
        """Prepare content based on operation type"""
        if self.config.operation == WriteOperation.CREATE:
            if self.config.file_path.exists():
                raise FileExistsError(f"File {self.config.file_path} already exists")
            return self.config.content

        elif self.config.operation == WriteOperation.OVERWRITE:
            return self.config.content

        elif self.config.operation == WriteOperation.APPEND:
            if original_content and not original_content.endswith('\n'):
                return original_content + '\n' + self.config.content
            return original_content + self.config.content

        elif self.config.operation == WriteOperation.PREPEND:
            if self.config.content and not self.config.content.endswith('\n'):
                return self.config.content + '\n' + original_content
            return self.config.content + original_content

        return self.config.content


class OutputFormatter:
    """Handles different output formatting styles"""

    @staticmethod
    def format_default(file_response: FileResponse) -> str:
        """Generate complete file content"""
        if not file_response.has_change:
            return file_response.change.original_content if file_response.change else ""
        return file_response.change.new_content

    @staticmethod
    def format_git_diff(file_response: FileResponse) -> str:
        """Generate git diff style output"""
        if not file_response.has_change:
            return ""

        change = file_response.change
        output = []

        if change.is_new_file:
            # New file
            output.append(f"diff --git a/{change.file_path} b/{change.file_path}")
            output.append("new file mode 100644")
            output.append("index 0000000..1111111")
            output.append("--- /dev/null")
            output.append(f"+++ b/{change.file_path}")

            new_lines = change.new_content.split('\n')
            output.append(f"@@ -0,0 +1,{len(new_lines)} @@")
            for line in new_lines:
                output.append(f"+{line}")
        else:
            # Modified file - use difflib for better diff
            output.append(f"diff --git a/{change.file_path} b/{change.file_path}")
            output.append("index 0000000..1111111 100644")
            output.append(f"--- a/{change.file_path}")
            output.append(f"+++ b/{change.file_path}")

            original_lines = change.original_content.split('\n')
            new_lines = change.new_content.split('\n')

            # Use difflib to generate unified diff
            diff = difflib.unified_diff(
                original_lines,
                new_lines,
                n=3,
                lineterm=''
            )

            # Skip the first two lines (file headers) as we already added them
            diff_lines = list(diff)[2:]
            output.extend(diff_lines)

        return '\n'.join(output)

    @staticmethod
    def format_git_conflict(file_response: FileResponse) -> str:
        """Generate git conflict style output for VS Code rendering"""
        if not file_response.has_change:
            return file_response.change.original_content if file_response.change else ""

        change = file_response.change

        if change.is_new_file:
            return change.new_content

        # Create conflict markers
        conflict_content = []
        conflict_content.append("<<<<<<< HEAD")
        conflict_content.append(change.original_content)
        conflict_content.append("=======")
        conflict_content.append(change.new_content)
        conflict_content.append(">>>>>>> incoming")

        return '\n'.join(conflict_content)


class SafetyValidator:
    """Handles safety checks and validations"""

    @staticmethod
    def validate_config(config: WriteConfig) -> List[str]:
        """Validate configuration for potential issues"""
        warnings = []

        # Check file path safety
        try:
            file_path = config.file_path.resolve()
            current_dir = Path.cwd().resolve()

            # Warn if writing outside current directory tree
            if not str(file_path).startswith(str(current_dir)):
                warnings.append(f"Writing outside current directory: {file_path}")
        except Exception:
            warnings.append("Could not resolve file path")

        # Check if file exists for CREATE operation
        if config.operation == WriteOperation.CREATE and config.file_path.exists():
            warnings.append(f"CREATE operation but file already exists: {config.file_path}")

        # Check for large content
        if len(config.content) > 1024 * 1024:  # 1MB
            warnings.append(f"Large content size: {len(config.content) / 1024 / 1024:.1f}MB")

        # Check for many lines
        line_count = len(config.content.split('\n'))
        if line_count > 10000:
            warnings.append(f"Large line count: {line_count} lines")

        # Check for binary content
        if '\x00' in config.content:
            warnings.append("Content contains null bytes (potential binary data)")

        return warnings

    @staticmethod
    def validate_file_access(file_path: Path) -> List[str]:
        """Validate file access permissions"""
        warnings = []

        try:
            if file_path.exists():
                if not os.access(file_path, os.R_OK):
                    warnings.append(f"File not readable: {file_path}")
                if not os.access(file_path, os.W_OK):
                    warnings.append(f"File not writable: {file_path}")
            else:
                # Check parent directory
                parent = file_path.parent
                if not parent.exists():
                    warnings.append(f"Parent directory does not exist: {parent}")
                elif not os.access(parent, os.W_OK):
                    warnings.append(f"Parent directory not writable: {parent}")
        except Exception as e:
            warnings.append(f"Could not check file permissions: {e}")

        return warnings


class WriteTool(BaseTool):
    """
    Tool for advanced file writing operations.

    Supports multiple operation modes (create, overwrite, append, prepend),
    preview/apply modes, and various output styles.
    """
    name = TOOL_NAME

    def __init__(self, **kwargs):
        """Initialize WriteTool."""
        super().__init__(**kwargs)
        self.formatter = OutputFormatter()
        self.validator = SafetyValidator()

    def execute(
        self,
        file_path: Union[str, Path],
        content: str,
        mode: str = "apply",
        output_style: str = "default",
        operation: str = "overwrite",
        output_file: Optional[Union[str, Path]] = None,
        encoding: str = "utf-8",
        backup: bool = True,
        create_dirs: bool = True,
        preserve_permissions: bool = True,
        as_type: Union[str, _IntactType] = ToolResponseType.PRETTY_STR,
        filter_empty_fields: bool = True,
        filter_metadata_fields: bool = True,
    ) -> Any:
        """
        Execute write operation.

        Args:
            file_path: Target file path
            content: Content to write
            mode: "preview" or "apply"
            output_style: "default", "git_diff", or "git_conflict"
            operation: "create", "overwrite", "append", or "prepend"
            output_file: Optional output file path (for apply mode)
            encoding: Text encoding (default: utf-8)
            backup: Whether to create backup before overwriting
            create_dirs: Whether to create parent directories if they don't exist
            preserve_permissions: Whether to preserve file permissions
            as_type: Output format type for the response
            filter_empty_fields: Whether to filter empty fields in output
            filter_metadata_fields: Whether to filter metadata fields in output

        Returns:
            WriteToolResponse (or converted format based on as_type)
        """
        self._validate_initialized()

        # Capture locals before creating any new variables
        local_vars = locals().copy()
        dumping_kwargs = self._parse_dump_kwargs(local_vars)
        write_kwargs = self._parse_dump_kwargs(local_vars, invert=True)

        config = WriteConfig(**write_kwargs)

        # Check if content would result in no changes
        if self._is_content_identical(file_path, content, operation):
            self.logger.info("Content is identical to existing file - no changes needed.")
            return WriteToolResponse(
                success=True,
                content="No changes needed",
                metadata=WriteToolResponseMetadata(**config.__dict__)
            ).dump(**dumping_kwargs)

        # Create configuration
        operation_value = operation.lower()
        if operation_value not in WriteOperation.values():
            raise ValueError(f"Invalid operation '{operation}'. Must be one of: {WriteOperation.values()}")

        # Validate configuration
        config_warnings = self.validator.validate_config(config)
        access_warnings = self.validator.validate_file_access(config.file_path)

        if config_warnings or access_warnings:
            self.logger.warning("Safety Warnings:")
            for warning in config_warnings + access_warnings:
                self.logger.warning(f"  - {warning}")

        # Process file
        processor = FileProcessor(config)
        response = WriteToolResponse(
            success=True,
            metadata=WriteToolResponseMetadata(**config.__dict__)
        )

        try:
            change = processor.prepare_change()
            file_response = FileResponse(file_path=config.file_path, change=change)
            response.file_responses.append(file_response)

            # Handle output based on mode
            mode_value = mode.lower()
            if mode_value not in ExecutionMode.values():
                raise ValueError(f"Invalid mode '{mode}'. Must be one of: {ExecutionMode.values()}")

            style_value = output_style.lower()
            if style_value not in OutputStyle.values():
                raise ValueError(f"Invalid output_style '{output_style}'. Must be one of: {OutputStyle.values()}")

            if mode_value == ExecutionMode.PREVIEW:
                self._handle_preview(response, style_value)
                response.content = "Preview completed"
            else:  # APPLY
                self._handle_apply(response, style_value, output_file)
                response.content = "Write operation completed"

            # Trigger callback if configured
            self._trigger_callback("write_completed", {
                "file_path": str(config.file_path),
                "operation": operation,
                "mode": mode,
                "success": response.success
            })

        except Exception as e:
            # Update the file_response that was already added
            if response.file_responses:
                response.file_responses[-1].success = False
                response.file_responses[-1].error = str(e)
            else:
                # If no file_response was added yet, create one
                file_response = FileResponse(
                    file_path=config.file_path,
                    success=False,
                    error=str(e)
                )
                response.file_responses.append(file_response)

            response.success = False
            response.error = str(e)
            self.logger.error(f"Write operation failed: {e}")

        return response.dump(**dumping_kwargs)

    def _is_content_identical(self, file_path: Union[str, Path], content: str, operation: str) -> bool:
        """Check if content would result in no changes"""
        file_path = Path(file_path)

        # Only check for overwrite operations
        if operation.lower() != "overwrite":
            return False

        if not file_path.exists():
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()

            # Normalize line endings for comparison
            existing_normalized = existing_content.replace('\r\n', '\n').replace('\r', '\n')
            content_normalized = content.replace('\r\n', '\n').replace('\r', '\n')

            return existing_normalized.strip() == content_normalized.strip()
        except Exception:
            return False

    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Create backup of existing file"""
        if not file_path.exists():
            return None

        try:
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            counter = 1
            while backup_path.exists():
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup.{counter}")
                counter += 1

            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            self.logger.warning(f"Failed to create backup: {e}")
            return None

    def _handle_preview(self, response: WriteToolResponse, style: str):
        """Handle preview mode output"""
        for file_response in response.file_responses:
            self.logger.info("=" * 60)
            self.logger.info(f"File: {file_response.file_path}")
            if file_response.change:
                self.logger.info(f"Operation: {file_response.operation_type}")
                self.logger.info(f"Size: {file_response.change.content_size} bytes, {file_response.change.line_count} lines")
            self.logger.info("Mode: PREVIEW")
            self.logger.info("=" * 60)

            if not file_response.has_change:
                self.logger.info("No changes to preview.")
                continue

            # Output formatted content
            if style == OutputStyle.DEFAULT:
                formatted_output = self.formatter.format_default(file_response)
            elif style == OutputStyle.GIT_DIFF:
                formatted_output = self.formatter.format_git_diff(file_response)
            elif style == OutputStyle.GIT_CONFLICT:
                formatted_output = self.formatter.format_git_conflict(file_response)
            else:
                formatted_output = ""

            # Log formatted output line by line to preserve formatting
            for line in formatted_output.splitlines():
                self.logger.info(line)

    def _handle_apply(self, response: WriteToolResponse, style: str, output_file: Optional[Path]):
        """Handle apply mode output"""
        files_written = []
        errors = []

        for file_response in response.file_responses:
            if not file_response.has_change:
                self.logger.info(f"No changes needed for: {file_response.file_path}")
                file_response.success = True
                continue

            try:
                # Determine target path
                if output_file:
                    target_path = Path(output_file)
                else:
                    target_path = file_response.file_path

                # Create backup if needed (only for DEFAULT style and same file)
                if (response.metadata.backup and
                    target_path.exists() and
                    target_path == file_response.file_path and
                    style == OutputStyle.DEFAULT):
                    file_response.backup_path = self._create_backup(target_path)
                    if file_response.backup_path:
                        self.logger.info(f"Backup created: {file_response.backup_path}")

                # Generate content based on style
                if style == OutputStyle.DEFAULT:
                    content = self.formatter.format_default(file_response)
                elif style == OutputStyle.GIT_DIFF:
                    content = self.formatter.format_git_diff(file_response)
                elif style == OutputStyle.GIT_CONFLICT:
                    content = self.formatter.format_git_conflict(file_response)

                # Create directories if needed
                if response.metadata.create_dirs:
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                # Write to file
                with open(target_path, 'w', encoding=response.metadata.encoding) as f:
                    f.write(content)

                # Preserve permissions if requested (only for DEFAULT style)
                if (response.metadata.preserve_permissions and
                    file_response.file_path.exists() and
                    target_path != file_response.file_path and
                    style == OutputStyle.DEFAULT):
                    try:
                        shutil.copystat(file_response.file_path, target_path)
                    except Exception:
                        pass  # Ignore permission copy errors

                files_written.append(str(target_path))
                file_response.success = True
                self.logger.info(f"Successfully {file_response.operation_type}: {target_path}")

            except Exception as e:
                error_msg = f"Error writing {file_response.file_path}: {e}"
                errors.append(error_msg)
                file_response.success = False
                file_response.error = str(e)
                self.logger.error(error_msg)

        # Set response status once at the end
        if errors:
            response.success = False
            response.error = "; ".join(errors)
            response.content = f"Apply completed with errors: {len(files_written)} succeeded, {len(errors)} failed"
        else:
            response.content = f"Apply completed: {len(files_written)} files written"
