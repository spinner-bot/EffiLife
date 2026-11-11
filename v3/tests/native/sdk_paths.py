"""Keep Linux SDK relocation confined to the native test subprocess tree."""
from pathlib import Path
import hashlib
import subprocess

def relocate_webkit(root: Path, env: dict):
    source = Path(__file__).with_name('relocate-webkit.c')
    fingerprint = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    library = root / '.cache/native-tests' / ('webkit-paths-' + fingerprint + '.so')
    library.parent.mkdir(parents=True, exist_ok=True)
    if not library.exists():
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror', '-o', str(library), str(source), '-ldl'], check=True)
    env['LD_PRELOAD'] = str(library) + (':' + env['LD_PRELOAD'] if env.get('LD_PRELOAD') else '')
    env['EFFILIFE_TEST_WEBKIT_DIR'] = str(root / '.tools/native-sdk/usr/lib/x86_64-linux-gnu/webkit2gtk-4.1')
