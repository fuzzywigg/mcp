"""Static checks on agent.py (avoids import-time credential side effects)."""

from __future__ import annotations

import ast
import unittest

from tests._support import APP_DIR, read_text

TIP_TABLES = (
    "foot_traffic",
    "demographics",
    "bakery_prices",
    "sales_history_weekly",
)


class AgentSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = read_text(APP_DIR / "agent.py")
        cls.tree = ast.parse(cls.source)

    def test_project_id_default_placeholder(self):
        self.assertIn(
            "os.getenv('GOOGLE_CLOUD_PROJECT', 'project_not_set')",
            self.source,
        )

    def test_instruction_names_all_tip_tables(self):
        for table in TIP_TABLES:
            with self.subTest(table=table):
                self.assertIn(table, self.source)

    def test_root_agent_is_llm_agent_assignment(self):
        assignments = [
            node
            for node in self.tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "root_agent"
                for t in node.targets
            )
        ]
        self.assertEqual(len(assignments), 1)
        call = assignments[0].value
        self.assertIsInstance(call, ast.Call)
        self.assertIsInstance(call.func, ast.Name)
        self.assertEqual(call.func.id, "LlmAgent")

        keywords = {kw.arg: kw.value for kw in call.keywords if kw.arg}
        self.assertIn("model", keywords)
        self.assertIsInstance(keywords["model"], ast.Constant)
        self.assertEqual(keywords["model"].value, "gemini-3-pro-preview")
        self.assertIn("name", keywords)
        self.assertIsInstance(keywords["name"], ast.Constant)
        self.assertEqual(keywords["name"].value, "root_agent")
        self.assertIn("tools", keywords)
        self.assertIsInstance(keywords["tools"], ast.List)
        self.assertEqual(len(keywords["tools"].elts), 2)

    def test_toolsets_constructed_at_module_level(self):
        # Tip wiring: maps + bigquery toolsets are created before root_agent.
        self.assertIn("get_maps_mcp_toolset()", self.source)
        self.assertIn("get_bigquery_mcp_toolset()", self.source)


if __name__ == "__main__":
    unittest.main()
