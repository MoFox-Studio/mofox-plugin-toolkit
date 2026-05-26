from __future__ import annotations

import json

from mpdt.utils.managers.manifest_manager import ManifestManager


def test_build_market_version_payload_includes_readme_markdown(tmp_path) -> None:
    plugin_dir = tmp_path / "sample_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "sample_plugin",
                "version": "1.2.3",
                "min_core_version": "1.0.0",
            }
        ),
        encoding="utf-8",
    )
    (plugin_dir / "README.md").write_text("# Sample Plugin\n\nUpdated README.", encoding="utf-8")

    manager = ManifestManager(plugin_dir)
    payload = manager.build_market_version_payload(
        asset_name="sample_plugin-1.2.3.mfp",
        asset_download_url="https://example.com/sample_plugin-1.2.3.mfp",
        release_url="https://example.com/releases/v1.2.3",
        sha256="a" * 64,
        file_size=1234,
    )

    assert payload["readme_markdown"] == "# Sample Plugin\n\nUpdated README."