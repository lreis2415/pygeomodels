"""
Unit tests for modelBank cache mechanism (Phase 1 optimization).

Tests the lightweight model listing cache that avoids 158 serial /info calls.
"""

import unittest
from configparser import ConfigParser
from unittest.mock import MagicMock, patch

from pygeomodels.config import ModelEngineConfig
from pygeomodels.modelBank import modelBank


def _make_mock_cfg():
    """Build a minimal ModelEngineConfig for unit testing."""
    cf = ConfigParser()
    cf.add_section("AUTH")
    cf.set("AUTH", "usernames", "testuser")
    cf.set("AUTH", "passwords", "testpass")
    cf.set("AUTH", "keycloak_url", "https://fake.keycloak/")
    cf.set("AUTH", "realm_name", "test")
    cf.set("AUTH", "client_id", "test-client")
    cf.set("AUTH", "client_secret_key", "test-secret")

    cf.add_section("SERVICE")
    cf.set("SERVICE", "modelmanager_url", "http://fake-modelmanager:7504")
    cf.set("SERVICE", "api_basename", "mbms/v1")
    cf.set("SERVICE", "api_cls_modelmanager", "model-manager")
    cf.set("SERVICE", "api_mgt_generalmodel", "general-models")
    cf.set("SERVICE", "api_gm_catalog", "catalog")
    cf.set("SERVICE", "api_gm_catalogcls", "catalog-classes")
    cf.set("SERVICE", "api_gm_catalogappl", "catalog-apply")
    cf.set("SERVICE", "api_mgt_singlemodel", "general-single-models")
    cf.set("SERVICE", "api_sm_list", "list")
    cf.set("SERVICE", "api_sm_info", "info")
    cf.set("SERVICE", "api_sm_ui", "ui")
    cf.set("SERVICE", "api_cls_runner", "runner")
    cf.set("SERVICE", "api_run_singlemodel", "single-model")
    cf.set("SERVICE", "api_srun_run", "run")
    cf.set("SERVICE", "api_srun_task", "task")
    cf.set("SERVICE", "api_srunt_stop", "stop")
    cf.set("SERVICE", "api_srunt_del", "del")
    cf.set("SERVICE", "api_srunt_info", "info")
    cf.set("SERVICE", "api_srunt_log", "log")
    cf.set("SERVICE", "api_cls_usrprj", "user-project")
    cf.set("SERVICE", "api_uprj_list", "list")
    cf.set("SERVICE", "api_uprj_data", "data")
    cf.set("SERVICE", "api_uprj_log", "log")
    cf.set("SERVICE", "api_uprj_detail", "detail")
    cf.set("SERVICE", "api_uprj_prog", "progress")
    cf.set("SERVICE", "api_uprj_stop", "stop")
    cf.set("SERVICE", "api_uprj_del", "del")
    cf.set("SERVICE", "api_uprj_single", "single")
    cf.set("SERVICE", "api_sprj_run", "run")

    return ModelEngineConfig(cf)


# Sample mock API responses
MOCK_CATEGORIES = {
    "success": "true",
    "data": {
        "categories": [
            {
                "id": "modelbank",
                "categories": [
                    {"id": "basic"},
                    {"id": "advanced"},
                ],
            }
        ]
    },
}

MOCK_LIST_BASIC = {
    "success": "true",
    "data": {
        "content": [
            {
                "model_id": "model-001",
                "model_unique_abbr": "abbr_one",
                "identification": {
                    "model_name": "Model One",
                    "description": "First test model",
                },
                "categoryName": "basic",
            },
            {
                "model_id": "model-002",
                "model_unique_abbr": "abbr_two",
                "identification": {
                    "model_name": "Model Two",
                    "description": "Second test model",
                },
                "categoryName": "basic",
            },
        ]
    },
}

MOCK_LIST_ADVANCED = {
    "success": "true",
    "data": {
        "content": [
            {
                "model_id": "model-003",
                "model_unique_abbr": "",
                "identification": {
                    "model_name": "Model Three",
                    "description": "Third test model (no abbr)",
                },
                "categoryName": "advanced",
            },
        ]
    },
}

# /list response without model_unique_abbr (simulating old backend)
MOCK_LIST_NO_ABBR = {
    "success": "true",
    "data": {
        "content": [
            {
                "model_id": "model-004",
                "identification": {
                    "model_name": "Model Four",
                    "description": "Fourth test model",
                },
                "categoryName": "basic",
            },
        ]
    },
}

