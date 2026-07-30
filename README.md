# lightx2v-studio-cli

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

## Quick start

```bash
lightx2v login
lightx2v models
lightx2v run t2i/Qwen-Image-2512 --prompt "a cute cat" --shape 512,512 -o out.png
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

## Workflow commands

```bash
lightx2v workflow list
lightx2v workflow list --public --page-size 5
lightx2v workflow create --input @workflow.json
lightx2v workflow run WORKFLOW_ID --poll
lightx2v workflow run WORKFLOW_ID --mode single --node-id NODE_ID --inputs @inputs.json --poll
lightx2v workflow status WORKFLOW_ID RUN_ID
lightx2v workflow outputs WORKFLOW_ID RUN_ID
```

Run inputs are keyed by input node ID. Text values can be passed through `--inputs`; local image, audio, and video files can be bound with `--input-file NODE_ID=PATH` and are converted to data URLs automatically.

```json
{
  "prompt_input": "A concise product tagline"
}
```

```bash
lightx2v workflow run WORKFLOW_ID \
  --inputs @inputs.json \
  --input-file image_input=./product.png \
  --poll
```

Digital-human workflow example:

```bash
cat > inputs.json <<'JSON'
{
  "script_input": "Hello, I am a LightX2V digital human."
}
JSON

lightx2v workflow run WORKFLOW_ID \
  --inputs @inputs.json \
  --input-file portrait_input=./portrait.png \
  --poll

lightx2v workflow outputs WORKFLOW_ID RUN_ID
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
