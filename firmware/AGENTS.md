# firmware (mari — TSCH-over-BLE link layer)

Firmware half of the unified `mari` repo. See `../AGENTS.md` for
the cross-cutting view and `../marilib/AGENTS.md` for the Python
half.

## Purpose

TSCH-over-BLE link-layer firmware for dense low-power IoT/robot
networks. Driving use case: the 1,000-DotBot OpenSwarm testbed.
Single gateway supports up to 102 nodes with ~270 ms RTT and >97%
PDR; horizontal scalability via multiple uncoordinated gateways
with node-driven handovers (<50 ms single-node, ~0.34 s avg for
100 moving nodes). No link-layer ACKs (latency tradeoff — apps
must retry). No security yet (planned EDHOC/ELA/PSK integration).

## Tech stack

- **Language**: C
- **Targets**: nRF52833, nRF52840, nRF5340 (dual-core; gateway runs
  on net core)
- **Build**: SEGGER Embedded Studio (`.emProject`) via `emBuild`
  from `Makefile`; Docker image `aabadie/dotbot:latest` wraps SES
  for CI
- **Style**: `clang-format` v15, `pre-commit` (root config covers
  both halves)
- **No package manager**

## Entry points

- `mari/mari.h` — public API surface (`mari_init`, node/gateway
  functions)
- `mari/mac.c` — TSCH MAC state machine, slot timing
- `app/03app_node/main.c` — minimal node example showing intended
  integration

## Build / run / test

```bash
# from firmware/
make node                                    # nrf52840dk node
make gateway                                 # nRF5340 net-core gateway
make all                                     # default
make docker                                  # CI path

SEGGER_DIR=/opt/segger ./flash.sh node|gateway --all|<snr...>
```

**No automated test setup.** `app/01mari_*` directories are
on-target experimental apps, not a unit-test suite. CI only
verifies it compiles.

## Cross-half / cross-repo coupling

- **`marilib`** (now in this repo at `../marilib/`): wire-level
  protocol agreement via HDLC and `MetricsProbePayload`. Field
  `marilib_timestamp` in `app/03app_node/main.c` is a legacy
  shared-struct artifact slated for removal.
- **`swarmit`** (layering inversion):
  - `drv/mr_rng/mr_rng_nrf5340_app.c` — `extern swarmit_init_rng` /
    `swarmit_read_rng`
  - `drv/mr_timer_hf/mr_timer_hf.c` — skips TIMER4 handler under
    swarmit's `USE_BULK_UART`
- No git submodules.

## Hot spots and known gaps

- **No link-layer ACKs and no security/encryption**. Cleanest
  greenfield work item; bolting on either touches `mac.c`,
  `packet.c`/`packet.h`, `models.h`.
- **No automated tests**: no unit tests, no host-side simulation,
  no hardware-in-loop.
- **Code-smell debt visible on the integration branch**: multiple
  "FIXME: remove before merge" and "only for debugging" comments
  shipped (`association.c`, `scheduler.c`); two `// TODO: use PPI
  instead` in the hot timing path (`mac.c`) — real perf/jitter
  wins available.
- **Strong SES lock-in**: vendored Nordic startup/linker assets
  under `nRF/`, seven `.emProject` files at this dir.

## Don't

- **Don't change slot timing constants** (`TsTxOffset`,
  `GuardTime`, slot duration 1.7 ms) without re-running the
  join-storm and handover experiments documented in the Mari paper.
- **Don't add link-layer ACKs casually** — the current latency
  profile depends on their absence. Any reliability addition should
  be optional and per-frame.
- **Don't refactor the Bloom filter** membership encoding without
  verifying the false-positive rate stays under 5% at 100 nodes per
  gateway.
