---
status: researched
scope: local semantic embeddings for Graphify node clustering and visualization
updated: 2026-09-22
---

# Embedding Model Research

## Decision

For this predominantly English corpus, use `ibm-granite/granite-embedding-small-english-r2` as the primary corporate evaluation candidate.
It is Apache 2.0 licensed, 47M parameters, 384-dimensional, English-focused, and has an 8,192-token context limit.
IBM's reported English evaluation table places it above the older E5-small-v2 and BGE-small-en-v1.5 baselines on the listed benchmark columns.

Use `ibm-granite/granite-embedding-97m-multilingual-r2` as the recent six-month SOTA comparator.
Its extra multilingual capacity is unnecessary for this corpus, but it has explicit code-language retrieval coverage and is also Apache 2.0 licensed.

Retain `intfloat/e5-small-v2` and `BAAI/bge-small-en-v1.5` as older reproducible baselines, not as current SOTA.

Use `jinaai/jina-embeddings-v5-text-nano` as a frontier comparison only when its CC BY-NC 4.0 license is acceptable.
It was released on 2026-02-18 and is outside the requested 2026-03-17 through 2026-09-17 window.

Use the existing `llama.cpp` Windows runtime first, with a reviewed local GGUF model file and CPU execution.
Use BGE-small-en-v1.5 Q8_0 GGUF for the zero-install smoke test because `ggml-org` publishes a direct conversion and the model is widely used.
Keep Granite Small English R2 as the preferred English quality candidate, but require an approved GGUF conversion or an internally produced artifact before using it in the same path.
Use Granite 97M Multilingual R2 as the recent-model comparison when its IBM-documented conversion or an approved GGUF artifact is available.

Model and dependency licensing still requires corporate legal review before redistribution or production deployment.
Apache 2.0 or MIT model weights do not automatically clear every dependency, tokenizer, training-data, or hosting obligation.

These models should produce a derived semantic visualization layer only.
Preserve Graphify nodes, edges, relations, provenance, and structural communities unchanged.
Semantic labels and colors must never override graph structure.

## QMD fit for future Graphify integration

### Decision

Use QMD as the document retrieval module and keep Graphify as the structural source-code and test-flow module.
Do not replace the Graphify node-embedding path above with QMD's document vectors.
The two systems have different embedding models, prompt formats, chunking rules, identifiers, and retrieval contracts.
Their vectors must not be compared directly or placed in one clustering space without a controlled parity study.

The useful seam is a small join adapter between the two indexes:

```text
QMD documents --lex/vector/hybrid--> document passages and qmd:// references
                                            \
                                             join adapter --> RAG evidence and visual links
                                            /
Graphify source graph -------------> nodes, edges, flow, and source locations
```

The adapter should produce a derived artifact, not rewrite either source of truth.
For each proposed document-to-code link, retain the document path and docid, line range, source node id, source location, Graphify commit, retrieval method, score, and a short evidence reason.
Treat QMD relevance scores as retrieval signals, not as proof that a specification governs a node or flow.

### What QMD contributes

The current project setup provides:

- BM25 keyword search for exact identifiers, limits, register names, and document terminology.
- Vector search for conceptual retrieval, plus hybrid RRF and local LLM reranking through `qmd query`.
- `qmd get` and JSON output for reproducible passage retrieval and agent/RAG handoff.
- Collection context that can identify document families by path when those sources are included in a collection.
- A local MCP interface for a later agent integration, with stdio as the default and loopback HTTP available for a shared process.

The local `.qmd/index.yml` uses `**/*.md`.
The current collection includes Markdown under the main documentation tree and the Graphify report; it does not currently include this hidden `.tp/knowledge` note, plain-text mail, CSV files, C++ files, or tester-program files.
Selected Markdown roots such as controlled specifications, mail converted to Markdown, and approved knowledge notes can be added later without duplicating Graphify's source graph.
The current QMD embedding model is EmbeddingGemma, not the BGE, E5, or Granite candidates evaluated for Graphify node clustering.
Changing QMD's embedding model requires re-embedding its collections and does not make its vectors compatible with the Graphify sidecar.

### Recommended larger-scope uses

#### Retrieval-augmented analysis

