# Plan: Tighten MCP Tool JSON Schemas

## TODO

- [x] 1. Inventory and freeze the public MCP contracts for model discovery, model execution, task status/logs, AOI listing, and terrain tools; decide which backend fields are stable enough to expose and document compatibility rules.
- [x] 2. Add a dedicated `mcp_service/schemas.py` containing Pydantic v2 request/response DTOs, shared JSON/value types, constrained identifiers, and `Literal["en", "cn"]` for language. Keep model-specific parameter values open at the outer layer, while making `model_name`, `inputs`, `outputs`, task IDs, pagination fields, and response envelopes explicit.
- [x] 3. Update `mcp_service/egc_service_tools.py` to accept/return the DTOs instead of untyped dictionaries and nullable primitives; normalize `run_model`, `describe_model`, task status, and task log results into stable public shapes. Preserve the existing backend payload conversion behind the tool boundary.
- [x] 4. Update `mcp_service/aoi_tools.py` and `mcp_service/terrain_analysis_tools.py` to use typed DTOs, constrained coordinate/path-or-asset inputs, and explicit result/error semantics. Do not expose arbitrary backend dictionaries or ambiguous sentinel strings such as `"invalid study area"`.
- [x] 5. Add runtime validation for dynamic model parameters using the metadata returned by `describe_model`; reject missing/unknown required parameters with field-level errors while retaining a controlled escape hatch for model extensions.
- [x] 6. Add MCP tool annotations and descriptions that reflect read-only versus side-effecting behavior, required fields, identifiers, units, and examples. Keep production-only tool lists free of debug/diagnostic tools.
- [x] 7. Add schema contract tests that inspect FastMCP-generated input/output JSON Schema, validate representative requests/responses, cover invalid language/coordinates/IDs, and verify backward-compatible normalization of existing backend payloads.
- [x] 8. Update `docs/MCP_EGC_Tools_API_Usage.md` with generated-schema-aligned examples, the two-stage model parameter workflow, structured task responses, and migration notes for clients currently sending `request_body` dictionaries.

## Acceptance Criteria

- `tools/list` exposes explicit required fields, descriptions, enum values, numeric constraints, and stable object properties for every production tool.
- `run_model` no longer advertises an unconstrained top-level `request_body`; its required outer fields are schema-visible, while dynamic model-specific values are validated after metadata discovery.
- Tool return values have one documented shape per operation; upstream failure, not-found, and valid empty results are distinguishable, and declared non-null types cannot receive `None`.
- AOI and terrain tools do not use arbitrary dictionaries or string sentinels for normal error states; coordinates and data references are validated at the MCP boundary.
- Existing valid calls can be normalized without silently changing model identifiers or backend parameter names; any breaking change has a documented compatibility path.
- Contract tests fail if FastMCP schema generation regresses to `additionalProperties: true` for fields intended to be closed, if `lang` loses its enum, or if output schemas become generic again.
- The approved implementation keeps backend model parameter names intact; the existing test suite and new MCP schema tests pass.
