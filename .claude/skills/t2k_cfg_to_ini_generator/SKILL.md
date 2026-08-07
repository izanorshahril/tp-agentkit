---
name: t2k_cfg_to_ini_generator
description: Generate T2K .ini launch files from existing .cfg files with auto RDK or OTPL detection.
metadata:
  status: beta
  language: batch
  source: tester-toolkit-t2k/ini-generator
---

# T2K Cfg-To-Ini Generator

Use `t2k_cfg_to_ini_generator.bat` to generate T2K `.ini` launch files from existing `.cfg` files, with automatic RDK or OTPL detection based on `stplFile`.

## Purpose

- Generate one or more `.ini` files from existing T2K `.cfg` files.
- Support silent, non-interactive invocation for agent workflows.
- Auto-detect OTPL when the cfg contains `stplFile`; otherwise default to RDK.
- Parse the real launcher keys used in this repo: `tplFile`, `envFile`, `socFile`, and optional `stplFile`.

## Tool Entry Point

- Script: `.claude/skills/t2k_cfg_to_ini_generator/t2k_cfg_to_ini_generator.bat`
- Platform: Windows batch
- Preferred working directory: target TP root or workspace root

## When To Use

Use this skill when:
- a T2K TP already has a valid `.cfg` file and needs the matching `.ini`
- the user wants to regenerate launch `.ini` files after TP copy, rename, or packaging work
- automation should avoid menu-driving and use a direct command

Do not use this skill when:
- the task is generic text-template rendering from arbitrary parameters
- there is no existing `.cfg` file to parse
- the task is outside Windows batch execution

## Modes Of Operation

### Silent mode for automation

Preferred invocation:

```bat
.claude\skills\t2k_cfg_to_ini_generator\t2k_cfg_to_ini_generator.bat "path\to\tplConfigFile.cfg" [RDK|OTPL]
```

Behavior:
- if mode is omitted, the script auto-detects mode from cfg content
- if `stplFile` exists, mode becomes `OTPL`
- if `stplFile` is absent, mode becomes `RDK`
- if `RDK` or `OTPL` is passed explicitly, that overrides auto-detection
- silent mode writes the generated `.ini` next to the selected cfg
- exits non-zero on missing cfg or missing required keys

### Interactive mode for humans

Run with no arguments to scan for `.cfg` files, preview output, and confirm file generation.

## Inputs

- cfg file path
- optional explicit mode override: `RDK` or `OTPL`

## Outputs

- generated `.ini` file next to the target cfg
- console summary
- non-zero exit code on failure

Generated INI schema:
- `[TESTPROGRAMDEFINITION]`
- `TestProgramFile=<tplFile>`
- `SubTestPlanList=<stplFile>` for OTPL only
- `SocketFile=<socFile>`
- `EnvFile=<envFile>`
- `KeepPattern=false`

## Standard Commands

### Auto-detect mode from cfg

```powershell
.claude/skills/t2k_cfg_to_ini_generator/t2k_cfg_to_ini_generator.bat "testprogram/UR7S_0021/tplConfigFile.cfg"
```

### Force OTPL

```powershell
.claude/skills/t2k_cfg_to_ini_generator/t2k_cfg_to_ini_generator.bat "testprogram/UR7S_0021/tplConfigFile.cfg" OTPL
```

### Force RDK

```powershell
.claude/skills/t2k_cfg_to_ini_generator/t2k_cfg_to_ini_generator.bat "testprogram/UR7T_0016/tplConfigFile.cfg" RDK
```

## Agent Guidance

- Prefer silent mode for automation and agent work.
- Pass an explicit cfg path rather than relying on menu selection.
- Use explicit mode only when the TP is unusual or auto-detection is known to be unreliable.
- Treat this skill as launch-file generation, not as a substitute for TP content edits.
- Expect parse failure when `tplFile`, `envFile`, or `socFile` are missing, or when `OTPL` is forced without `stplFile`.

## Notes

- Harvested from the sibling toolkit repo `tester-toolkit-t2k/ini-generator`, then adapted to keep tp-agentkit's next-to-cfg output behavior.