Use QMD first to retrieve governing passages for a question such as a limit, test intent, operating condition, or feature definition.
Then use the retrieved identifiers, file names, and terminology to query Graphify for callers, active-flow reachability, and implementation locations.
Return both evidence types:

1. QMD document references with line ranges and docids.
2. Graphify source nodes and edges with source locations and graph revision.

This supports answers such as "which active test implements this datasheet requirement?" without asking either tool to prove what it does not model.
QMD supplies document evidence; Graphify supplies structural navigation; source inspection and runtime evidence remain the authority for final conclusions.

#### Document-to-code links

Start with exact identifier and path matches because they are auditable.
Use QMD semantic retrieval only to propose additional links, then verify them through Graphify reachability and source inspection.
Store links in a derived sidecar keyed by `qmd://collection/path` plus docid on one side and Graphify's stable node id on the other.
Use explicit methods such as `exact-identifier`, `source-path`, `semantic-retrieval`, and `manual-review` so later visualizations can separate verified links from candidates.

Do not create Graphify structural edges from an unreviewed semantic match.
At most, expose candidate document references or dotted visualization overlays with their method and score.

#### Visualizations

Keep Graphify's existing nodes, edges, structural communities, relation types, provenance, and reachability unchanged.
Add QMD-derived views as separate layers:

- document evidence available from a selected source node;
- specifications or datasheets retrieved for a selected Graphify node;
- candidate document-to-code links, visually distinct from structural edges;
- document and source facets for filtering a graph view.

The existing Graphify semantic-clustering research remains the correct place to evaluate colors or clusters for code nodes.
QMD's document vectors can support document-side clustering or retrieval, but should not silently determine code-node colors.

### Tool choice

| Question | Preferred tool | Reason |
| --- | --- | --- |
| Where is a term, limit, or requirement described? | QMD | Exact and conceptual document retrieval |
| Which function calls this helper, or which test is reachable in a flow? | Graphify | Structural relationships and active-code navigation |
| Does a documented requirement map to an implemented test? | Both | QMD locates the authority; Graphify traces the implementation |
| Which code nodes should share a visualization color? | Graphify plus a dedicated evaluated node model | QMD's document vectors are a different space and purpose |
| What evidence should an agent cite in a RAG answer? | Both | QMD passage plus Graphify source location and revision |

### Evaluation plan

Before building a persistent join adapter, create a small reviewed fixture containing:

- document questions and expected QMD passages;
- expected source files, symbols, and active-flow paths;
- positive and negative document-to-code pairs;
- a requirement-to-test matrix drawn from the existing CPQ and controlled documents.

Measure document recall at `k`, exact-identifier precision, semantic-link precision after Graphify verification, citation line accuracy, and stability across document or source revisions.
Keep separate baselines for QMD BM25, QMD vector/hybrid retrieval, exact matching, and Graphify-only structural lookup.
Do not treat a generic embedding benchmark or a visually plausible cluster as proof of domain correctness.

### Implementation order

1. Keep the current Markdown-only QMD collection and add path context for the major document families.
2. Use QMD JSON output or its local MCP interface as the narrow document-retrieval interface.
3. Generate or refresh Graphify from the same source revision used by the evaluation fixture.
4. Build a disposable join report for a small set of requirements and tests before choosing a permanent sidecar schema.
5. Add a visualization overlay only after candidate links have a reviewed precision baseline.
6. Consider indexing source files in QMD only as a separate experiment; its documented AST-aware chunkers target TypeScript, JavaScript, Python, Go, and Rust, so C++ and tester-program text would fall back to generic chunking while Graphify already understands the structural relationships.

### QMD sources and local evidence

QMD's official documentation describes its BM25, vector, hybrid, reranking, collection, context, JSON, MCP, model, and chunking interfaces:

- https://github.com/tobi/qmd
- [Project QMD configuration](../../.qmd/index.yml)
- [Workspace routing guidance](../../AGENTS.md)
- [Graphify report](../../graphify-out/GRAPH_REPORT.md)

## GGUF and llama.cpp deployment decision

### Recommendation

