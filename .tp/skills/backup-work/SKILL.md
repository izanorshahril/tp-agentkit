---
name: backup-work
description: Create and verify a recoverable baseline for test-program or framework work. Use before in-place edits, revision copies, replacements, removals, bulk rewrites, or any change whose original state is not already recoverable.
---

# Back up the work

Choose the smallest backup that can restore the exact mutation scope. Prefer an existing version-control checkpoint when it is present and usable; otherwise create an explicit copy or archive outside the target being changed.

## Baseline

1. Resolve the source and backup destinations to absolute paths.
2. Prove both remain inside the authorized workspace and that the backup is outside the mutation target.
3. Refuse accidental overwrite of an existing backup unless the user explicitly chooses replacement.
4. Create the snapshot, then independently inspect its size and expected entries.
5. Record the restore operation in the task checkpoint before mutation.

Adapt this PowerShell shape rather than saving a permanent helper:

```powershell
$sourcePath = (Resolve-Path -LiteralPath '<source>').Path
$backupPath = [System.IO.Path]::GetFullPath('<backup.zip>')
if (Test-Path -LiteralPath $backupPath) { throw 'Backup already exists.' }
Compress-Archive -LiteralPath $sourcePath -DestinationPath $backupPath
$zip = [System.IO.Compression.ZipFile]::OpenRead($backupPath)
try { $zip.Entries | Select-Object -First 20 FullName, Length } finally { $zip.Dispose() }
```

Load `System.IO.Compression.FileSystem` first only on PowerShell versions that require it. For very large or tool-sensitive programs, a verified sibling copy can be cheaper and easier to compare than a ZIP.

## Boundaries

- A backup beside an in-place-edited file is acceptable only when the mutation cannot sweep it up.
- Generated summaries and task notes are not a source backup.
- Preserve timestamps, permissions, or links when the target platform depends on them; test the chosen copy method on a small slice when unsure.
- Redact identifiers in the checkpoint, not inside the source snapshot required for restoration.

## Complete when

The baseline exists, contains the expected source, is outside the mutation target, and a concrete restore path is known. Creation success without content inspection is incomplete.
