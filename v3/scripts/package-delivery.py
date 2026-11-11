#!/usr/bin/env python3
"""Assemble a local acceptance bundle from verified production artifacts."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from run import ROOT
from artifact_fingerprints import frontend_fingerprint

def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()

def main():
    version = (ROOT / 'VERSION').read_text().strip()
    repository = ROOT.parent
    changed = subprocess.check_output(['git', 'status', '--porcelain', '--', 'v3'], cwd=repository, text=True)
    if changed.strip():
        raise SystemExit('Commit v3 changes before assembling a reviewable delivery.')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repository, text=True).strip()
    native = json.loads((ROOT / 'test-results/native-desktop/result.json').read_text())
    webkit = json.loads((ROOT / 'test-results/native-webkit/result.json').read_text())
    if native.get('version') != version or len(native['checks']) < 11 or 'main-window CSP rejects inline script injection' not in native['checks'] or webkit.get('version') != version or len(webkit['checks']) < 8:
        raise SystemExit('Current-version native and WebKit acceptance evidence is required.')
    if webkit['frontendIndexSha256'] != digest(ROOT / 'dist/index.html') or webkit.get('frontendTreeSha256') != frontend_fingerprint(ROOT / 'dist'):
        raise SystemExit('The production frontend changed after WebKit verification.')
    package = ROOT / '.cache/native-target/release/bundle/deb' / ('EffiLife_' + version + '_amd64.deb')
    package_version = subprocess.check_output(['dpkg-deb', '-f', str(package), 'Version'], text=True).strip()
    if package_version != version:
        raise SystemExit('The native package version differs from VERSION.')
    examples = ROOT / 'dist/examples'
    if not examples.is_dir() or len(list(examples.iterdir())) != 3:
        raise SystemExit('Build the three extension examples before packaging.')
    deliveries = ROOT / '.cache/delivery'
    deliveries.mkdir(parents=True, exist_ok=True)
    name = 'EffiLife-' + version + '-' + commit[:8] + '-linux-amd64'
    final = deliveries / name
    archive = deliveries / (name + '.zip')
    if final.exists() or archive.exists():
        raise SystemExit('This commit already has a delivery. Existing review artifacts are immutable.')
    with tempfile.TemporaryDirectory(prefix='.preparing-', dir=deliveries) as temporary:
        temporary = Path(temporary)
        extracted = temporary / 'extracted'
        subprocess.run(['dpkg-deb', '-x', str(package), str(extracted)], check=True)
        if digest(extracted / 'usr/bin/effilife-desktop') != native['applicationSha256']:
            raise SystemExit('The package contains a different executable from the verified program.')
        staging = temporary / name
        staging.mkdir()
        shutil.copy2(package, staging / package.name)
        shutil.copytree(ROOT / 'dist', staging / 'web', ignore=shutil.ignore_patterns('examples'))
        shutil.copytree(examples, staging / 'examples')
        shutil.copytree(ROOT / 'docs', staging / 'docs')
        for file in ['VERSION', 'CHANGELOG.md', 'README.md']:
            shutil.copy2(ROOT / file, staging / file)
        verification = staging / 'verification'
        verification.mkdir()
        for folder in ['native-desktop', 'native-webkit']:
            shutil.copy2(ROOT / 'test-results' / folder / 'result.json', verification / (folder + '.json'))
        spec = importlib.util.spec_from_file_location('dependency_notices', ROOT / 'scripts/dependency-notices.py')
        notices = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(notices)
        notices.collect(ROOT, staging / 'third-party-notices')
        files = sorted(path for path in staging.rglob('*') if path.is_file())
        checksums = {path.relative_to(staging).as_posix(): digest(path) for path in files}
        metadata = {'product': 'EffiLife', 'version': version, 'status': 'acceptance', 'platform': 'linux-amd64', 'packagedFromCommit': commit, 'assembledAt': datetime.now(timezone.utc).isoformat(), 'checksums': checksums}
        (staging / 'delivery.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
        (staging / 'SHA256SUMS').write_text(''.join(value + '  ' + key + '\n' for key, value in checksums.items()))
        candidate = temporary / archive.name
        with zipfile.ZipFile(candidate, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6, strict_timestamps=False) as bundle:
            for path in sorted(staging.rglob('*')):
                if path.is_file():
                    bundle.write(path, path.relative_to(staging).as_posix())
        with zipfile.ZipFile(candidate) as bundle:
            for path, expected in checksums.items():
                if hashlib.sha256(bundle.read(path)).hexdigest() != expected:
                    raise SystemExit('Delivery archive verification failed: ' + path)
        os.replace(staging, final)
        os.replace(candidate, archive)
    checksum = digest(archive)
    archive.with_suffix('.zip.sha256').write_text(checksum + '  ' + archive.name + '\n')
    print(json.dumps({'directory': str(final.relative_to(ROOT)), 'archive': str(archive.relative_to(ROOT)), 'sha256': checksum, 'bytes': archive.stat().st_size, 'payloadFiles': len(checksums)}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