Use `llama.cpp` as the first local inference runtime.
The machine already has `llama-server.exe` and `llama-cli.exe` from WinGet, build `9837 (b3fed31b9)`, compiled for Windows x86_64.
The dedicated `llama-embedding.exe` executable is not on `PATH`, but the installed server supports `--embedding`, mean or CLS pooling, L2 normalization, offline mode, and the OpenAI-compatible `/v1/embeddings` endpoint.
This avoids installing Python, PyTorch, Sentence Transformers, ONNX Runtime, or OpenVINO for the initial experiment.

Use the `ggml-org/bge-small-en-v1.5-Q8_0-GGUF` artifact for the first smoke test.
It is a `bert` architecture GGUF, carries the MIT model license, has a documented `llama.cpp` command, and is published by the `ggml-org` organization.
Use CLS pooling for BGE and compare Q8_0 against an F16 or upstream reference before accepting any semantic grouping change.

Do not silently replace Granite Small English R2 with BGE as the final quality decision.
Granite Small English R2 remains the English-first quality candidate, but no IBM-published GGUF artifact was found in the sources reviewed.
Its available community conversion must be checked for revision, conversion command, file hash, model license, and output equivalence.
IBM explicitly documents conversion of Granite 97M Multilingual R2 with `convert_hf_to_gguf.py`, and `llama.cpp` has native ModernBERT support for the Granite 97M R2 architecture, but that route still needs a one-time conversion toolchain or an approved converted artifact.

### Unsloth embedding GGUF check

Unsloth publishes a genuine embedding GGUF at `unsloth/embeddinggemma-300m-GGUF`.
The Hub metadata tags it for sentence similarity, feature extraction, text-embeddings-inference, and GGUF, and identifies its GGUF architecture as `gemma-embedding`.
The repository contains BF16, F32, Q8_0, and Q4_0 files.
The model card identifies `google/embeddinggemma-300m` as the base model and reports 768-dimensional output with truncation options at 512, 256, and 128 dimensions, a 2,048-token context, and prompts that differ for queries and documents.

This confirms an Unsloth-published quantized embedding artifact, but the reviewed card does not expose the exact conversion command or checksum lineage.
Review the fixed revision, file hash, Gemma terms, tokenizer, prompt format, and runtime compatibility before using it in the controlled Graphify path.
It does not replace BGE as the first corporate smoke test because the Gemma license requires a separate review and the model produces a different vector space and dimension from the current 384D shortlist.

The reviewed Unsloth embedding collection also contains safetensors embedding uploads for BGE, GTE-ModernBERT, Qwen3 Embedding, MiniLM, and others, but no additional Unsloth-published embedding GGUF was verified in this check.

Sources:

- https://huggingface.co/unsloth/embeddinggemma-300m-GGUF
- https://huggingface.co/api/models/unsloth/embeddinggemma-300m-GGUF
- https://huggingface.co/collections/unsloth/embedding-models
- https://huggingface.co/google/embeddinggemma-300m
- https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-gguf

### Popularity signals observed 2026-09-17

Popularity is an adoption signal, not an embedding-quality measurement.
Hugging Face download counters are not unique-user counts and can include automated downloads.

| Item | HF downloads last month | Likes/stars | GGUF or runtime signal | Interpretation |
| --- | ---: | ---: | --- | --- |
| `llama.cpp` | N/A | 128,477 GitHub stars; 23,286 forks | MIT; latest release `v0.4.1` on 2026-09-14 | Very popular and operationally mature runtime |
| `BAAI/bge-small-en-v1.5` | 64,638,739 | 583 HF likes | `ggml-org` Q8_0: 2,414 downloads and 6 likes; CompendiumLabs GGUF: 8,476 downloads and 8 likes | Strongest practical GGUF adoption signal in this shortlist |
| `ibm-granite/granite-embedding-small-english-r2` | 6,398,398 | 82 HF likes | Community GGUF: 688 downloads and 2 likes; no IBM-published GGUF found | Strong original-model adoption, weaker GGUF provenance/adoption |
| `intfloat/e5-small-v2` | 533,400 | 125 HF likes | `ggml-org` Q8_0: 164 downloads | Mature baseline, but weaker current GGUF signal |
| `ibm-granite/granite-embedding-97m-multilingual-r2` | 76,618 | 139 HF likes | Community GGUFs observed at 82 and 162 downloads; IBM documents conversion | Recent model with official conversion guidance, not a ready-made official GGUF |

