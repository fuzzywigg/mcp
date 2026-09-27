"""Offline checks for setup/cleanup shell scripts."""

from __future__ import annotations

import subprocess
import unittest

from tests._support import CLEANUP_DIR, SETUP_DIR, read_text

SCRIPTS = (
    SETUP_DIR / "setup_env.sh",
    SETUP_DIR / "setup_bigquery.sh",
    CLEANUP_DIR / "cleanup_env.sh",
)


class ShellScriptTest(unittest.TestCase):
    def test_scripts_exist_and_are_nonempty(self):
        for path in SCRIPTS:
            with self.subTest(script=path.name):
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 0)

    def test_bash_syntax(self):
        for path in SCRIPTS:
            with self.subTest(script=path.name):
                result = subprocess.run(
                    ["bash", "-n", str(path)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    msg=f"{path.name} bash -n failed:\n{result.stderr}",
                )

    def test_setup_env_writes_required_keys(self):
        source = read_text(SETUP_DIR / "setup_env.sh")
        for key in (
            "GOOGLE_GENAI_USE_VERTEXAI",
            "GOOGLE_CLOUD_PROJECT",
            "GOOGLE_CLOUD_LOCATION",
            "MAPS_API_KEY",
        ):
            with self.subTest(key=key):
                self.assertIn(key, source)

    def test_setup_env_enables_expected_services(self):
        source = read_text(SETUP_DIR / "setup_env.sh")
        for service in (
            "aiplatform.googleapis.com",
            "apikeys.googleapis.com",
            "mapstools.googleapis.com",
            "bigquery.googleapis.com",
        ):
            with self.subTest(service=service):
                self.assertIn(service, source)

    def test_setup_bigquery_default_bucket_pattern(self):
        source = read_text(SETUP_DIR / "setup_bigquery.sh")
        self.assertIn('BUCKET_NAME="gs://mcp-bakery-data-$PROJECT_ID"', source)
        self.assertIn('DATASET_NAME="mcp_bakery"', source)

    def test_cleanup_targets_match_setup_defaults(self):
        cleanup = read_text(CLEANUP_DIR / "cleanup_env.sh")
        self.assertIn('DATASET_NAME="mcp_bakery"', cleanup)
        self.assertIn('BUCKET_NAME="gs://mcp-bakery-data-$PROJECT_ID"', cleanup)
        self.assertIn("bakery-demo-key-*", cleanup)


if __name__ == "__main__":
    unittest.main()
