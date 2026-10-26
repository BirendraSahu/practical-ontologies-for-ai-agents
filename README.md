# Practical Ontologies for AI Agents — companion

Runnable teaching examples for *Practical Ontologies for AI Agents* by Birendra Kumar Sahu. Python 3.10+ with the standard library is sufficient for the core examples and offline tests. All data is synthetic; no credentials or paid account is required.

From this directory:

```sh
python3 examples/service_context.py
python3 examples/service_context.py --test
python3 examples/capstone.py
python3 examples/capstone.py --test
python3 examples/model_walkthrough.py
python3 examples/binding_walkthrough.py
python3 examples/llm_adapter.py
python3 examples/llm_adapter.py --blocked
python3 -m unittest discover -s examples -p 'test_llm_adapter.py' -v
```

The two core programs have 21 combined unit tests. The model and binding walkthroughs contain nine additional executable assertions. The optional model adapter has eight offline tests. These tests check the supplied fixtures and boundaries, not general agent quality.

`model.json` is the book's small custom format, not JSON-LD. The model walkthrough implements directly declared endpoint checks, not OWL reasoning or SHACL. `service-model.ttl` is a teaching representation not parsed or validated by this package. The support capstone is current-only; its separate policy query demonstrates valid and recorded time. SQLite is in memory and is discarded at process exit.

## Optional local model

The adapter prints the request by default. To call an already installed Ollama model that supports structured output, run:

```sh
python3 examples/llm_adapter.py --run-local --model YOUR_INSTALLED_MODEL
```

It calls only `http://127.0.0.1:11434/api/chat`, installs nothing, and preserves application-owned status fields. Blocked context skips generation. The model selects approved fact identifiers; the application validates and renders them. Live model inference has not been benchmarked in this package.

The examples do not host MCP, enforce production authorization, execute warehouse SQL or perform operational actions. Do not add production data, documents or secrets to these fixtures.

## License

The companion code and synthetic fixtures are MIT licensed; see LICENSE. This license does not cover the book manuscript, cover, diagrams or publishing files, which are not included here.