Sources:

- https://github.com/ggml-org/llama.cpp
- https://github.com/ggml-org/llama.cpp/releases/tag/v0.4.1
- https://huggingface.co/BAAI/bge-small-en-v1.5
- https://huggingface.co/ggml-org/bge-small-en-v1.5-Q8_0-GGUF
- https://huggingface.co/CompendiumLabs/bge-small-en-v1.5-gguf
- https://huggingface.co/intfloat/e5-small-v2
- https://huggingface.co/ggml-org/e5-small-v2-Q8_0-GGUF
- https://huggingface.co/ibm-granite/granite-embedding-small-english-r2
- https://huggingface.co/mradermacher/granite-embedding-small-english-r2-GGUF
- https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2
- https://huggingface.co/cstr/granite-embedding-97m-multilingual-r2-GGUF
- https://huggingface.co/Lorelum/granite-embedding-97m-multilingual-r2-GGUF

### Minimal Windows workflow

Stage the reviewed GGUF and its checksum in a local model directory.
For the BGE smoke test, the installed server can run without a Python environment:

```powershell
llama-server.exe `
  --model .\models\bge-small-en-v1.5-q8_0.gguf `
  --embedding `
  --pooling cls `
  --embd-normalize 2 `
  --offline `
  --host 127.0.0.1 `
  --port 8080
```

Send batches of node text to `POST http://127.0.0.1:8080/v1/embeddings` and write the returned vectors to the existing semantic sidecar.
Keep the input prefix, pooling mode, normalization, GGUF filename, SHA-256, llama.cpp build, and model license in the sidecar metadata.
Do not use `--hf-repo` in the controlled offline run; download and approve artifacts separately.

The server API is simpler for a Graphify integration than spawning one process per node, while the command-line executable remains useful for a small deterministic smoke test.
The runtime is MIT licensed, but the model license and converted-artifact provenance remain separate review items.

Sources:

- https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- https://github.com/ggml-org/llama.cpp/tree/master/examples/embedding
- https://huggingface.co/ggml-org/bge-small-en-v1.5-Q8_0-GGUF
- https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2
- https://github.com/ggml-org/llama.cpp/blob/master/src/models/modern-bert.cpp

## Corporate English scope

The corpus is overwhelmingly English, with only a small trace of French, Italian, and German.
That makes English quality, permissive corporate licensing, CPU cost, and code/technical-text behavior more important than broad multilingual coverage.
The small European-language trace is not a reason by itself to choose a multilingual model.

### Preferred model

Use `ibm-granite/granite-embedding-small-english-r2` first.
IBM's model card identifies it as an English-only, 47M-parameter model with 384-dimensional output and an 8,192-token maximum sequence length.
It is released under Apache 2.0 and is available through Sentence Transformers.
The model card also reports code/text-optimized training and English benchmark results for retrieval, code retrieval, and other embedding tasks.

Sources:

- https://huggingface.co/ibm-granite/granite-embedding-small-english-r2
- https://github.com/ibm-granite/granite-embedding-models
- https://www.apache.org/licenses/LICENSE-2.0

### Corporate license shortlist

| Model | Model-card license | Corporate posture | Decision |
| --- | --- | --- | --- |
| `ibm-granite/granite-embedding-small-english-r2` | Apache 2.0 | Permissive license with attribution, notice, and redistribution conditions | Preferred English candidate |
| `ibm-granite/granite-embedding-english-r2` | Apache 2.0 | Same license; 149M parameters and 768 dimensions | Accuracy/quality reference |
| `ibm-granite/granite-embedding-97m-multilingual-r2` | Apache 2.0 | Permissive license; multilingual and code coverage are broader than needed | Recent SOTA comparator |
| `intfloat/e5-small-v2` | MIT | Permissive license; English-only and 512-token limit | Lowest-cost baseline |
| `BAAI/bge-small-en-v1.5` | MIT | Permissive license; English and 512-token limit | English baseline |
| `jinaai/jina-embeddings-v5-text-nano` | CC BY-NC 4.0 | Non-commercial restriction makes it unsuitable for unrestricted corporate use without separate permission | Exclude |
| `google/embeddinggemma-300m` | Gemma Terms of Use | Not an Apache/MIT choice; gated access and terms require a separate review | Exclude from first corporate path |

