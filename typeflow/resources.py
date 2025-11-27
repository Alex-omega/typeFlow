from pathlib import Path


ASSETS_DIR = Path(__file__).parent / "assets"


def asset_path(name: str) -> Path:
    """Return absolute path to an asset inside typeflow/assets."""
    return ASSETS_DIR / name
