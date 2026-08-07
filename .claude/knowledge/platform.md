# Platform Reference

This workspace supports multiple ATE program families. Use this file as a quick structural reference, not as a per-task source of truth.

## Host Execution Environment

Check the host environment before using terminal commands or assuming tool availability.

### Required First Check

Confirm:

- operating system
- active shell
- available search tools
- whether the task is better served by workspace tools than raw terminal commands

### Windows PowerShell Guidance

On Windows with PowerShell:

- do not assume `rg` is installed
- do not assume Unix tools such as `grep`, `sed`, `awk`, `cat`, or shell chaining with `&&`
- prefer PowerShell-native commands when terminal use is necessary

### Practical Fallbacks

| Need | Preferred | Windows PowerShell fallback |
|------|-----------|-----------------------------|
| File search | workspace file-search tool | `Get-ChildItem -Recurse -File` |
| Text search | workspace grep/search tool | `Select-String` |
| Directory listing | workspace list tool | `Get-ChildItem` |
| File read preview | workspace read tool | `Get-Content` |

### Rule

Use dedicated workspace tools first when they exist.

Only fall back to terminal commands when:

- a dedicated tool does not fit the task, or
- you need shell-specific verification

If a command fails because it is unavailable in the current shell, switch to a shell-native fallback instead of retrying the same command pattern.

## ATE Platform
<!-- Replace with your ATE platform -->
ATE: [Advantest T2000 | Advantest V93000 | Teradyne Flex | Teradyne ETS800]
Framework: [OTPL | RDK | SmarTest | IG-XL]
Version: [TOS/Software version if known]

For task-specific execution order, discovery, and validation rules, follow `../rules/workflows.md`.

## Supported Platform Families

| Platform | Common Frameworks | Typical Key Files |
|----------|-------------------|-------------------|
| Advantest T2000 | OTPL, RDK | `.tpl`, `.stpl`, `.ls`, `.bdefs`, `.cfg`, `.cpp` |
| Advantest V93000 | SmarTest | `.tf`, `.cpp`, setup `.txt` |
| Teradyne Flex | IG-XL | `.igxl`, `.vb`, limits `.txt` |
| Teradyne ETS800 | varies by TP | tester-specific config and source files |

## Common T2000 Reference

### Flow Files

| Extension | Purpose | Typical Location |
|-----------|---------|------------------|
| `.tpl` | Main or sub test plan | `MainTestPlan/`, `SubTestPlans/` |
| `.stpl` | Sub test plan include/registration | `MainTestPlan/`, `SubTestPlans/` |

### Limit And Bin Files

| Extension | Purpose | Typical Location |
|-----------|---------|------------------|
| `.ls` | Limit sheet | `MainTestPlan/` |
| `.bdefs` | Softbin-to-hardbin mappings | `MainTestPlan/` |

### Code Files

| Extension | Purpose | Typical Location |
|-----------|---------|------------------|
| `.cpp` | Test logic or helper implementation | `TestClasses/`, `TestFunctions/` |
| `.h` | Headers and declarations | `TestClasses/`, `TestFunctions/` |

## Read-Only And High-Risk Areas

- `CommonLib/` is shared and should not be modified.
- Generated build artifacts and simulator residue should not be treated as authoritative source changes.

## Usage Notes

- Use folder-name environment tokens and the environment rules in `../rules/workflows.md` when deciding which limit groups apply.
- For OTPL flow-level work such as relative tests, inspect `MainTestPlan/*.stpl` and linked `SubTestPlans/` before searching only in source code.

## IPS Versus IPSE Identification Heuristic

When a TP family does not explicitly state whether it is IPS or IPSE, resource naming can provide a practical first-pass signal.

- `IPS` commonly uses `MMXH` instrument/resource naming.
- `IPSE` commonly uses `MMXHE` instrument/resource naming, where the trailing `E` indicates enhanced resources.

Use this as a heuristic, not as the sole proof source.

Preferred confirmation order:

1. check resource or instrument names in TP source and comments
2. check `.soc` headers for generator template or config names such as `config_IPSE`
3. check simulator or startup files such as `OASISSim_IPSE.def`
4. if those disagree, treat the TP as ambiguous and verify with the user or the original program package