Apache 2.0 permits commercial use, reproduction, modification, distribution, and sublicensing subject to its conditions, including preserving notices and providing the license when redistributing.
MIT likewise permits commercial use, modification, distribution, and sale subject to retaining the copyright and permission notice.
These are license-text facts, not a legal opinion about the complete model supply chain.

Sources:

- https://www.apache.org/licenses/LICENSE-2.0
- https://opensource.org/license/mit
- https://huggingface.co/ibm-granite/granite-embedding-small-english-r2
- https://huggingface.co/ibm-granite/granite-embedding-english-r2
- https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2
- https://huggingface.co/intfloat/e5-small-v2
- https://huggingface.co/BAAI/bge-small-en-v1.5
- https://huggingface.co/jinaai/jina-embeddings-v5-text-nano
- https://huggingface.co/google/embeddinggemma-300m

Before production or redistribution, review the exact model revision, bundled files, tokenizer, inference dependencies, notices, and any corporate policy requirements with the responsible legal or open-source review function.

## Six-month SOTA refresh

### Scope and conclusion

Research window: 2026-03-17 through 2026-09-17.

The clearly verified in-window release found in the primary sources reviewed is IBM Granite Embedding Multilingual R2, released on 2026-04-29.
Its 97M model is the practical candidate; its 311M model is the higher-quality reference.

Jina Embeddings v5 Nano and Small are useful 2026 frontier references, but their model cards date the release to 2026-02-18, before this window.
Google EmbeddingGemma, Qwen3 Embedding, and Nomic Embed v2 are also outside this window based on their first-party release or paper dates.

This is a source-bounded refresh, not a claim that no other model was released globally during the window.
It does establish that E5-small-v2 and BGE-small-en-v1.5 should no longer be described as SOTA.

Sources:

- https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2
- https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2
- https://huggingface.co/jinaai/jina-embeddings-v5-text-nano
- https://huggingface.co/jinaai/jina-embeddings-v5-text-small
- https://huggingface.co/google/embeddinggemma-300m
- https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
- https://huggingface.co/nomic-ai/nomic-embed-text-v2-moe

### Candidate comparison

| Model | Release | Parameters | Output | Context | License | Code/language evidence | Local CPU relevance |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `ibm-granite/granite-embedding-97m-multilingual-r2` | 2026-04-29 | 97M | 384D | 32,768 | Apache 2.0 | 200+ language pretraining; enhanced support for 52 languages and Python, Go, Java, JavaScript, PHP, Ruby, SQL, C, and C++ | Recent SOTA comparator; pre-converted ONNX and OpenVINO INT8 paths are documented |
| `ibm-granite/granite-embedding-311m-multilingual-r2` | 2026-04-29 | 311M | 768D, truncatable to 512/384/256/128 | 32,768 | Apache 2.0 | Same code and multilingual coverage as 97M | Accuracy reference; likely slower and heavier on four CPU cores |
| `jinaai/jina-embeddings-v5-text-nano` | 2026-02-18, outside window | 239M | 768D, Matryoshka to 32D-768D | 8,192 on model card | CC BY-NC 4.0 | Multilingual; no equivalent verified code-language list in the card | Strong comparison model, but license and runtime complexity reduce suitability |
| `jinaai/jina-embeddings-v5-text-small` | 2026-02-18, outside window | 677M | 1,024D, Matryoshka to 32D-1,024D | 32,768 | CC BY-NC 4.0 | 119+ languages | Frontier reference, too large for the first local experiment |
| `google/embeddinggemma-300m` | 2025-09-24, outside window | 300M | 768D, truncatable to 512/256/128 | 2,048 | Gemma terms | 100+ languages; code and technical documents included in training | Compact reference, but gated access and terms require review |
| `Qwen/Qwen3-Embedding-0.6B` | 2025-06-05, outside window | 0.6B | Up to 1,024D | 32,768 | Apache 2.0 | 100+ languages including programming languages; code retrieval | Strong reference, but larger and less CPU-focused |
| `nomic-ai/nomic-embed-text-v2-moe` | 2025-02-11, outside window | 475M total / 305M active | 768D, truncatable to 256D | 512 | Apache 2.0 | About 100 languages | Higher runtime burden from custom MoE code and `trust_remote_code` |

