#!/usr/bin/env python3
"""Sign and verify an Android APK without exposing keystore passwords."""

from __future__ import annotations

import base64
import os
import subprocess
import tempfile
from pathlib import Path


def _required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise ValueError(f"Missing required signing environment variable: {name}")
    return value


def sign_android_artifact(input_path: Path, output_path: Path, *, zipalign: Path, apksigner: Path) -> Path:
    if not input_path.is_file() or input_path.stat().st_size == 0:
        raise FileNotFoundError(f"Android input APK is missing or empty: {input_path}")
    if not zipalign.is_file():
        raise FileNotFoundError(f"zipalign is missing: {zipalign}")
    if not apksigner.is_file():
        raise FileNotFoundError(f"apksigner is missing: {apksigner}")
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Android signing output must differ from the unsigned input")

    keystore_b64 = _required_env("EFFILIFE_ANDROID_KEYSTORE_BASE64")
    store_password = _required_env("EFFILIFE_ANDROID_KEYSTORE_PASSWORD")
    key_alias = _required_env("EFFILIFE_ANDROID_KEY_ALIAS")
    key_password = _required_env("EFFILIFE_ANDROID_KEY_PASSWORD")
    try:
        keystore_bytes = base64.b64decode(keystore_b64, validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError("EFFILIFE_ANDROID_KEYSTORE_BASE64 is not valid base64") from error
    if not keystore_bytes:
        raise ValueError("EFFILIFE_ANDROID_KEYSTORE_BASE64 is empty")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="effilife-android-sign-") as temp_dir:
        temp_root = Path(temp_dir)
        keystore = temp_root / "release.keystore"
        aligned = temp_root / "aligned.apk"
        keystore.write_bytes(keystore_bytes)
        env = {
            **os.environ,
            # apksigner supports env: references, keeping passwords out of the
            # process argument list and ordinary command output.
            "EFFILIFE_ANDROID_KEYSTORE_PASSWORD": store_password,
            "EFFILIFE_ANDROID_KEY_PASSWORD": key_password,
        }
        subprocess.run([str(zipalign), "-f", "-p", "4", str(input_path), str(aligned)], check=True, env=env)
        subprocess.run([
            str(apksigner), "sign", "--ks", str(keystore),
            "--ks-pass", "env:EFFILIFE_ANDROID_KEYSTORE_PASSWORD",
            "--ks-key-alias", key_alias,
            "--key-pass", "env:EFFILIFE_ANDROID_KEY_PASSWORD",
            "--out", str(output_path), str(aligned),
        ], check=True, env=env)
        subprocess.run([str(apksigner), "verify", str(output_path)], check=True, env=env)

    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError(f"Android signing produced no usable output: {output_path}")
    input_path.unlink()
    return output_path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--zipalign", required=True, type=Path)
    parser.add_argument("--apksigner", required=True, type=Path)
    args = parser.parse_args()
    try:
        artifact = sign_android_artifact(args.input, args.output, zipalign=args.zipalign, apksigner=args.apksigner)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
    print(f"Signed Android APK: {artifact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
