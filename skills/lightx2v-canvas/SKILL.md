---
name: lightx2v-canvas
description: Create, inspect, edit and run an owned LightX2V Canvas from an external agent using the LightX2V CLI and API Key. Use for Canvas workflows, nodes, media references, connections, groups and exact run deliverables.
---

On a server with browser authorization enabled, CLI v0.3.3+ supports lightx2v login. In a headless environment, run lightx2v login --headless --json and show only the URL and short code. After the user approves, run lightx2v login --resume --json in the same environment and against the same origin. Exit code 3 means pending; follow retry_after. Run lightx2v models once connected. CLI credentials last 30 days and are revocable in API Keys. Use lightx2v login --api-key for manual entry.


Use the installed `lightx2v` CLI (0.3.0 or compatible) and configured API Key/base URL. Do not read or print secret configuration. No Cookie, chat session or Agent Worker is needed.

Run `lightx2v doctor --json` first. Check protocol=public-canvas-v1, deployment enabled, account_allowed. If unsupported, report the missing capability; do not fall back to browser cookies or whole-graph replacement.

Create an empty canvas with `workflow create --name NAME --operation-id ID --json`, then `workflow use WORKFLOW_ID --json` for project context. `workflow capabilities --json` returns live tools/models/parameters/ports and edit_schema; use it rather than remembered model IDs or a copied whitelist. Search with `workflow nodes`; retain stable IDs, not names, for writes. `node get ID --include content` reads text bodies explicitly. For a Script use `workflow script read NODE_ID --section shots --json`. Keep the returned `revision` for subsequent pages (`--revision REV --offset NEXT_OFFSET`). Use `--view detail` or repeated `--id ID` to retrieve full records; `--section anchors` selects the anchors.

Before writing anchor prompts, run `workflow script guide --topic anchor-prompts --json`. It returns writing guidance and complete examples for character, scene, prop and voice anchors. Write the image prompt in `description`; use `voice_prompt` for the voice identity and the exact sample words when generating reference audio. Reuse sufficient existing assets and choose views based on what later clips show.

Preview a pinned revision with `workflow script preview --input @preview.json`, supplying `stage=video` and target shot IDs. Review the resolved video prompt and ordered anchor inputs. Send the same request with `preview_digest` and `preview_shots` (the returned `shot_digests`) to `workflow script create-group --input @create.json --operation-id ID`. This saves video nodes, edges and the group. Read the original receipt with `workflow operation get`.

Use `workflow upload --file PATH --operation-id ID --json` for local images/video/audio. Connect returned input IDs separately. `workflow edit --input @ops.json --operation-id ID --json` is the atomic typed batch; @item_id references earlier created items. A Script creation receipt includes `script_documents` with the saved node and revision, production registration, and connected source node IDs. Node/connection/group convenience commands convert to this same contract. Use `--help` for exact flags. Do not write task state, runtime metadata, authors or past artifacts.

For every change/run, retain one operation ID and original payload. CLI journals them before sending in .lightx2v/operations/. On exit 4 (unknown), query `workflow operation get WORKFLOW_ID OP_ID --kind edit|upload|run|create --json`, or retry the identical request. Never rotate ID or version after timeout. Explicit conflicts need a fresh read and intentional new edit, not silent overwrite. saved/bound confirms graph publication; upload_persisted alone does not. accepted means run admission only.

`workflow quote WORKFLOW_ID ... --json` observes API fees; complete=false means partial quote, not a free remainder. A run invokes paid API generation under existing account authorization. Submit only within the user's requested scope; CLI does not add human approval. `workflow run WORKFLOW_ID --mode single --node-id ID --operation-id ID --json` returns run_id. `wait WORKFLOW_ID RUN_ID --until outputs --json` observes that run. Exit 3 means local wait timed out; Ctrl-C stops observation, not server execution. Cancel explicitly with `workflow cancel WORKFLOW_ID RUN_ID`.

Download with `workflow download WORKFLOW_ID --run-id RUN_ID -o DIR --zip --json`. Select exact node/group IDs when needed. Inspect complete/failures and manifest SHA256. Deliver only readable outputs, and distinguish completed, failed, cancelled and unavailable. Do not substitute the node's newer selected artifact for the requested run. Never attach the platform Key to CDN/third-party media requests; use the CLI download implementation.
