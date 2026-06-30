---
applyTo: "src/azure/connectors/*.py"
---
# Connector Code Maintenance

## Generated Code Rules

Generated connector files in `src/azure/connectors/` are read-only. Do NOT hand-edit generated files. If the generated code has bugs:

1. Fix the generator in BPM repo (`src/tools/CodefulSdkGenerator/DirectClient/DirectClientPythonCodeGenerator.cs`)
2. Regenerate the connector
3. Add the defect to the Known Generator Defects Registry in `GENERATION.md`

See `GENERATION.md` for:
- **Generated Client Acceptance Criteria** — invariants every generated client must satisfy
- **Generator File Locations** — BPM repo paths for fixing generator bugs
- **Known Generator Defects Registry** — tracking known issues

## Validation Checklist

When a new connector module is added to `src/azure/connectors/`:

1. Run the code quality tests: `pytest tests/test_code_quality.py -v`
2. Update the supported SDK connector names list in `.github/skills/connection-setup/SKILL.md` (Step 2)
3. Update the validated connectors table in `README.md`
4. Ensure unit tests cover:
   - Request body assertions for create/update operations
   - Error handling (non-2xx raises `ConnectorException`) for all operations including void ones
