---
type: toolkit_harvest
status: verified
verifier: sibling toolkit doc cross-read against current tp-agentkit skill surfaces
date: 2026-04-27
source: "sibling tester-toolkit-t2k module docs plus local .claude skill registry and skill docs"
---

# Harvested Toolkit Modules

Summary of reusable content harvested from the sibling toolkit and how it should be carried forward inside TP-AgentKit.

## Cross-Device Harvest Rule

Promote a sibling module into a callable TP-AgentKit skill only when all of these are true:

- the module takes stable on-disk artifacts as input and emits deterministic outputs
- the operating boundary is schema-based rather than device-name-based
- the agent-facing value is the parser or transformer, not the browser UI or menu flow
- the local skill surface can document real limits and failure modes without relying on human-only interaction

Keep a sibling module as knowledge or reference only when the main value is presentation, dashboard UX, or ad-hoc manual review.

## Current Inventory And Local Coverage

| Sibling module | Local TP-AgentKit state | Future applicability rule | Keep as |
|----------------|-------------------------|---------------------------|---------|
| `ls-updater` | already maintained locally as `.claude/skills/ls-updater/` | applicable across T2K devices whose target `.ls` family is supported by the local parser; extend parser support per LS family instead of cloning by device name | callable skill |
| `ini-generator` | already harvested as `.claude/skills/t2k_cfg_to_ini_generator/` | applicable across devices that use the same cfg-driven launcher contract; scope is the cfg schema, not the product family | callable skill |
| `under-dev/error-log-analyzer` | already harvested as `.claude/skills/system_controller_log_analyzer/` | applicable across devices that emit SystemController-style logs; scope is the log family, not the device family | callable skill |
| `error-log-dashboard` | intentionally not harvested as a skill | useful across devices for human visual review, but browser or Chrome assumptions make it a poor maintained agent boundary | knowledge or reference only |

## Practical Guidance

- Treat the local TP-AgentKit skill docs as the operational source of truth once a module has been harvested.
- Revisit the sibling toolkit only when checking for new capabilities, clearer examples, or low-risk sync candidates.
- Keep skill names behavior-first and schema-first. Avoid new device-specific skill folders when the real boundary is `.ls`, `.cfg`, or log format support.

## Reusable Lessons

- Harvest parser and transformer cores, not interactive menus.
- Preserve compact machine-readable outputs when a module is meant to feed later automation or artifact generation.
- Prefer narrow names such as `system_controller_log_analyzer` over generic names that over-promise unsupported formats.
- When a sibling module is visualization-first, capture the interpretation rule in knowledge and keep the dashboard itself as optional human-facing support material.

## Non-Goals

- Do not assume every `.ls` family is automatically covered just because `ls-updater` is cross-device in intent.
- Do not treat the SystemController parser as proof of generic ATE log coverage.
- Do not promote browser dashboards into maintained callable skills unless the browser runtime becomes a deliberate supported boundary.