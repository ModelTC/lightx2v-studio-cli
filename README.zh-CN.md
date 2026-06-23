# lightx2v-studio-cli

[English](README.md)

**LightX2V** 命令行客户端，通过 [x2v.light-ai.top](https://x2v.light-ai.top) OpenAPI 提交、轮询并下载 AI 图像/视频生成任务。

## 安装

```bash
curl -fsSL https://raw.githubusercontent.com/ModelTC/lightx2v-studio-cli/main/install.sh | sh
```

或使用 pip / pipx：

```bash
pip install "git+https://github.com/ModelTC/lightx2v-studio-cli.git"
```

更多安装方式见 [cli-install.md](./cli-install.md)。

## 快速开始

```bash
lightx2v login
lightx2v models
lightx2v run t2i/Qwen-Image-2512 --prompt "a cute cat" --shape 512,512 -o out.png
```

`lightx2v login` 会提示前往 https://x2v.light-ai.top 个人菜单 → API Key 获取密钥。

## Agent Skill

在 Cursor 等环境中做 Agent 自动化，请从 Skills 仓库安装：

```bash
npx skills add ModelTC/LightX2V-Skills@lightx2v-ai-video-generation -g -y
```

Skills 仓库：https://github.com/ModelTC/LightX2V-Skills

## 相关链接

- 平台：https://x2v.light-ai.top
- API 文档：https://x2v.light-ai.top/api-docs
- OpenAPI：https://x2v.light-ai.top/openapi.json

## 许可证

MIT
