# SPDX-License-Identifier: AGPL-3.0-only
"""Builds the Claude Desktop extension: dist/selfhost-remote-mail-mcp-<version>.mcpb.

    python3 scripts/build_mcpb.py

An .mcpb file is a zip: extension/manifest.json (with this version filled in) plus the project itself. Claude
Desktop runs it with uv, which brings Python and the exact packages in uv.lock, so nothing needs installing
first. The release workflow runs this and attaches the file to each GitHub release.
"""
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ["pyproject.toml", "uv.lock", "README.md", "LICENSE", "NOTICE", "CHANGELOG.md"]   # what uv needs to install it
SKIP = {"__pycache__", ".DS_Store"}


def version() -> str:
    found = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M)
    if not found:
        sys.exit("No version in pyproject.toml.")
    return found.group(1)


def build(out_dir: Path = ROOT / "dist") -> Path:
    ver = version()
    manifest = json.loads((ROOT / "extension" / "manifest.json").read_text())
    manifest["version"] = ver
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"selfhost-remote-mail-mcp-{ver}.mcpb"
    package = ROOT / "src" / "selfhost_remote_mail_mcp"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, indent=2) + "\n")
        zf.write(ROOT / "extension" / "icon.png", "icon.png")   # 512 px, the size Claude Desktop shows best
        for name in FILES:
            zf.write(ROOT / name, name)
        for path in sorted(package.rglob("*")):
            if path.is_file() and not SKIP & set(path.parts) and path.suffix != ".pyc":
                zf.write(path, path.relative_to(ROOT).as_posix())
    return out


if __name__ == "__main__":
    print(build())
