# LightX2V CLI install

The CLI is published from this repo. **LightX2V-Deploy is internal and not required.**

## Prerequisites

- Python 3.10+
- `pip` or `pipx`

## Option 1: install script (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/ModelTC/lightx2v-studio-cli/main/install.sh | sh
```

## Option 2: pip from GitHub

```bash
pip install --upgrade pip
pip install "git+https://github.com/ModelTC/lightx2v-studio-cli.git"
```

With pipx (isolated env):

```bash
pipx install "git+https://github.com/ModelTC/lightx2v-studio-cli.git"
```

## Option 3: local development

```bash
git clone https://github.com/ModelTC/lightx2v-studio-cli.git
cd lightx2v-studio-cli
pip install -e .
```

## Configure

```bash
lightx2v login
```

Or environment variables:

```bash
export LIGHTX2V_BASE_URL="https://x2v.light-ai.top"
export LIGHTX2V_API_KEY="apikey_xxxxxxxx"
```

Get an API key at https://x2v.light-ai.top (user menu → API Key).

## Verify

```bash
lightx2v --help
lightx2v models
```

## Shell completion

```bash
eval "$(lightx2v completion bash)"
eval "$(lightx2v completion zsh)"
```