The Granite dimensions, context, license, language/code coverage, deployment formats, and release date come from the IBM model cards.
The Jina, Google, Qwen, and Nomic facts come from their linked first-party model cards.

### Benchmark versus practical suitability

Granite 97M R2 reports 60.3 on Multilingual MTEB Retrieval, 60.4 on MTEB Code Retrieval, and 65.5 on LongEmbed.
Granite 311M R2 reports 65.2, 63.8, and 71.7 on those same reported benchmark columns.
The model card reports throughput on an NVIDIA H100, so those numbers are not CPU measurements for this machine.

Jina v5 Nano reports 71.0 on MTEB English v2 and 65.5 on MMTEB.
Those scores are useful frontier references but do not establish superiority for short, identifier-heavy semiconductor test-program nodes.

Qwen3-Embedding-8B reports 70.58 on the Qwen team's June 2025 MTEB Multilingual table.
That is a benchmark reference, not a practical four-core CPU recommendation.

Sources:

- https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2
- https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2
- https://huggingface.co/jinaai/jina-embeddings-v5-text-nano
- https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
- https://github.com/embeddings-benchmark/mteb
- https://huggingface.co/spaces/mteb/leaderboard

### Revised evaluation order

1. BGE-small-en-v1.5 `ggml-org` Q8_0 GGUF as the zero-install runtime smoke test.
2. Granite Small English R2 with an approved GGUF artifact as the preferred English quality candidate.
3. E5-small-v2 GGUF as the stable 384D baseline.
4. Granite 97M Multilingual R2 with an approved GGUF artifact as the recent SOTA comparator.
5. Granite English R2 149M as an accuracy reference if the small English model is weak.

Compare models using identical node text, reviewed related/unrelated node pairs, cluster-size distributions, encoding time, and peak memory.
Do not select a model from generic MTEB scores alone.

### Runtime implications

IBM documents pre-converted ONNX and OpenVINO models for the Granite multilingual R2 sizes.
The multilingual model card describes OpenVINO as optimized for Intel hardware, including CPUs and integrated GPUs, and documents an INT8 quantized file.
The English R2 model cards document Sentence Transformers usage; verify an ONNX or OpenVINO artifact for the selected English revision before depending on that backend.

Use ONNX Runtime CPU if OpenVINO packaging is inconvenient.
Sentence Transformers documents ONNX and OpenVINO backends, while ONNX Runtime documents the Windows x64 CPU package and `CPUExecutionProvider`.

Sources:

- https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2
- https://sbert.net/docs/sentence_transformer/usage/efficiency.html
- https://onnxruntime.ai/docs/get-started/with-python.html

### SOTA boundary

"SOTA" here means a recent, source-documented frontier candidate, not a guarantee of the best result on this repository.
The graph has no labeled semantic ground truth, and no local benchmark has been run.
The winning model for visual grouping must be determined by reviewed node pairs and cluster stability on this graph.

## Verified Local Facts

The current Graphify output contains:

- 1,256 nodes.
- 3,308 edges.
- 90 structural communities.
- 77% extracted edges and 23% inferred edges.
- 752 inferred edges with average confidence 0.85.
- A graph built from commit `a1387f19`.

Source: [graphify-out/GRAPH_REPORT.md](../../graphify-out/GRAPH_REPORT.md).

The graph JSON uses a node-link structure with:

- Top-level graph flags: `directed`, `multigraph`, and `graph`.
- Node records containing `id`, `label`, `norm_label`, `file_type`, `_origin`, `source_file`, `source_location`, and sometimes `metadata`.
- Edge records containing `source`, `target`, `relation`, `_origin`, `confidence`, `confidence_score`, `context`, `source_file`, `source_location`, and `weight`.

