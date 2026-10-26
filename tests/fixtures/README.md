# Generated scalar-union test fixture

`scalarunionfixture.swagger.json` is an authored, synthetic Swagger 2.0
contract. It is **not** a live connector definition. The Python generator
emitted the complete `scalarunionfixture.py` module from that exact input.
Do not infer scalar-only values from the distinct, empty `dynamicValues`
schema; the `structured` map is object-valued. `ScalarItem` also tests
scalar unions reached through a definition reference in a map and a field.

Generator base: AzureUX-BPM `ece2097232d306965d6886ea7a6c4b0857130b7a`
plus the uncommitted Python scalar-union generator changes on
`fix/scalar-only-python-dotnet`. The source file SHA-256 values at generation:

- `DirectClientPythonGenerator.cs`: `cdd4d2560115a4cf4ffa751d7d4570c141434cc70f3fe3bcd9c374fa66183145`
- `DirectClientPythonCodeGenerator.cs`: `33195dcf6e7d507994d3162385481fbb96585e8d5206dfd92133f1090491f2cf`
- Input `.swagger.json`: `e0060ea3f7fb14d08f0cd3f71f1cf0ac94ad7d9edb1c7617467b8c3222f6521c`
- Generated `.py`: `03176ed09f045f23783090f53ea15e8418486a29fa57e943e893f65ae7c4d667`

From the BPM repository, build `LogicAppsCompiler.Cli` and run:

```powershell
LogicAppsCompiler.exe <output-directory> --directClient --language=python     --connectors=scalarunionfixture     --swagger-input-directory=<python-sdk>/tests/fixtures
```

The SDK tests import the emitted model, compile the full module, exercise
runtime value checks and wire serialization, and type-check valid and invalid
consumers. The generated operation method currently needs the separate Azure
Core migration (#103): it calls `ConnectorHttpClient.send`, while the Python
SDK on `main` exposes `send_async`. The fixture does not claim to test an HTTP
call. Live production regeneration and its hashes are tracked separately;
this synthetic input does not replace fresh managed-API downloads.
