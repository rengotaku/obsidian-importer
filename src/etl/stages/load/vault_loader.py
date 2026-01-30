"""VaultLoader stage for ETL pipeline.

Loads processed items to appropriate Vault folders.
"""

from pathlib import Path

from src.etl.core.models import ProcessingItem
from src.etl.core.stage import BaseStage, BaseStep
from src.etl.core.types import StageType

# Default vault mapping
GENRE_VAULT_MAP = {
    "engineer": "Vaults/engineer",
    "business": "Vaults/business",
    "economy": "Vaults/economy",
    "daily": "Vaults/daily",
    "other": "Vaults/other",
}


class DetermineVaultStep(BaseStep):
    """Determine target vault based on genre."""

    def __init__(
        self,
        vaults_path: Path | None = None,
        vault_map: dict[str, str] | None = None,
    ):
        """Initialize DetermineVaultStep.

        Args:
            vaults_path: Base path for vaults.
            vault_map: Genre to vault path mapping.
        """
        self._vaults_path = vaults_path or Path("Vaults")
        self._vault_map = vault_map or GENRE_VAULT_MAP

    @property
    def name(self) -> str:
        return "determine_vault"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Determine target vault for item.

        Args:
            item: Item with genre metadata.

        Returns:
            Item with target_vault metadata.
        """
        genre = item.metadata.get("genre", "other")

        # Get vault path for genre
        relative_path = self._vault_map.get(genre, self._vault_map.get("other", "Vaults/other"))

        # Build full path
        if self._vaults_path.is_absolute():
            vault_path = self._vaults_path.parent / relative_path
        else:
            vault_path = Path(relative_path)

        item.metadata["target_vault"] = str(vault_path)
        item.metadata["target_genre"] = genre

        return item


class MoveToVaultStep(BaseStep):
    """Move file to target vault."""

    def __init__(self, vaults_path: Path | None = None):
        """Initialize MoveToVaultStep.

        Args:
            vaults_path: Base path for vaults.
        """
        self._vaults_path = vaults_path

    @property
    def name(self) -> str:
        return "move_to_vault"

    def process(self, item: ProcessingItem) -> ProcessingItem:
        """Move file to target vault.

        Args:
            item: Item with target_vault metadata.

        Returns:
            Item with final output_path.
        """
        content = item.transformed_content or item.content or ""
        target_vault = item.metadata.get("target_vault", "Vaults/other")

        # Determine filename
        if item.source_path:
            filename = item.source_path.stem + ".md"
        else:
            filename = f"{item.item_id}.md"

        # Build output path
        vault_path = Path(target_vault)
        if self._vaults_path:
            vault_path = self._vaults_path / vault_path.name

        output_file = vault_path / filename

        # Ensure directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        output_file.write_text(content, encoding="utf-8")

        item.output_path = output_file
        item.metadata["moved_to_vault"] = True

        return item


class VaultLoader(BaseStage):
    """Load stage for vault organization.

    Moves processed items to appropriate vault folders.
    """

    def __init__(
        self,
        vaults_path: Path | None = None,
        vault_map: dict[str, str] | None = None,
        steps: list[BaseStep] | None = None,
    ):
        """Initialize VaultLoader.

        Args:
            vaults_path: Base path for vaults.
            vault_map: Genre to vault path mapping.
            steps: Optional custom steps. Defaults to standard load steps.
        """
        super().__init__()
        self._vaults_path = vaults_path
        self._vault_map = vault_map
        self._steps = steps or [
            DetermineVaultStep(vaults_path, vault_map),
            MoveToVaultStep(vaults_path),
        ]

    @property
    def stage_type(self) -> StageType:
        return StageType.LOAD

    @property
    def steps(self) -> list[BaseStep]:
        return self._steps
