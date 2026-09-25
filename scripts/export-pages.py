"""Export the latest actual SUMO replay to the GitHub Pages /docs directory."""
from pathlib import Path
import shutil
import gzip
root = Path(__file__).resolve().parents[1]
source = root / 'runs' / 'pinole'
for name in ('index.html', 'app.js', 'style.css', 'manifest.json'):
    shutil.copyfile(source / name, root / 'docs' / name)
(root / 'docs' / '.nojekyll').touch()
print('Pages export ready in docs/. Commit and push to publish updates.')

(root/'docs'/'replay.json.gz').write_bytes(gzip.compress((source/'replay.json').read_bytes(),mtime=0))
(root/'docs'/'replay.json').unlink(missing_ok=True)
