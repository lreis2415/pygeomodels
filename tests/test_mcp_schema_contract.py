import unittest

from fastmcp import FastMCP
from pydantic import ValidationError

from mcp_service.aoi_tools import register_aoi_tools
from mcp_service.egc_service_tools import (
    _normalize_model_description,
    _normalize_task_log,
    _normalize_task_status,
    _validate_dynamic_parameters,
    register_model_tools,
)
from mcp_service.schemas import ModelDescription, RunModelRequest

try:
    from mcp_service.terrain_analysis_tools import register_terrain_tools
except ModuleNotFoundError as exc:
    if exc.name != "osgeo":
        raise
    register_terrain_tools = None


class TestMCPToolSchemaContract(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mcp = FastMCP("schema-test")
        register_model_tools(self.mcp)
        register_aoi_tools(self.mcp)
        if register_terrain_tools is not None:
            register_terrain_tools(self.mcp)
        self.tools = {tool.name: tool for tool in await self.mcp.list_tools()}

    async def test_run_model_schema_has_explicit_outer_fields(self):
        schema = self.tools["run_model"].parameters
        request_schema = schema["properties"]["request"]

        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(request_schema["additionalProperties"])
        self.assertEqual(
            request_schema["required"], ["model_name", "inputs", "outputs"]
        )
        self.assertEqual(request_schema["properties"]["inputs"]["minProperties"], 1)
        self.assertEqual(request_schema["properties"]["outputs"]["minProperties"], 1)

    async def test_language_and_coordinate_constraints_are_visible(self):
        lang_schema = self.tools["list_categories"].parameters["properties"]["lang"]

        self.assertEqual(lang_schema["enum"], ["en", "cn"])
        if register_terrain_tools is None:
            self.skipTest("GDAL/osgeo is not installed")
        bbox_schema = self.tools["get_dem_by_bbox"].parameters["properties"]
        self.assertEqual(bbox_schema["min_lon"]["minimum"], -180)
        self.assertEqual(bbox_schema["max_lat"]["maximum"], 90)

    async def test_outputs_are_structured_and_debug_tool_is_not_registered(self):
        self.assertNotIn("debug_token_tool", self.tools)
        status_schema = self.tools["get_task_status"].output_schema
        log_schema = self.tools["get_task_log"].output_schema
        aoi_schema = self.tools["list_study_areas"].output_schema
        self.assertIn("progress", status_schema["properties"])
        self.assertIn("entries", log_schema["properties"])
        self.assertIn("aoiId", aoi_schema["properties"]["result"]["items"]["properties"])
        self.assertEqual(self.tools["run_model"].annotations.readOnlyHint, False)


class TestMCPDTOValidation(unittest.TestCase):
    def test_run_request_requires_non_empty_inputs_and_outputs(self):
        with self.assertRaises(ValidationError):
            RunModelRequest(model_name="demo", inputs={}, outputs={"out": "x"})
        with self.assertRaises(ValidationError):
            RunModelRequest(model_name="demo", inputs={"in": "x"}, outputs={})

    def test_legacy_model_description_is_normalized(self):
        result = _normalize_model_description(
            "demo",
            {
                "description": "Demo model",
                "run_template": {"inputs": {"dem": "in.tif"}},
                "parameter_info": {
                    "parameters": [
                        {
                            "arg_name": "dem",
                            "param_type": "input_data",
                            "required": True,
                            "data_type": "tif",
                        }
                    ]
                },
            },
        )
        self.assertEqual(result.model_name, "demo")
        self.assertTrue(result.parameter_info.parameters[0].required)
        self.assertEqual(result.run_template.inputs["dem"], "in.tif")

    def test_task_payloads_are_normalized(self):
        status = _normalize_task_status("p1", {"progress": 25, "status": "running"})
        self.assertEqual(status.project_id, "p1")
        self.assertEqual(status.progress, 25)
        self.assertEqual(status.state, "running")

        log = _normalize_task_log(
            "p1",
            [{"time": "2026-08-08T00:00:00Z", "severity": "info", "msg": "ok"}],
        )
        self.assertEqual(log.project_id, "p1")
        self.assertEqual(log.entries[0].message, "ok")

    def test_dynamic_model_parameters_are_checked_after_discovery(self):
        description = ModelDescription.model_validate(
            {
                "model_name": "demo",
                "run_template": {"model_name": "demo"},
                "parameter_info": {
                    "parameters": [
                        {"arg_name": "dem", "param_type": "input_data", "required": True},
                        {"arg_name": "out", "param_type": "output_data", "required": True},
                    ]
                },
            }
        )
        with self.assertRaisesRegex(ValueError, "Missing required"):
            _validate_dynamic_parameters(
                RunModelRequest(model_name="demo", inputs={"dem": "in.tif"}, outputs={"x": "out.tif"}),
                description,
            )
        with self.assertRaisesRegex(ValueError, "Unknown model parameters"):
            _validate_dynamic_parameters(
                RunModelRequest(model_name="demo", inputs={"dem": "in.tif"}, outputs={"out": "out.tif", "x": "x"}),
                description,
            )
