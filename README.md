# lightx2v-studio-cli

On a server with browser authorization enabled, CLI v0.3.3+ supports lightx2v login. In a headless environment, run lightx2v login --headless --json and show only the URL and short code. After the user approves, run lightx2v login --resume --json in the same environment and against the same origin. Exit code 3 means pending; follow retry_after. Run lightx2v models once connected. CLI credentials last 30 days and are revocable in API Keys. Use lightx2v login --api-key for manual entry.


[中文](README.zh-CN.md)

Command-line client for **LightX2V** — submit, poll, and download AI image/video generation tasks, generate TTS audio, and manage cloned voices via [x2v.light-ai.top](https://x2v.light-ai.top) OpenAPI.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/ModelTC/lightx2v-studio-cli/main/install.sh | sh
```

Or with pip / pipx:

```bash
pip install "git+https://github.com/ModelTC/lightx2v-studio-cli.git"
```

See [cli-install.md](./cli-install.md) for details.

Check or update the installed CLI:

```bash
lightx2v --version
lightx2v update
```

API responses advertise the latest compatible CLI version. Interactive commands show an update reminder at most once every 24 hours; `--json` and `--quiet` output stays unchanged.

## Quick start

```bash
lightx2v login
lightx2v models
lightx2v run t2i/Qwen-Image-2512 --prompt "a cute cat" --shape 512,512 -o out.png
```

MiniMax-H3 uses `resolution_level` to select its output tier. To request 768P,
pass `--resolution-level 768p` explicitly. `--shape` is a low-level custom size
and does not replace the resolution tier:

```bash
lightx2v run t2av/MiniMax-H3 \
  --prompt "A 15-second vertical product film" \
  --aspect-ratio 9:16 \
  --resolution-level 768p \
  --duration 15 \
  -o product.mp4
```

## Voice commands

List built-in TTS voices:

```bash
lightx2v voices --limit 5
```

Generate speech with a built-in voice. Use `voice_type` and `resource_id` from `lightx2v voices` together:

```bash
lightx2v tts \
  --text "Hello from LightX2V." \
  --voice-type zh_female_vv_uranus_bigtts \
  --resource-id seed-tts-2.0 \
  -o speech.mp3
```

Create, save, synthesize with, and delete cloned voices:

```bash
lightx2v voice-clone create ./voice_sample.wav --save-name "My voice"
lightx2v voice-clone list
lightx2v voice-clone tts --speaker-id SPEAKER_ID --text "Hello." -o cloned.wav
lightx2v voice-clone delete SPEAKER_ID
```

## Canvas commands

```bash
lightx2v canvas list
lightx2v canvas list --page-size 5
lightx2v canvas create --input @workflow.json
lightx2v canvas inputs CANVAS_ID
lightx2v canvas run CANVAS_ID --poll
lightx2v canvas run CANVAS_ID --mode single --node-id NODE_ID --inputs @inputs.json --poll
lightx2v canvas runs CANVAS_ID --status running
lightx2v canvas status CANVAS_ID RUN_ID
lightx2v canvas stream CANVAS_ID RUN_ID
lightx2v canvas outputs CANVAS_ID RUN_ID
lightx2v canvas cancel CANVAS_ID RUN_ID
lightx2v canvas cancel-node CANVAS_ID RUN_ID NODE_ID
```

Call `canvas inputs` before a run to discover required Input node IDs for the selected scope. Run inputs are keyed by those IDs. Text values can be passed through `--inputs`; local image, audio, and video files can be bound with `--input-file NODE_ID=PATH` and are converted to data URLs automatically.

```json
{
  "prompt_input": "A concise product tagline"
}
```

```bash
lightx2v canvas run CANVAS_ID \
  --inputs @inputs.json \
  --input-file image_input=./product.png \
  --poll
```

Use `canvas stream` for server-sent `run_status` and `run_outputs` events, or use `status` for polling. `outputs` returns `pending: true` until the run reaches a terminal state.

Digital-human canvas example:

```bash
cat > inputs.json <<'JSON'
{
  "script_input": "Hello, I am a LightX2V digital human."
}
JSON

lightx2v canvas run CANVAS_ID \
  --inputs @inputs.json \
  --input-file portrait_input=./portrait.png \
  --poll

lightx2v canvas outputs CANVAS_ID RUN_ID
```

## Agent skill

For Cursor / agent automation, install the skill from the separate repo:

```bash
npx skills add ModelTC/LightX2V-Skills@lightx2v-ai-video-generation -g -y
```

Skills repo: https://github.com/ModelTC/LightX2V-Skills

## Links

- Platform: https://x2v.light-ai.top
- API docs: https://x2v.light-ai.top/api-docs
- OpenAPI: https://x2v.light-ai.top/openapi.json

## License

MIT

## Public Canvas for external agents (0.3.0)

Requires a public-canvas-v1 server with public admission enabled, a valid API Key and Canvas entitlement. No Cookie, chat session or Agent Worker. Runs use API billing and invocation authorization; quote is read-only.

```bash
lightx2v doctor --json
lightx2v canvas create --name "Agent canvas" --operation-id canvas-001 --json
lightx2v canvas use CANVAS_ID --json
lightx2v canvas capabilities --json
lightx2v canvas upload --file ./reference.png --operation-id upload-001 --json
lightx2v canvas node create --tool-id text-document --body "Prompt" --operation-id text-001 --json
lightx2v canvas edit --input @ops.json --operation-id graph-001 --json
lightx2v canvas script read SCRIPT_NODE_ID --section shots --json
lightx2v canvas script preview --input @preview.json --json
lightx2v canvas script create-group --input @create-group.json --operation-id shot-group-001 --json
lightx2v canvas quote CANVAS_ID --mode single --node-id NODE_ID --json
lightx2v canvas run CANVAS_ID --mode single --node-id NODE_ID --operation-id run-001 --json
lightx2v canvas operation get CANVAS_ID run-001 --kind run --json
lightx2v canvas wait CANVAS_ID RUN_ID --until outputs --json
lightx2v canvas download CANVAS_ID --run-id RUN_ID -o ./delivery --zip --json
```

Node, connection and group commands are listed by `lightx2v canvas --help`; capabilities.edit_schema is the authoritative batch schema, including @item_id references. Read content/configuration on demand.

New commands support --json; stdout is JSON and recovery identity goes to stderr. Original requests are saved before submission in the nearest .lightx2v/operations/; context stores service/account/workflow, never the Key. Recover unknown results with the same ID and payload, never a new ID. Exit 4 means unknown, 3 wait timeout, 2 invalid arguments, 1 definitive failure. Ctrl-C stops observation only; cancel explicitly. quote complete=false means incomplete pricing. Download selects the exact run, returns nonzero on partial failure and never overwrites existing files.

Legacy `canvas create --input` retains JSON-create semantics; the new --name path provides operation identity/idempotency.

[External agent skill](skills/lightx2v-canvas/SKILL.md). Isolated executor tests and one authorized development-8081 real-provider image generation/cancellation have passed (gpt-image-2.5-flare). Package publication and production activation have not occurred; this is not verification of every provider/model.


For public run/quote commands, pair `--node-id` with `--mode single` (or downstream/upstream). The default full mode with a node scope is rejected as an argument error to prevent unintended whole-canvas execution.

## Self-describing Script authoring

No basic/product skill is required. These read-only commands query the authenticated server contract without a canvas context:

```bash
lightx2v canvas script schema --json
lightx2v canvas script schema --section anchors --json
lightx2v canvas script schema --field anchors.variant_of --json
lightx2v canvas script schema --section shots --json
lightx2v canvas script examples --case create-script --json
lightx2v canvas script examples --case create-script --payload-only > create.json
lightx2v canvas script guide --topic anchor-prompts --json
lightx2v canvas script examples --case anchor-prompts --json
lightx2v canvas script guide --topic preflight --json
```

The default response is a section catalogue. Field/section responses derive types, defaults and required fields from the current backend model, with authoring semantics and service-maintained field notes. Examples include explicit replacement instructions for runtime identities and owned media. Variants inherit their base voice by default unless they already contain explicit local voice settings. Set voice_source to inherit/independent to choose explicitly, or voice_enabled=false to disable voice. One shot record represents a generated video clip and may contain multiple camera shots. Read the preflight guide and inspect actual prompts, references, issues and review flags before saving groups. Saving does not run generation. Servers without discovery return an explicit upgrade error rather than silently guessing a schema.

```bash
lightx2v canvas script examples --case reuse-scene-layout --json
```

For consecutive clips in one location, establish a shared blocking/layout image at the first clip and adopt the same exact ref on a separate visual-reference record per clip. Follow each returned revision. Video groups automatically consume adopted images. Layout references do not imply an exact first-frame binding.


### Script operation discovery

Query live request schemas before writing Script records. Public actions share the server Canvas contracts.

```bash
lightx2v canvas script schema --action edit
lightx2v canvas script schema --action prepare-anchors
lightx2v canvas script examples --case edit-record --payload-only
lightx2v canvas script edit --canvas-id CANVAS_ID --input @edit.json --operation-id edit-v1
lightx2v canvas script sync-anchors --canvas-id CANVAS_ID --input @sync.json --operation-id sync-v1
lightx2v canvas operation get sync-v1 --canvas-id CANVAS_ID --kind sync
```

Additional actions include prompts and select-output. Use schema --action ACTION and examples --case ACTION for exact payloads. Read sections include subjects, outputs, media_sources and production. Reads default to compact summaries. Request details by stable ID and pin document pagination to revision. For Script prompts, use mode=options to list full-reference generation_models. Use mode=optimize with generation_model set to an available ID with a preset_id. Compose remains deterministic. Both return candidates without saving or starting video generation. See canvas script examples --case prompts. Saving groups does not start media generation. Reuse the original operation ID and payload for recovery. A new sync operation observes newly available results.

CLI 0.3.4 uses `lightx2v canvas` throughout help, completion and examples. The previous command spelling remains a hidden compatibility alias. API routes and response keys retain their existing protocol names.