Source: [graphify-out/graph.json](../../graphify-out/graph.json).

The checked machine is an 11th Gen Intel Core i5-1145G7 with 4 physical cores and 8 logical processors.
`uv` 0.8.16 is available.
The current `uv` environment does not have `sentence_transformers`, `onnxruntime`, `torch`, `scikit-learn`, or `numpy` installed.
No local embedding benchmark was run.

The repository guidance favors portable, offline-friendly tooling and treats Graphify output as generated analysis rather than a replacement for source or runtime evidence.
Source: [AGENTS.md](../../AGENTS.md).

## Shortlist

| Option | Local CPU/offline feasibility | License | Output | Input limit | Semantic fit | Runtime burden | Clustering implication |
| --- | --- | --- | ---: | ---: | --- | --- | --- |
| `intfloat/e5-small-v2` GGUF | Good after a reviewed GGUF is cached locally | MIT | 384 dimensions | 512 tokens | Strong general semantic similarity; the model card explicitly recommends the `query:` prefix for clustering | Existing `llama-server.exe`; use mean pooling and the required prefix | Normalize vectors and cluster by cosine similarity |
| `BAAI/bge-small-en-v1.5` `ggml-org` Q8_0 GGUF | Best immediate Windows path | MIT | 384 dimensions | 512 tokens | Strong general retrieval/similarity model; suitable for node text treated as passages | Existing `llama-server.exe`; use CLS pooling | Normalize vectors; compare against Granite on a small labeled sample |
| Granite Small English R2 approved GGUF | Good after artifact approval or internal conversion | Apache 2.0 | 384 dimensions | 8,192 tokens | Preferred English quality candidate with code/text training | Existing `llama-server.exe`; conversion/provenance is the extra step | Validate GGUF output against the upstream model before clustering |
| Granite 97M Multilingual R2 approved GGUF | Good after IBM-documented conversion or artifact approval | Apache 2.0 | 384 dimensions | 32,768 tokens | Recent SOTA comparator with broader code and language coverage | Existing `llama-server.exe`; one-time conversion/provenance is the extra step | Validate CLS pooling and normalization before comparison |

E5-small-v2 is an English model with 384-dimensional embeddings, a 512-token limit, and MIT licensing.
Its model card states that clustering inputs should use the `query:` prefix and demonstrates normalized embeddings.
Source: https://huggingface.co/intfloat/e5-small-v2

BGE-small-en-v1.5 is an English model with 384-dimensional embeddings, a 512-token limit, and MIT licensing.
Its model card documents normalized embeddings, sentence similarity usage, and an ONNX representation.
Source: https://huggingface.co/BAAI/bge-small-en-v1.5

The models are compact enough for this graph size, but actual latency and memory use on this machine are not verified here.
The repository provides no CPU model, instruction-set, or benchmark evidence, so those must be measured locally before selecting batch size or quantization.

## Previous baseline recommendation

### Legacy baseline: E5-small-v2

Use one consistent text representation per node, for example:

```text
label: T_0100_PowerOn()
type: callable
file: TestFunctions/T_0100_PowerOn.cpp
location: L1
metadata: ...
```

Encode each node using the same `query:` prefix, because the E5 model card explicitly recommends that prefix for clustering.
Normalize the resulting vectors.

E5 remains a useful reproducible baseline because its model card directly documents clustering usage, normalized embeddings, and the required input convention.
It is not the current SOTA recommendation and has not been benchmarked specifically on semiconductor test-program code here.

### Fallback: BGE-small-en-v1.5

Use BGE when E5 groups identifier-heavy or short node descriptions poorly, or when a passage-oriented representation without E5's query prefix is easier to maintain.

BGE's model card documents direct sentence-transformer usage, normalized embeddings, 384 dimensions, 512-token inputs, and ONNX deployment examples.
Source: https://huggingface.co/BAAI/bge-small-en-v1.5

## Reference backend: Sentence Transformers

Sentence Transformers is an optional reference backend for checking GGUF output, not the primary deployment path.
Load the upstream model from a pinned local directory only when a parity check is needed.
Sentence Transformers supports CPU devices, `local_files_only=True`, normalized embeddings, configurable batch sizes, and cosine similarity.
Source: https://sbert.net/docs/package_reference/sentence_transformer/SentenceTransformer.html

