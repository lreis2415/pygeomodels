# Plan: Add MCP Tool for Querying Model Categories

## Background

Remove the hardcoded `SUPPORTED_CATEGORIES` list. Instead, fetch categories dynamically from the `catalog/categories` API endpoint, cache them in `modelBank`, and expose via an MCP tool. This way the system auto-discovers available categories.

## TODO

- [x] 1. Add category fetching & caching to `modelBank` (`pygeomodels/modelBank.py`)
  - Add `_categories` cache field (token-gated like other caches)
  - Add `get_categories()` / `set_categories()` methods
  - `set_categories()` calls REST API: `{host}/{api_basename}/{api_cls_modelmanager}/{api_mgt_generalmodel}/{api_gm_catalogcls}`
  - Parse response into a list of category dicts (e.g. `[{"category_id": "basic", "category_name": "..."}, ...]`)
  - `get_models_ids()` should use `self._categories` instead of the removed `self._category_ids` to iterate categories

- [x] 2. Remove hardcoded `SUPPORTED_CATEGORIES` from `mcp_service/egc_service_tools.py`
  - Remove `SUPPORTED_CATEGORIES` list (lines 13-18)
  - `initialize()` no longer passes `category_ids` to `modelBank(cfg, ...)`

- [x] 3. Add `list_categories` MCP tool in `mcp_service/egc_service_tools.py`
  - Register inside `register_model_tools()`
  - Call `mb.get_categories(access_token)` — uses cache if available, fetches once otherwise
  - Docstring: "Returns all available model categories"

## Acceptance Criteria

- No hardcoded category list — categories come from the API
- `list_categories` MCP tool returns categories from cache (0 extra requests after init)
- `list_models` still works — loads models per category from the dynamically fetched list
- Existing tools (`describe_model`, `run_model`, etc.) remain unaffected