# /info response (for describe_model / list_all_models compatibility tests)
MOCK_INFO_001 = {
    "success": "true",
    "data": {
        "model_unique_abbr": "abbr_one",
        "identification": {
            "model_name": "Model One",
            "description": "First test model detailed",
        },
        "parameter_info": {"parameters": []},
    },
}

MOCK_INFO_002 = {
    "success": "true",
    "data": {
        "model_unique_abbr": "abbr_two",
        "identification": {
            "model_name": "Model Two",
            "description": "Second test model detailed",
        },
        "parameter_info": {"parameters": []},
    },
}

MOCK_INFO_003 = {
    "success": "true",
    "data": {
        "model_unique_abbr": "",
        "identification": {
            "model_name": "Model Three",
            "description": "Third test model detailed",
        },
        "parameter_info": {"parameters": []},
    },
}


class TestModelBankLightweightCache(unittest.TestCase):
    """Test the lightweight model listing cache (Phase 1 optimization)."""

    def setUp(self):
        self.cfg = _make_mock_cfg()

    @patch("pygeomodels.modelBank.restapi_get")
    def test_basic_info_populated_from_list(self, mock_get):
        """_load_models_by_category should cache basic info from /list response."""
        mock_get.side_effect = [MOCK_CATEGORIES, MOCK_LIST_BASIC, MOCK_LIST_ADVANCED]

        mb = modelBank(self.cfg)
        mb.set_models_ids("token123", lang="en")

        # Check all model IDs are loaded
        self.assertIn("model-001", mb._models_ids)
        self.assertIn("model-002", mb._models_ids)
        self.assertIn("model-003", mb._models_ids)

        # Check basic info cache is populated
        self.assertIn("model-001", mb._models_basic_info)
        self.assertEqual(
            mb._models_basic_info["model-001"]["display_name"], "Model One"
        )
        self.assertEqual(
            mb._models_basic_info["model-001"]["description"], "First test model"
        )
        self.assertEqual(
            mb._models_basic_info["model-001"]["model_unique_abbr"], "abbr_one"
        )
        self.assertEqual(mb._models_basic_info["model-001"]["category_name"], "basic")

        # Model without model_unique_abbr should still be cached
        self.assertIn("model-003", mb._models_basic_info)
        self.assertEqual(mb._models_basic_info["model-003"]["model_unique_abbr"], "")

        # Token and lang should be set
        self.assertEqual(mb._basic_info_token, "token123")
        self.assertEqual(mb._basic_info_lang, "en")

    @patch("pygeomodels.modelBank.restapi_get")
    def test_lightweight_listing_no_info_calls(self, mock_get):
        """list_all_models_lightweight should NOT call /info endpoints."""
        mock_get.side_effect = [MOCK_CATEGORIES, MOCK_LIST_BASIC, MOCK_LIST_ADVANCED]

        mb = modelBank(self.cfg)
        mb.set_models_ids("token123", lang="en")

        # Reset mock to verify no further HTTP calls
        mock_get.reset_mock()

        result = mb.list_all_models_lightweight("token123", category="basic", lang="en")

        # Verify no /info calls were made (mock_get should not be called)
        mock_get.assert_not_called()

        # Verify returned data
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["model_id"], "model-001")
        self.assertEqual(result[0]["display_name"], "Model One")
        self.assertEqual(result[0]["description"], "First test model")
        self.assertEqual(result[0]["model_unique_abbr"], "abbr_one")
        self.assertEqual(result[0]["category_name"], "basic")

    @patch("pygeomodels.modelBank.restapi_get")
    def test_lightweight_listing_category_filtering(self, mock_get):
        """Category parameter should filter results correctly."""
        mock_get.side_effect = [MOCK_CATEGORIES, MOCK_LIST_BASIC, MOCK_LIST_ADVANCED]

        mb = modelBank(self.cfg)
        mb.set_models_ids("token123", lang="en")

        # Filter by 'advanced' category
        result = mb.list_all_models_lightweight(
            "token123", category="advanced", lang="en"
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["model_id"], "model-003")
        self.assertEqual(result[0]["display_name"], "Model Three")

    @patch("pygeomodels.modelBank.restapi_get")
    def test_no_abbr_not_included(self, mock_get):
        """model_unique_abbr should be omitted from result when empty/missing."""
        mock_get.side_effect = [MOCK_CATEGORIES, MOCK_LIST_BASIC, MOCK_LIST_ADVANCED]

        mb = modelBank(self.cfg)
        mb.set_models_ids("token123", lang="en")

        result = mb.list_all_models_lightweight(
            "token123", category="advanced", lang="en"
        )

        # Model Three has empty model_unique_abbr, should not include key
        self.assertNotIn("model_unique_abbr", result[0])

    @patch("pygeomodels.modelBank.restapi_get")
    def test_cache_invalidation_on_token_change(self, mock_get):
        """Cache should reload when token changes."""
        # First load with token123
        mock_get.side_effect = [MOCK_CATEGORIES, MOCK_LIST_BASIC, MOCK_LIST_ADVANCED]
        mb = modelBank(self.cfg)
        mb.set_models_ids("token123", lang="en")

        # Reset and set up for token456
        mock_get.reset_mock()
        mock_get.side_effect = [
            MOCK_CATEGORIES,
            MOCK_LIST_BASIC,
            MOCK_LIST_ADVANCED,
        ]

        # Request with different token should trigger reload
        result = mb.list_all_models_lightweight("token456", category="basic")

        # Verify reload happened (categories + 2 model lists called)
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(result[0]["model_id"], "model-001")
        self.assertEqual(mb._basic_info_token, "token456")

    @patch("pygeomodels.modelBank.restapi_get")
    def test_cache_invalidation_on_lang_change(self, mock_get):
        """Cache should reload when language changes."""
        mock_get.side_effect = [MOCK_CATEGORIES, MOCK_LIST_BASIC, MOCK_LIST_ADVANCED]
        mb = modelBank(self.cfg)
        mb.set_models_ids("token123", lang="en")

        # Reset and set up for lang='cn'
        mock_get.reset_mock()
        mock_get.side_effect = [
            MOCK_CATEGORIES,
            MOCK_LIST_BASIC,
            MOCK_LIST_ADVANCED,
        ]

        _ = mb.list_all_models_lightweight("token123", category="basic", lang="cn")

        # Verify reload happened
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(mb._basic_info_lang, "cn")

    @patch("pygeomodels.modelBank.restapi_get")
    def test_list_all_models_still_works(self, mock_get):
        """list_all_models (original) should still work with /info calls."""
        mock_get.side_effect = [
            MOCK_CATEGORIES,
            MOCK_LIST_BASIC,
            MOCK_LIST_ADVANCED,
            MOCK_INFO_001,
            MOCK_INFO_002,
            MOCK_INFO_003,
        ]

        mb = modelBank(self.cfg)
        result = mb.list_all_models("token123", category="basic")

        # list_all_models uses model_unique_abbr as model_name
        model_names = {m["model_name"] for m in result}
        self.assertIn("abbr_one", model_names)
        self.assertIn("abbr_two", model_names)

    @patch("pygeomodels.modelBank.restapi_get")
    def test_empty_list_response_handled(self, mock_get):
        """Gracefully handle empty /list response (no crash)."""
        empty_list = {"success": "true", "data": {"content": []}}
        mock_get.side_effect = [MOCK_CATEGORIES, empty_list, empty_list]

        mb = modelBank(self.cfg)
        mb.set_models_ids("token123", lang="en")

        result = mb.list_all_models_lightweight("token123", category="basic")
        self.assertEqual(result, [])
        self.assertEqual(mb._models_basic_info, {})

    @patch("pygeomodels.modelBank.restapi_get")
    def test_failed_list_response_handled(self, mock_get):
        """Gracefully handle failed /list response (no crash)."""
        # The code treats non-empty success strings as truthy, so we simulate
        # a response where success is an empty/falsey value
        failed_list = {
            "success": False,
            "message": "Internal error",
            "data": {"content": []},
        }
        mock_get.side_effect = [MOCK_CATEGORIES, failed_list, failed_list]

        mb = modelBank(self.cfg)
        mb.set_models_ids("token123", lang="en")

        self.assertEqual(mb._models_ids, [])
        self.assertEqual(mb._models_basic_info, {})

    @patch("pygeomodels.modelBank.restapi_get")
    def test_missing_identification_field(self, mock_get):
        """Handle models without identification field (graceful fallback)."""
        no_identification = {
            "success": "true",
            "data": {
                "content": [
                    {
                        "model_id": "model-005",
                        "categoryName": "basic",
                    }
                ]
            },
        }
        mock_get.side_effect = [MOCK_CATEGORIES, no_identification, MOCK_LIST_ADVANCED]

        mb = modelBank(self.cfg)
        mb.set_models_ids("token123", lang="en")

        info = mb._models_basic_info["model-005"]
        self.assertEqual(info["display_name"], "")
        self.assertEqual(info["description"], "")
        self.assertEqual(info["model_unique_abbr"], "")

    @patch("pygeomodels.modelBank.restapi_get")
    def test_categories_cache_reset_invalidates_basic_info(self, mock_get):
        """set_categories should invalidate basic info cache."""
        mock_get.side_effect = [MOCK_CATEGORIES, MOCK_LIST_BASIC, MOCK_LIST_ADVANCED]
        mb = modelBank(self.cfg)
        mb.set_models_ids("token123", lang="en")

        self.assertTrue(len(mb._models_basic_info) > 0)

        # Reset mock for set_categories call
        mock_get.reset_mock()
        mock_get.side_effect = [MOCK_CATEGORIES]

        mb.set_categories("token123", lang="en")

        # Cache should be invalidated
        self.assertEqual(mb._models_basic_info, {})
        self.assertIsNone(mb._basic_info_token)
        self.assertIsNone(mb._basic_info_lang)

    @patch("pygeomodels.modelBank.restapi_get")
    def test_lightweight_auto_loads_on_first_call(self, mock_get):
        """First call to list_all_models_lightweight should trigger loading."""
        mock_get.side_effect = [MOCK_CATEGORIES, MOCK_LIST_BASIC, MOCK_LIST_ADVANCED]

        mb = modelBank(self.cfg)
        result = mb.list_all_models_lightweight("token123", category="basic")

        # Should have made 3 API calls (categories + 2 model lists)
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(len(result), 2)
        self.assertEqual(mb._basic_info_token, "token123")

    @patch("pygeomodels.modelBank.restapi_get")
    def test_describe_model_uses_single_info_call(self, mock_get):
        """describe_model should use only 1 /info call via basic_info cache lookup."""
        mock_get.side_effect = [
            MOCK_CATEGORIES,
            MOCK_LIST_BASIC,
            MOCK_LIST_ADVANCED,
            MOCK_INFO_001,  # single /info for abbr_one
        ]

        mb = modelBank(self.cfg)
        mb.set_models_ids("token123", lang="en")

        # describe_model should find model-001 via basic_info cache, then call 1 /info
        result = mb.describe_model("abbr_one", "token123", lang="en")

        # Total: categories(1) + 2 model lists + 1 info = 4 calls
        self.assertEqual(mock_get.call_count, 4)
        self.assertIsNotNone(result)
        self.assertEqual(result["model_name"], "abbr_one")
        self.assertIn("run_template", result)
        self.assertIn("parameter_info", result)

    @patch("pygeomodels.modelBank.restapi_get")
    def test_describe_model_fallback_when_no_abbr_in_basic_info(self, mock_get):
        """When basic_info lacks model_unique_abbr, fall back to full metadata load."""
        # /list returns models without model_unique_abbr (old backend),
        # so basic_info cache entries have empty model_unique_abbr
        mock_get.side_effect = [
            MOCK_CATEGORIES,
            MOCK_LIST_NO_ABBR,
            MOCK_LIST_ADVANCED,
            # Fallback: set_models_metadata loads /info for model-004 and model-003
            {
                "success": "true",
                "data": {
                    "model_unique_abbr": "abbr_four",
                    "identification": {"model_name": "M4", "description": "Desc 4"},
                    "parameter_info": {"parameters": []},
                },
            },
            {
                "success": "true",
                "data": {
                    "model_unique_abbr": "",
                    "identification": {"model_name": "M3", "description": "Desc 3"},
                    "parameter_info": {"parameters": []},
                },
            },
        ]

        mb = modelBank(self.cfg)
        mb.set_models_ids("token123", lang="en")

        # basic_info has empty abbr for model-004, so lookup fails, triggers fallback
        result = mb.describe_model("abbr_four", "token123", lang="en")

        # 1(categories) + 2(model lists) + 2(/info fallback for model-004, model-003) = 5
        self.assertEqual(mock_get.call_count, 5)
        self.assertIsNotNone(result)
        self.assertEqual(result["model_name"], "abbr_four")

    @patch("pygeomodels.modelBank.restapi_get")
    def test_describe_model_unknown_model_returns_none(self, mock_get):
        """describe_model should return None for unknown model names."""
        mock_get.side_effect = [
            MOCK_CATEGORIES,
            MOCK_LIST_BASIC,
            MOCK_LIST_ADVANCED,
            MOCK_INFO_001,
            MOCK_INFO_002,
            MOCK_INFO_003,
        ]

        mb = modelBank(self.cfg)
        mb.set_models_ids("token123", lang="en")

        # "nonexistent" not in any basic_info entry nor /info metadata
        result = mb.describe_model("nonexistent", "token123", lang="en")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