Use the ONNX backend only when an approved GGUF is unavailable or the parity check identifies a conversion problem:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "intfloat/e5-small-v2",
    backend="onnx",
    model_kwargs={"provider": "CPUExecutionProvider"},
)
```

Sentence Transformers documents ONNX as a supported backend and explains that ONNX export preserves the Transformer component while pooling and normalization remain necessary for sentence embeddings.
Source: https://sbert.net/docs/sentence_transformer/usage/efficiency.html

ONNX Runtime publishes a CPU package for Windows x64 and supports CPU and hardware-specific execution providers through one API.
Only one of the CPU or GPU Python packages should be installed in an environment.
Sources:

- https://onnxruntime.ai/docs/get-started/with-python.html
- https://onnxruntime.ai/docs/execution-providers/

The ONNX path should be treated as an implementation option, not as a different embedding model.
Validate that model outputs and cluster assignments remain acceptably close to the PyTorch reference before switching.

## Clustering Design

For 1,256 nodes, begin with cosine-distance agglomerative clustering.
Scikit-learn supports `metric="cosine"` and average linkage for agglomerative clustering.
It also supports a distance threshold when the desired number of groups is unknown.
Source: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AgglomerativeClustering.html

Use K-Means only when a stable, fixed number of visual colors is required.
K-Means requires `n_clusters`; use a fixed `random_state` and compare several candidate values.
Source: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html

DBSCAN can identify noise nodes without specifying the number of clusters, but its scikit-learn implementation can require quadratic memory in the worst case.
Use it only if outlier detection is more important than stable color assignment.
Source: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html

Recommended first experiment:

1. Run BGE-small-en-v1.5 Q8_0 GGUF through the installed `llama-server.exe` with CLS pooling and L2 normalization.
2. Encode the same reviewed node-pair sample with an upstream BGE reference and compare cosine-score ordering.
3. Evaluate Granite Small English R2 only after its GGUF artifact, revision, and hash are approved.
4. Run agglomerative clustering with cosine distance and several thresholds.
5. Inspect cluster sizes and representative labels, then compare against E5-small-v2.
6. Select a threshold that avoids one giant cluster and excessive singleton clusters.
7. Assign colors from a deterministic palette keyed by semantic cluster ID.
8. Keep structural Graphify community IDs visible as a separate attribute.

## Hybrid Graphify Integration

Do not replace or rewrite Graphify's graph edges.

Create a derived sidecar such as:

```json
{
  "model": "ggml-org/bge-small-en-v1.5-Q8_0-GGUF",
  "model_revision": "...",
  "embedding_dimension": 384,
  "input_prefix": "",
  "pooling": "cls",
  "normalization": "l2",
  "cluster_method": "agglomerative_cosine",
  "nodes": {
    "stable-node-id": {
      "semantic_cluster": 3,
      "semantic_color": "#...",
      "confidence": 0.0
    }
  }
}
```

Join sidecar records by the existing stable node `id`.
Keep the original `community` and `community_name` fields unchanged.
Add semantic attributes only in the visualization layer or in a new derived artifact.

The visualization should distinguish:

- Structural edges: existing Graphify relationships.
- Structural communities: existing Graphify community assignments.
- Semantic clusters: embedding-derived groups.
- Semantic colors: derived visual encoding.

Semantic clustering labels and colors are exploratory aids.
They are not authoritative domain classifications and must not change edge direction, relation type, provenance, confidence, source location, or Graphify reachability.

## Validation and Open Risks

The decisive local check is a small manually reviewed set of related and unrelated node pairs drawn from this graph.
Compare E5 and BGE using the same node text and inspect whether groups correspond to recognizable test-program concepts such as logging, trimming, ADC, EEPROM, alarms, or setup helpers.

No model has been evaluated here against labeled UR78FT semantic groups.
No local CPU benchmark was run.
The 512-token limit means long function bodies or source excerpts must be summarized or chunked consistently before embedding.

Pin the model revision and runtime versions for reproducibility.
Recompute the derived semantic layer when the source graph or node text changes.
