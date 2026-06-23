# lightx2v-studio-cli

[中文](README.zh-CN.md)

Command-line client for **LightX2V** — submit, poll, and download AI image/video generation tasks via [x2v.light-ai.top](https://x2v.light-ai.top) OpenAPI.

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
