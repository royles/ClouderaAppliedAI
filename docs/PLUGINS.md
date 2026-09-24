# Pluggable control tools

Each catalog control is exposed as an **LLM-callable tool** with JSON Schema inputs/outputs and a **simulator** that maps inputs → outputs deterministically.

## Architecture

| Layer | Module | Role |
| --- | --- | --- |
| **Protocols** | `banking_control.plugins.protocols` | `SchemaProvider`, `ControlSimulator`, `BankingControlPlugin` |
| **Registry** | `banking_control.plugins.manager.PluginManager` | Resolves providers/simulators by priority |
| **Built-ins** | `banking_control.plugins.builtins` | Default EU schemas + simulators |
| **Engine** | `banking_control.tools.engine.ControlToolEngine` | Validate → simulate → validate |
| **HTTP** | `banking_control.api.routers.tools` | REST surface for agents |
| **App factory** | `banking_control.api.factory.create_app()` | Wire plugins + routers |

## HTTP API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/tools` | All tools with input/output schemas |
| `GET` | `/api/tools/openai` | OpenAI-style `tools[]` payload |
| `GET` | `/api/tools/{control_code}` | One tool definition |
| `POST` | `/api/tools/{control_code}/invoke` | Run simulation `{ "inputs": { ... } }` |
| `GET` | `/api/tools/meta/plugins` | Registered plugin classes |

## Add a custom plugin (setuptools)

1. Implement simulators and/or schema providers (see `banking_control/tools/simulators/`).
2. Register in a module:

```python
def register(manager):
    manager.register_simulator(MySimulator())
```

3. Declare an entry point in your package `pyproject.toml`:

```toml
[project.entry-points."banking_control.plugins"]
my_bank = "my_bank.plugins:register"
```

4. Install the package in the CAI session (`pip install -e .`).

## Add a plugin in-process (no entry point)

```python
from banking_control.api.factory import create_app

app = create_app(extra_plugins=[MyPlugin()])
```

`MyPlugin` must expose `name` and `register(manager)`.

## Custom simulator sketch

```python
class MySimulator:
    priority = 40  # higher than built-in generic (0) and similarity (30)

    def matches(self, tool) -> bool:
        return tool.control_code == "AML-003"

    def simulate(self, tool, inputs: dict) -> dict:
        return {
            "control_code": tool.control_code,
            "status": "Effective",
            "summary": "Custom logic",
            "findings": [],
            "simulated": True,
        }
```

Higher `priority` wins when multiple simulators `matches()` return true.
