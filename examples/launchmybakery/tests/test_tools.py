"""Unit tests for mcp_bakery_app.tools (mocked ADK; no live credentials)."""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from tests._support import load_tools_module


class ToolsConstantsTest(unittest.TestCase):
    def test_mcp_endpoint_urls(self):
        tools = load_tools_module()
        self.assertEqual(
            tools.MAPS_MCP_URL, "https://mapstools.googleapis.com/mcp"
        )
        self.assertEqual(
            tools.BIGQUERY_MCP_URL, "https://bigquery.googleapis.com/mcp"
        )


class GetMapsMcpToolsetTest(unittest.TestCase):
    def test_uses_maps_api_key_from_env(self):
        tools = load_tools_module()
        fake_toolset = object()
        with patch.object(tools, "MCPToolset", return_value=fake_toolset) as mock_toolset, patch.object(
            tools, "StreamableHTTPConnectionParams"
        ) as mock_params, patch.dict(
            os.environ, {"MAPS_API_KEY": "test-maps-key"}, clear=False
        ):
            result = tools.get_maps_mcp_toolset()

        self.assertIs(result, fake_toolset)
        mock_params.assert_called_once_with(
            url="https://mapstools.googleapis.com/mcp",
            headers={"X-Goog-Api-Key": "test-maps-key"},
        )
        mock_toolset.assert_called_once()
        kwargs = mock_toolset.call_args.kwargs
        self.assertIs(kwargs["connection_params"], mock_params.return_value)

    def test_missing_maps_api_key_uses_placeholder(self):
        tools = load_tools_module()
        env = {k: v for k, v in os.environ.items() if k != "MAPS_API_KEY"}
        with patch.object(tools, "MCPToolset") as mock_toolset, patch.object(
            tools, "StreamableHTTPConnectionParams"
        ) as mock_params, patch.dict(os.environ, env, clear=True):
            tools.get_maps_mcp_toolset()

        mock_params.assert_called_once_with(
            url="https://mapstools.googleapis.com/mcp",
            headers={"X-Goog-Api-Key": "no_api_found"},
        )
        mock_toolset.assert_called_once()


class GetBigQueryMcpToolsetTest(unittest.TestCase):
    def test_builds_oauth_headers_from_default_credentials(self):
        tools = load_tools_module()
        fake_creds = MagicMock()
        fake_creds.token = "oauth-token-123"
        fake_toolset = object()
        fake_request = MagicMock(name="RequestInstance")
        fake_request_cls = MagicMock(return_value=fake_request)

        # tools.py calls google.auth.default / google.auth.transport.requests.Request
        fake_transport = MagicMock()
        fake_transport.requests.Request = fake_request_cls
        fake_auth = MagicMock()
        fake_auth.default.return_value = (fake_creds, "demo-project")
        fake_auth.transport = fake_transport
        fake_google = MagicMock()
        fake_google.auth = fake_auth

        with patch.object(tools, "google", fake_google), patch.object(
            tools, "MCPToolset", return_value=fake_toolset
        ) as mock_toolset, patch.object(
            tools, "StreamableHTTPConnectionParams"
        ) as mock_params:
            result = tools.get_bigquery_mcp_toolset()

        self.assertIs(result, fake_toolset)
        fake_auth.default.assert_called_once_with(
            scopes=["https://www.googleapis.com/auth/bigquery"]
        )
        fake_creds.refresh.assert_called_once_with(fake_request)
        fake_request_cls.assert_called_once_with()
        mock_params.assert_called_once_with(
            url="https://bigquery.googleapis.com/mcp",
            headers={
                "Authorization": "Bearer oauth-token-123",
                "x-goog-user-project": "demo-project",
            },
        )
        mock_toolset.assert_called_once()


if __name__ == "__main__":
    unittest.main()
