# Limit Sheet Environment Mapping (T2K)

## Purpose
When updating limits for a **specific temperature or environment**, change only the corresponding LL/UL pairs. Do not update all environments unless the task explicitly says so.

## T2K LimitDef Argument Order

```
LimitDef(TestNo, Desc, PrecScale, Unit, Bin,
  FTC_LL, FTC_UL,   FTR_LL, FTR_UL,   FTH_LL, FTH_UL,
  EWC_LL, EWC_UL,   EWR_LL, EWR_UL,   EWH_LL, EWH_UL)
```

## Environment Groups

| Group | Environments | Use when task says |
|-------|--------------|--------------------|
| **COLD** | FTC, EWC | "COLD only", "at COLD", "FPY at COLD" |
| **ROOM / AMB** | FTR, EWR | "ROOM only", "AMB", "at room temp" |
| **HOT** | FTH, EWH | "HOT only", "at hot" |
| **ALL** | FTC, FTR, FTH, EWC, EWR, EWH | "all temps", "all environments", or no env specified |

## Direct Edit Example

Task: "Tighten T6027 USL at COLD from -200 mV to -700 mV"

- **Before**: `-2V, -0.2V, -2V, -0.2V, -2V, -0.2V, -2V, -0.2V, -2V, -0.2V, -2V, -0.2V`
- **After**:  `-2V, -0.7V, -2V, -0.2V, -2V, -0.2V, -2V, -0.7V, -2V, -0.2V, -2V, -0.2V`
  - FTC_UL and EWC_UL changed to -0.7V; FTR, FTH, EWR, EWH remain -0.2V

## ls-updater Usage

When using the ls-updater skill with `--env`:
- `--env FTC` updates only FTC
- `--env EWC` updates only EWC
- `--env ALL` (or omit) updates all environments

For COLD-only: run twice with `--env FTC` and `--env EWC`, or use a skill that supports multiple envs if available.
