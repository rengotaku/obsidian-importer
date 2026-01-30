"""IO - 入出力（ファイル操作、セッション管理、Ollama API通信）"""

from normalizer.io.files import (
    should_exclude,
    get_excluded_files,
    clear_excluded_files,
    cleanup_empty_folders,
    read_file_content,
    write_file_content,
    list_index_files,
    get_destination_path,
)
from normalizer.io.session import (
    progress_bar,
    timestamp,
    get_session_dir,
    get_state_files,
    get_log_file,
    create_new_session,
    load_latest_session,
    log_message,
    start_new_log_session,
)
from normalizer.io.ollama import (
    call_ollama,
    extract_json_from_code_block,
    extract_first_json_object,
    format_parse_error,
    parse_json_response,
)

__all__ = [
    # files.py
    "should_exclude",
    "get_excluded_files",
    "clear_excluded_files",
    "cleanup_empty_folders",
    "read_file_content",
    "write_file_content",
    "list_index_files",
    "get_destination_path",
    # session.py
    "progress_bar",
    "timestamp",
    "get_session_dir",
    "get_state_files",
    "get_log_file",
    "create_new_session",
    "load_latest_session",
    "log_message",
    "start_new_log_session",
    # ollama.py
    "call_ollama",
    "extract_json_from_code_block",
    "extract_first_json_object",
    "format_parse_error",
    "parse_json_response",
]
