# Local Artifact Compress

Closed-environment markdown and text compactor for TP-AgentKit artifacts.

## Why It Exists

An external model-based compressor may rewrite prose using networked or opaque behavior. That is not suitable for confidential or sealed environments. This local replacement keeps the workflow inside the machine and uses deterministic text shortening only.

## Safety Model

- no network calls
- stdlib only
- preserves code fences, headings, links, URLs, file paths, tables, and blockquotes
- validates preserved structure before writing by default
- creates a sibling backup for in-place mode and refuses to overwrite if the backup already exists
- keeps the original content unchanged when the conservative rewrite does not reduce size

## Typical Use

- compact a large completed task artifact into a lighter version
- keep the original readable backup beside the compressed file
- use the JSON summary when another automation step needs the savings metrics
- prioritize prose-heavy artifacts; diff-heavy compare files may only shrink slightly

## Modes

- `conservative`: default; aims for safe reduction and keeps the original if there is no clear size win
- `aggressive`: stronger shortening for completed low-risk artifacts; may read more terse

## Limitations

- more conservative than an LLM rewrite
- does not try to rewrite table cell text
- does not attempt semantic merging of repeated paragraphs
- should not be used as a substitute for human judgment on safety-critical instructions