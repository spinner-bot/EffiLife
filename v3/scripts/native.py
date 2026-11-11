#!/usr/bin/env python3
"""Run native v3 commands with project-local Rust, Node and Linux SDK paths."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
from run import ROOT, ensure_node

PROJECT = ROOT / "apps" / "desktop"

def environment():
    settings = json.loads((ROOT / "toolchain.json").read_text())
    rust = ROOT / ".tools" / ("rust-" + settings["rust"]["version"]) / "bin"
    node = ensure_node()
    sdk = ROOT / ".tools" / "native-sdk"
    env = dict(os.environ)
    paths = [str(node), str(rust)]
    if sdk.is_dir():
        paths.append(str(sdk / "usr/bin"))
        libraries = [str(sdk / path) for path in ["usr/lib/x86_64-linux-gnu", "lib/x86_64-linux-gnu", "usr/lib"]]
        env["LD_LIBRARY_PATH"] = os.pathsep.join([*libraries, env.get("LD_LIBRARY_PATH", "")])
        env["PKG_CONFIG_SYSROOT_DIR"] = str(sdk)
        env["PKG_CONFIG_PATH"] = os.pathsep.join([str(sdk / path) for path in ["usr/lib/x86_64-linux-gnu/pkgconfig", "usr/share/pkgconfig", "usr/lib/pkgconfig"]])
        env["XDG_DATA_DIRS"] = str(sdk / "usr/share") + os.pathsep + env.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
        schemas = sdk / "usr/share/glib-2.0/schemas"
        compiler = next(iter(sdk.rglob("glib-compile-schemas")), None)
        if schemas.is_dir() and compiler and not (schemas / "gschemas.compiled").exists():
            subprocess.run([str(compiler), str(schemas)], env=env, check=True)
        if (schemas / "gschemas.compiled").exists():
            env["GSETTINGS_SCHEMA_DIR"] = str(schemas)
    env["PATH"] = os.pathsep.join([*paths, env.get("PATH", "")])
    env["CARGO_HOME"] = str(ROOT / ".cache/cargo")
    env["CARGO_TARGET_DIR"] = str(ROOT / ".cache/native-target")
    env.setdefault("CARGO_BUILD_JOBS", "4")
    return env

def main():
    args = sys.argv[1:]
    if not args or args[0] not in {"cargo", "tauri", "info"}:
        raise SystemExit("Usage: python3 v3/scripts/native.py cargo|tauri|info [arguments]")
    env = environment()
    if args[0] == "info":
        for command in [["rustc", "--version"], ["cargo", "--version"], ["pkg-config", "--modversion", "gtk+-3.0", "webkit2gtk-4.1"]]:
            subprocess.run(command, env=env, check=True)
        return
    if args[0] == "cargo":
        command = ["cargo", *args[1:]]
        cwd = PROJECT / "src-tauri"
    else:
        command = ["node", str(ROOT / "node_modules/@tauri-apps/cli/tauri.js"), *args[1:]]
        cwd = PROJECT
    raise SystemExit(subprocess.call(command, env=env, cwd=cwd))

if __name__ == "__main__":
    main()

