"""Copy the encounter viewer to Pages; analysis exports its data separately."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
for name in ("encounters.html", "encounters.css", "encounters.js"):
    shutil.copyfile(root / "viewer" / name, root / "docs" / name)
print("Exported encounter viewer to docs/")
