# Plan: Normalize MCP Result and Error Semantics

## Scope

Fix the mismatch between MCP return annotations and the values produced by the
backend. The MCP boundary must distinguish successful empty data, resource not
found, invalid input, and upstream failures without using `None` as an
ambiguous sentinel.

## Public contract

Use typed Pydantic v2 DTOs at the MCP boundary. Keep backend payloads private to
the adapter layer.

- `get_task_status` returns a non-null object such as
  `{project_id, state, progress, message, updated_at}`. `progress` is optional
  only when the backend explicitly reports an unknown progress value.
- `get_task_log` returns `{project_id, entries, next_cursor}`. A valid empty log
  is `entries: []`; it is never `None`.
- `describe_model` returns a discriminated result with `outcome: "found"` and
  `model`, or `outcome: "not_found"`, `model_name`, and optional suggestions.
- `list_models_by_category` returns a normal empty page for a valid category
  with no models. An unknown category is an `invalid_argument` tool error.
- Invalid arguments are rejected at the MCP boundary or raised as a domain
  tool error with a stable code and field details.
- Timeouts, transport failures, HTTP 5xx, malformed upstream JSON, and backend
  `success: false` responses become upstream/protocol tool errors with a
  retryable flag where appropriate. They must not become empty lists or `None`.

## TODO

- [ ] 1. Add shared DTOs and error types in `mcp_service/schemas.py` and
  `mcp_service/errors.py`. Include task status/log entries, model lookup
  outcomes, error codes, retryability, and a safe details map. Use explicit
  `Literal`/enum values and discriminators where an operation has a
  `found`/`not_found` outcome.
- [ ] 2. Refactor `pygeomodels/api.py` and `mcp_service/inner_api.py` so
  `restapi_get`/`restapi_post` no longer catch every exception and return
  `None`. Catch only transport, timeout, HTTP-status, JSON-decoding, and
  protocol errors; wrap them in a typed upstream exception while preserving
  status/code/message and the original cause. Never include bearer tokens in
  the error details.
- [ ] 3. Update `modelTask.py` to normalize successful backend data into
  task DTOs and raise typed errors for request failure, `success: false`,
  missing task, or malformed data. Treat an explicitly successful empty log
  as `[]`. Update `modelBank.py` callers so an upstream outage cannot populate
  an empty cache or be mistaken for an empty catalog.
- [ ] 4. Update `mcp_service/egc_service_tools.py` at the MCP boundary:
  return the DTOs above, convert an unknown model into a structured
  `not_found` outcome, validate categories before querying, and map typed
  upstream/domain exceptions to MCP tool errors. Remove `Optional` primitive
  returns from status/log tools. Keep `debug_token_tool` out of the production
  registration path.
- [ ] 5. Decide and document the compatibility path for clients that currently
  expect a raw integer, raw list, or `None`. Prefer versioned result shapes or
  a documented one-time contract change; do not silently return two unrelated
  shapes from the same tool.
- [ ] 6. Add unit and contract tests. Inspect generated FastMCP schemas and
  assert status/log outputs are non-null objects, `entries` is an array,
  `outcome` has the expected enum, and no generic `additionalProperties` object
  is used where the contract is closed. Test valid empty data, not-found,
  invalid category, timeout, HTTP 401/404/500, malformed JSON, and backend
  `success: false`. Assert MCP error responses are marked `isError` and do not
  expose tokens, URLs, or raw exception traces.
- [ ] 7. Update `docs/MCP_EGC_Tools_API_Usage.md` with the new response
  examples, error-code table, retry guidance, and migration notes.

## Acceptance Criteria

- `get_task_status` and `get_task_log` cannot produce an undeclared `None` on
  any successful code path; their generated output schemas match the DTOs.
- `describe_model` exposes a machine-readable `found`/`not_found` result, and
  a valid empty model list remains distinguishable from an invalid category.
- A network timeout, HTTP error, malformed response, or backend failure is
  surfaced as an MCP tool error with a stable code and retryability; no layer
  converts it into an empty result.
- Existing backend payloads are normalized in one adapter layer, with no
  bearer token or sensitive upstream details in client-visible errors.
- The existing tests plus the new MCP contract tests pass, and the generated
  schemas remain stable under future refactors.

