"""Collect upstream license texts for locally resolved application dependencies."""
from pathlib import Path
import json
import re
import shutil

def collect(root: Path, destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    inventory = []
    def add(kind, name, version, license_name, directory):
        target = destination / kind / (name.replace('/', '__') + '-' + version)
        texts = []
        if directory.is_dir():
            for entry in sorted(directory.iterdir()):
                if entry.is_file() and entry.name.lower().startswith(('license', 'licence', 'copying', 'copyright', 'notice')):
                    target.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(entry, target / entry.name)
                    texts.append((target / entry.name).relative_to(destination).as_posix())
        inventory.append({'ecosystem': kind, 'name': name, 'version': version, 'license': license_name, 'texts': texts})
    packages = json.loads((root / 'package-lock.json').read_text())['packages']
    for location, package in sorted(packages.items()):
        if not location or package.get('dev') or package.get('link'):
            continue
        directory = root / location
        metadata = directory / 'package.json'
        if metadata.is_file():
            value = json.loads(metadata.read_text())
            add('npm', value['name'], value['version'], value.get('license'), directory)
    cargo_lock = (root / 'apps/desktop/src-tauri/Cargo.lock').read_text()
    for block in cargo_lock.split('[[package]]')[1:]:
        if 'registry+' not in block:
            continue
        name = re.search(r'^name = "([^"]+)"', block, re.M)[1]
        version = re.search(r'^version = "([^"]+)"', block, re.M)[1]
        directory = next(iter((root / '.cache/cargo/registry/src').glob('*/' + name + '-' + version)), None)
        if directory:
            manifest = (directory / 'Cargo.toml').read_text()
            license_name = re.search(r'^license = "([^"]+)"', manifest, re.M)
            add('cargo', name, version, license_name[1] if license_name else None, directory)
    rust_version = json.loads((root / 'toolchain.json').read_text())['rust']['version']
    rust = root / '.tools' / ('rust-' + rust_version) / 'share/doc/rust'
    if rust.is_dir():
        shutil.copytree(rust / 'licenses', destination / 'rust-standard-library/licenses')
        for name in ['COPYRIGHT.html', 'COPYRIGHT-library.html']:
            if (rust / name).exists():
                shutil.copy2(rust / name, destination / 'rust-standard-library' / name)
    (destination / 'inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n')
