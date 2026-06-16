# SPDX-License-Identifier: Apache-2.0

import json
import tempfile
import unittest
from importlib import metadata
from pathlib import Path

from tools.offline_license_bundle import collect_conda_licenses, collect_pip_licenses


class OfflineLicenseBundleTest(unittest.TestCase):
    def test_collect_conda_licenses_copies_package_cache_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_prefix = root / "env"
            output_root = root / "bundle" / "licenses"
            package_cache = root / "pkgs"
            env_prefix.joinpath("conda-meta").mkdir(parents=True)
            package_dir = package_cache / "demo-1.0-h123_0"
            package_dir.joinpath("info", "licenses").mkdir(parents=True)
            package_dir.joinpath("info", "licenses", "LICENSE").write_text("demo license\n", encoding="utf-8")
            package_dir.joinpath("info", "about.json").write_text('{"license": "MIT"}\n', encoding="utf-8")

            record = {
                "name": "demo",
                "version": "1.0",
                "build": "h123_0",
                "fn": "demo-1.0-h123_0.conda",
                "license": "MIT",
                "license_family": "MIT",
                "channel": "conda-forge",
                "url": "https://example.invalid/demo-1.0.conda",
            }
            env_prefix.joinpath("conda-meta", "demo-1.0-h123_0.json").write_text(
                json.dumps(record),
                encoding="utf-8",
            )

            packages = collect_conda_licenses(env_prefix, output_root, package_cache_dirs=[package_cache])

            self.assertEqual(packages[0]["name"], "demo")
            copied_paths = packages[0]["license_files"]
            self.assertTrue(any(path.endswith("licenses/LICENSE") for path in copied_paths))
            self.assertTrue(any(path.endswith("conda-package-record.json") for path in copied_paths))
            manifest_text = json.dumps(packages)
            self.assertNotIn(str(root), manifest_text)

    def test_collect_pip_licenses_copies_metadata_and_license_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site_packages = root / "site-packages"
            output_root = root / "bundle" / "licenses"
            dist_info = site_packages / "sample_pkg-1.0.dist-info"
            dist_info.mkdir(parents=True)
            dist_info.joinpath("METADATA").write_text(
                "\n".join(
                    [
                        "Metadata-Version: 2.1",
                        "Name: sample-pkg",
                        "Version: 1.0",
                        "Summary: sample package",
                        "License: Apache-2.0",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            dist_info.joinpath("LICENSE").write_text("sample license\n", encoding="utf-8")
            dist_info.joinpath("RECORD").write_text(
                "\n".join(
                    [
                        "sample_pkg-1.0.dist-info/METADATA,,",
                        "sample_pkg-1.0.dist-info/LICENSE,,",
                        "sample_pkg-1.0.dist-info/RECORD,,",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            dists = list(metadata.distributions(path=[str(site_packages)]))
            packages = collect_pip_licenses(output_root, distributions=dists)

            self.assertEqual(packages[0]["name"], "sample-pkg")
            self.assertEqual(packages[0]["license"], "Apache-2.0")
            copied_paths = packages[0]["license_files"]
            self.assertTrue(any(path.endswith("METADATA") for path in copied_paths))
            self.assertTrue(any(path.endswith("licenses/LICENSE") for path in copied_paths))
            manifest_text = json.dumps(packages)
            self.assertNotIn(str(root), manifest_text)


if __name__ == "__main__":
    unittest.main()
