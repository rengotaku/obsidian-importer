"""
File Operations - ファイル読み書き

ファイルの読み書きと一覧取得を行う。
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from normalizer.models import GenreType

from normalizer.config import INDEX_DIR, VAULT_MAP, MAX_CONTENT_CHARS, DUST_DIR


# =============================================================================
# Exclusion Tracking
# =============================================================================


_excluded_files: list[tuple[Path, str]] = []  # (path, reason) のリスト


def should_exclude(path: Path, log_exclusion: bool = True) -> bool:
    """パスが除外対象かどうかを判定

    除外条件:
    - 親ディレクトリが . で始まる（隠しフォルダ）

    注意:
    - ファイル名がドットで始まっていても .md 拡張子なら処理対象

    Args:
        path: 判定対象のファイルパス
        log_exclusion: 除外をログに記録するかどうか

    Returns:
        True: 除外対象, False: 処理対象
    """
    global _excluded_files
    try:
        rel_path = path.relative_to(INDEX_DIR)
        parts = rel_path.parts

        # 親ディレクトリをチェック
        for part in parts[:-1]:
            if part.startswith("."):
                reason = f"隠しフォルダ: {part}"
                if log_exclusion:
                    _excluded_files.append((path, reason))
                return True

        # ファイル名のチェック
        if parts:
            filename = parts[-1]
            if filename.startswith(".") and not filename.endswith(".md"):
                reason = f"隠しファイル: {filename}"
                if log_exclusion:
                    _excluded_files.append((path, reason))
                return True

        return False
    except ValueError:
        reason = "INDEX_DIR外"
        if log_exclusion:
            _excluded_files.append((path, reason))
        return True


def get_excluded_files() -> list[tuple[Path, str]]:
    """除外されたファイルのリストを取得"""
    return _excluded_files.copy()


def clear_excluded_files() -> None:
    """除外ファイルリストをクリア"""
    global _excluded_files
    _excluded_files = []


def cleanup_empty_folders(base_dir: Path, quiet: bool = False) -> int:
    """空のサブフォルダを削除

    Args:
        base_dir: クリーンアップ対象のベースディレクトリ
        quiet: 進捗表示を抑制

    Returns:
        削除されたフォルダ数
    """
    deleted_count = 0
    # 深い階層から順に処理
    folders = sorted(
        [d for d in base_dir.rglob("*") if d.is_dir()],
        key=lambda x: len(x.parts),
        reverse=True
    )

    for folder in folders:
        # 隠しフォルダはスキップ
        if any(part.startswith(".") for part in folder.relative_to(base_dir).parts):
            continue
        # 空フォルダかチェック
        contents = [f for f in folder.iterdir() if not f.name.startswith(".")]
        if not contents:
            try:
                if not list(folder.iterdir()):
                    folder.rmdir()
                    deleted_count += 1
                    if not quiet:
                        print(f"  🗑️ 空フォルダ削除: {folder.relative_to(base_dir)}")
            except OSError:
                pass

    return deleted_count


# =============================================================================
# File Operations
# =============================================================================


def read_file_content(filepath: Path, max_chars: int = MAX_CONTENT_CHARS) -> tuple[str, str | None]:
    """
    ファイル内容を読み込み

    Returns:
        tuple: (content, error_message)
    """
    try:
        content = filepath.read_text(encoding="utf-8")
        # frontmatter以降の内容を抽出
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]
        return content[:max_chars].strip(), None
    except FileNotFoundError:
        return "", f"ファイルが見つかりません: {filepath}"
    except PermissionError:
        return "", f"読み取り権限がありません: {filepath}"
    except UnicodeDecodeError:
        return "", f"エンコーディングエラー: {filepath}"
    except Exception as e:
        return "", f"読み込みエラー: {e}"


def write_file_content(filepath: Path, content: str) -> str | None:
    """
    ファイルに内容を書き込み

    Returns:
        error_message or None if success
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        return None
    except PermissionError:
        return f"書き込み権限がありません: {filepath}"
    except Exception as e:
        return f"書き込みエラー: {e}"


def list_index_files() -> list[Path]:
    """@index内の処理対象ファイルを一覧取得（再帰的スキャン対応）

    Returns:
        処理対象ファイルのリスト
    """
    if not INDEX_DIR.exists():
        return []

    files = []
    for f in INDEX_DIR.rglob("*.md"):
        # 隠しファイル/フォルダを除外
        if should_exclude(f):
            continue
        # 既存の除外パターン
        if f.name.startswith("処理結果_"):
            continue
        files.append(f)

    return sorted(files)


def get_destination_path(genre: "GenreType", filename: str, subfolder: str = "") -> Path:
    """ジャンルとサブフォルダに基づいて移動先パスを決定

    Args:
        genre: ジャンル名
        filename: ファイル名
        subfolder: サブフォルダ名（空文字=ルート、"新規: xxx"=新規作成）

    Returns:
        移動先パス

    Routing Rules (Pipeline統合):
        - genre="dust" → @dust/
        - その他 → VAULT_MAP[genre]/subfolder/
    """
    # 特殊ジャンルのルーティング
    if genre == "dust":
        base_path = DUST_DIR
        subfolder = ""  # dustはsubfolderなし
    else:
        base_path = VAULT_MAP.get(genre, VAULT_MAP["その他"])

    # サブフォルダ処理
    if subfolder:
        # "新規: xxx" 形式の処理
        if subfolder.startswith("新規:"):
            subfolder = subfolder[3:].strip()
        elif subfolder.startswith("新規："):  # 全角コロン対応
            subfolder = subfolder[3:].strip()

        if subfolder:
            base_path = base_path / subfolder
            # 必要に応じてサブフォルダを作成
            base_path.mkdir(parents=True, exist_ok=True)

    dest_path = base_path / filename

    # 重複ファイル処理
    if dest_path.exists():
        stem = dest_path.stem
        suffix = dest_path.suffix
        counter = 1
        while dest_path.exists():
            dest_path = base_path / f"{stem}_{counter}{suffix}"
            counter += 1

    return dest_path
