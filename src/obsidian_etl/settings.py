"""Project settings for obsidian-etl.

Defines hooks, session store, and other Kedro configuration.
"""

from obsidian_etl.hooks import ErrorHandlerHook, LoggingHook

HOOKS = (ErrorHandlerHook(), LoggingHook())

# Disable telemetry
TELEMETRY_ENABLED = False
