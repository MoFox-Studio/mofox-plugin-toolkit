"""Short verification script for the package_manager fix."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from mpdt.utils.managers.package_manager import PackageManager


def _create_fake_plugin(base: Path) -> Path:
    """Create a minimal fake plugin directory with the problematic layout."""
    plugin_dir = base / "test_plugin"
    plugin_dir.mkdir()

    manifest = {
        "name": "test_plugin",
        "version": "1.0.0",
        "description": "Test",
        "author": "Test",
        "entry_point": "plugin.py",
    }
    (plugin_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    (plugin_dir / "plugin.py").write_text("print('hello')\n", encoding="utf-8")

    # Root-level README.md
    (plugin_dir / "README.md").write_text("# Test Plugin\n", encoding="utf-8")

    # Nested dist/ (e.g. web/dist/)
    nested_dist = plugin_dir / "web" / "dist"
    nested_dist.mkdir(parents=True)
    (nested_dist / "index.html").write_text("<html></html>\n", encoding="utf-8")
    (nested_dist / "app.js").write_text("console.log('hi')\n", encoding="utf-8")

    # Root-level dist/ (output directory that should be excluded)
    root_dist = plugin_dir / "dist"
    root_dist.mkdir()
    (root_dist / "old_build.mfp").write_text("old\n", encoding="utf-8")

    # docs/ directory
    docs_dir = plugin_dir / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text("# Guide\n", encoding="utf-8")

    # CHANGELOG.md
    (plugin_dir / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")

    return plugin_dir


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    plugin_dir = _create_fake_plugin(tmp)

    pm = PackageManager(plugin_dir)

    # Test 1: with_docs=False (default)
    files = pm.collect_files(with_docs=False)
    relative = sorted(
        str(f.relative_to(plugin_dir)).replace("\\", "/") for f in files
    )
    print("=== Test 1: with_docs=False ===")
    for f in relative:
        print(f"  {f}")

    assert "README.md" in relative, "FAIL[1]: README.md should always be included"
    assert "web/dist/index.html" in relative, "FAIL[1]: web/dist/index.html should be included"
    assert "web/dist/app.js" in relative, "FAIL[1]: web/dist/app.js should be included"
    assert "dist/old_build.mfp" not in relative, "FAIL[1]: root dist/ should be excluded"
    assert "docs/guide.md" not in relative, "FAIL[1]: docs/ should NOT be included without --with-docs"
    assert "CHANGELOG.md" not in relative, "FAIL[1]: CHANGELOG.md should NOT be included without --with-docs"
    print("  PASS\n")

    # Test 2: with_docs=True
    files2 = pm.collect_files(with_docs=True)
    relative2 = sorted(
        str(f.relative_to(plugin_dir)).replace("\\", "/") for f in files2
    )
    print("=== Test 2: with_docs=True ===")
    for f in relative2:
        print(f"  {f}")

    assert "README.md" in relative2, "FAIL[2]: README.md should be included"
    assert "docs/guide.md" in relative2, "FAIL[2]: docs/ should be included with --with-docs"
    assert "CHANGELOG.md" in relative2, "FAIL[2]: CHANGELOG.md should be included with --with-docs"
    assert "web/dist/index.html" in relative2, "FAIL[2]: web/dist/index.html should be included"
    assert "dist/old_build.mfp" not in relative2, "FAIL[2]: root dist/ should still be excluded"
    print("  PASS\n")

    # Test 3: custom output_dir name
    files3 = pm.collect_files(with_docs=False, output_dir="build")
    relative3 = sorted(
        str(f.relative_to(plugin_dir)).replace("\\", "/") for f in files3
    )
    print("=== Test 3: output_dir='build' ===")
    for f in relative3:
        print(f"  {f}")

    assert "dist/old_build.mfp" in relative3, "FAIL[3]: dist should NOT be excluded when output_dir='build'"
    print("  PASS\n")

    print("All tests passed!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
