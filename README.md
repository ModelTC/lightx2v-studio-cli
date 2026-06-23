# lightx2v-studio-cli

Agent skills and install docs for the **LightX2V CLI** — submit, poll, and download AI image/video generation tasks via [x2v.light-ai.top](https://x2v.light-ai.top) OpenAPI.

## Install the Agent skill

```bash
npx skills add ModelTC/lightx2v-studio-cli@lightx2v-cli -g -y
```

Or install all skills from this repo:

```bash
npx skills add ModelTC/lightx2v-studio-cli -g -y
```

## Install the CLI

The skill teaches your agent how to use `lightx2v`. Install the binary separately:

```bash
curl -fsSL https://raw.githubusercontent.com/ModelTC/lightx2v-studio-cli/main/install.sh | sh
```

Or with pip (from [LightX2V-Deploy](https://github.com/ModelTC/LightX2V)):

```bash
pip install "lightx2v-cli @ git+https://github.com/ModelTC/LightX2V.git#subdirectory=LightX2V-Deploy"
```

Then:

```bash
lightx2v login
lightx2v models
lightx2v run t2i/Qwen-Image-2512 --prompt "a cute cat" --shape 512,512 -o out.png
```

See [cli-install.md](./cli-install.md) for details.

## Quick example

```bash
export LIGHTX2V_BASE_URL="https://x2v.light-ai.top"
export LIGHTX2V_API_KEY="apikey_xxxxxxxx"

lightx2v run t2v/Wan2.2_T2V_A14B_distilled \
  --prompt "waves at sunset" \
  --shape 720,1280 \
  -o beach.mp4
```

## Links

- Platform: https://x2v.light-ai.top
- API docs: https://x2v.light-ai.top/api-docs
- OpenAPI: https://x2v.light-ai.top/openapi.json
- LightX2V GitHub: https://github.com/ModelTC/LightX2V

## License

MIT
