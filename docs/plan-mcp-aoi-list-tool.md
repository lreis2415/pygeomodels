# Plan: Add MCP Tool for Querying Study Area (AOI) List

## Background

Encapsulate the `GET /aoi/list/data` API (Apifox interface ID: 214312745) as an MCP tool.
The AOI API shares the same host as other services — `modelmanager_url` is used as the base URL.
Only a path config key is needed, following the existing `[SERVICE]` pattern.

API details:
- Method: `GET`
- URL: `{modelmanager_url}/aoi/list/data`
- Auth: Bearer token (reuses `call_inner_api`)
- No query parameters
- Response: `{ "success": bool, "code": int, "message": str, "data": [{ aoiId, studyAreaName, dataWithPathList }] }`

## TODO

- [ ] 1. Add AOI path config to `pygeomodels/default_config.ini` `[SERVICE]` section
  - `aoi_list_data_path = aoi/list/data`

- [ ] 2. Parse `aoi_list_data_path` in `pygeomodels/config.py` `ModelEngineConfig.__init__`
  - Add `self.aoi_list_data_path` (same `get_option_value` pattern as other `[SERVICE]` keys)
  - Default to empty string for backward compatibility

- [ ] 3. Add `enable_aoi_tools` feature flag
  - Parse from `[FEATURE_FLAGS]` in `ModelEngineConfig.__init__`, default `false`
  - Add `enable_aoi_tools = true` to `default_config.ini` and `local_config.ini`

- [ ] 4. Create `mcp_service/aoi_tools.py`
  - `register_aoi_tools(mcp)` with lazy `initialize()` (same pattern as `egc_service_tools.py`)
  - `list_study_areas` MCP tool: calls `GET {modelmanager_url}/{aoi_list_data_path}` via `call_inner_api`
  - Returns parsed `data` list from response

- [ ] 5. Register AOI tools in `pygeomodels_service.py`
  - Add `ENABLE_AOI_TOOLS()` feature flag function
  - Conditionally import and call `register_aoi_tools(mcp)`

## Acceptance Criteria

- `list_study_areas` uses `cfg.modelmanager_url` + `cfg.aoi_list_data_path` to build request URL
- Only one new config key: `aoi_list_data_path` in `[SERVICE]`
- Reuses `call_inner_api()` for authenticated HTTP calls
- Feature flag controls tool registration
- Existing tools unaffected
