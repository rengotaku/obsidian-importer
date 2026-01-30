"""State - 処理状態管理（StateManagerシングルトン）"""

from normalizer.state.manager import (
    StateManager,
    get_state,
    load_state,
    save_state,
    delete_state,
    create_initial_state,
    update_state,
)

__all__ = [
    "StateManager",
    "get_state",
    "load_state",
    "save_state",
    "delete_state",
    "create_initial_state",
    "update_state",
]
