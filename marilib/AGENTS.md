# marilib (Python half of mari)

Python half of the unified `mari` repo. Self-contained: package
source, tests, examples, and `pyproject.toml` all live under this
directory. See `../AGENTS.md` for the cross-cutting view and
`../firmware/AGENTS.md` for the firmware half.

## Purpose

Python library and CLI agents (`mari-edge`, `mari-cloud`) that talk
to a Mari low-power wireless network. `MarilibEdge` connects to a
UART-attached Mari gateway (typical use: Raspberry Pi between an
nRF5340 gateway and a network); `MarilibCloud` connects via MQTT,
bridging the local gateway to the cloud. Ships a Rich-based
real-time TUI for network state and stats.

## Tech stack

- **Language**: Python >= 3.8
- **Runtime deps**: `click`, `pyserial`, `rich`, `structlog`,
  `tqdm`, `paho-mqtt`
- **Build**: `hatchling` (`pyproject.toml` in this directory)
- **Package**: PyPI as `marilib-pkg`; pip / hatch
- **Dev/test**: `pytest` + `pytest-cov` via hatch envs; `ruff`,
  `black`, `isort`, `pre-commit` (root config)
- **Targets**: Mari gateway over UART/HDLC; deployed on Raspberry
  Pi (systemd service + bind-interface scripts under
  `examples/raspberry-pi/`); MQTT broker (e.g. mosquitto)

## Layout

```
marilib/
├── pyproject.toml            ← hatchling build config (PyPI: marilib-pkg)
├── README.md                 ← PyPI-facing description
├── AGENTS.md                 ← this file
├── AUTHORS
├── install_marilib.sh        ← Raspberry Pi installer
├── tests_requirements.txt
├── marilib/                  ← package source (the importable `marilib`)
│   ├── __init__.py
│   ├── marilib_edge.py
│   ├── marilib_cloud.py
│   ├── cli/{edge,cloud}.py
│   └── …
├── tests/
└── examples/
```

## Entry points

- `marilib/marilib_edge.py` — UART-side library class (the core)
- `marilib/marilib_cloud.py` — MQTT-side cloud client
- `marilib/cli/edge.py`, `marilib/cli/cloud.py` — CLI wiring for
  the two console scripts
- `examples/mari_edge_minimal.py` — smallest usable example

## Build / run / test

```bash
# from marilib/
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Pi install helper
./install_marilib.sh

# Run
mari-edge -m mqtts://...
mari-cloud -n 0x0100 -m mqtts://...

# Tests / format / build
hatch test                                   # pytest --doctest-modules --cov=marilib
hatch fmt --check
hatch build
```

CI matrix: ubuntu / macOS / Windows × py3.12 / 3.13. Workflow is
path-filtered to `marilib/**`.

## Cross-half / cross-repo coupling

- **`firmware/`** (now in this repo at `../firmware/`): HDLC wire
  contract and `MetricsProbePayload` layout in
  `marilib/mari_protocol.py` ↔ `../firmware/mari/models.h`. Field
  `marilib_timestamp` in `../firmware/app/03app_node/main.c` is a
  legacy shared-struct artifact slated for removal.
- **`PyDotBot`** and **`swarmit`** consume marilib as a PyPI dep
  (`marilib-pkg`).
- **TODO marker** in `marilib/protocol.py:1` — `# TODO: import this
  from like PyDotBot or similar` (consolidation intent, not done).

## Hot spots and known gaps

- **`marilib/protocol.py` and `marilib/mari_protocol.py` duplicate**
  packet/dataclass scaffolding — the explicit TODO suggests
  unification with `PyDotBot` was the original intent. Prime
  consolidation target.
- **Test suite is thin**: only `tests/test_hdlc.py` and
  `tests/test_protocol.py`. No tests for `marilib_edge`,
  `marilib_cloud`, `metrics`, `model`. Doctest-modules is on, so
  coverage may rely on inline doctests, but the hot paths (MQTT
  bridge, gateway state machine) are untested.
- **`install_marilib.sh` runs `sudo venv/bin/pip install`** —
  unusual (sudo into a user venv); minor but worth fixing.

## Don't

- **Don't change the HDLC framing** without verifying compatibility
  with the firmware UART output
  (`../firmware/app/03app_gateway_app/`).
- **Don't break MQTT topic structure** (`/mari/<network-id>/to_edge`,
  `/mari/<network-id>/to_cloud`) — `swarmit` and `PyDotBot` rely on
  it.
- **Don't add a hard dep on `PyDotBot`**; if shared protocol code
  needs a home, put it in `PyDotBot-utils` or a new shared package,
  not in either consumer.
