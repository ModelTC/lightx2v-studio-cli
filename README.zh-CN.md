# lightx2v-studio-cli

[English](README.md)

**LightX2V** 命令行客户端，通过 [x2v.light-ai.top](https://x2v.light-ai.top) OpenAPI 提交、轮询并下载 AI 图像/视频生成任务，也支持 TTS 语音合成和音色克隆管理。

## 安装

```bash
curl -fsSL https://raw.githubusercontent.com/ModelTC/lightx2v-studio-cli/main/install.sh | sh
```

或使用 pip / pipx：

```bash
pip install "git+https://github.com/ModelTC/lightx2v-studio-cli.git"
```

更多安装方式见 [cli-install.md](./cli-install.md)。

查看版本或更新 CLI：

```bash
lightx2v --version
lightx2v update
```

服务端会通过 API 响应告知最新兼容版本。交互命令最多每 24 小时提醒一次；`--json` 和 `--quiet` 输出不会受到影响。

## 快速开始

```bash
lightx2v login
lightx2v models
lightx2v run t2i/Qwen-Image-2512 --prompt "a cute cat" --shape 512,512 -o out.png
```

MiniMax-H3 使用 `resolution_level` 选择分辨率档位。需要 768P 时必须显式传入
`--resolution-level 768p`；`--shape` 只是底层自定义尺寸，不能代替分辨率档位：

```bash
lightx2v run t2av/MiniMax-H3 \
  --prompt "一支 15 秒的竖屏产品短片" \
  --aspect-ratio 9:16 \
  --resolution-level 768p \
  --duration 15 \
  -o product.mp4
```

`lightx2v login` 会提示前往 https://x2v.light-ai.top 个人菜单 → API Key 获取密钥。

## 语音命令

查看内置 TTS 音色：

```bash
lightx2v voices --limit 5
```

使用内置音色生成语音。`voice_type` 和 `resource_id` 需要从 `lightx2v voices` 中成对获取：

```bash
lightx2v tts \
  --text "你好，欢迎使用 LightX2V。" \
  --voice-type zh_female_vv_uranus_bigtts \
  --resource-id seed-tts-2.0 \
  -o speech.mp3
```

创建、保存、合成和删除克隆音色：

```bash
lightx2v voice-clone create ./voice_sample.wav --save-name "我的音色"
lightx2v voice-clone list
lightx2v voice-clone tts --speaker-id SPEAKER_ID --text "你好。" -o cloned.wav
lightx2v voice-clone delete SPEAKER_ID
```

## 工作流命令

```bash
lightx2v workflow list
lightx2v workflow list --page-size 5
lightx2v workflow create --input @workflow.json
lightx2v workflow inputs WORKFLOW_ID
lightx2v workflow run WORKFLOW_ID --poll
lightx2v workflow run WORKFLOW_ID --mode single --node-id NODE_ID --inputs @inputs.json --poll
lightx2v workflow runs WORKFLOW_ID --status running
lightx2v workflow status WORKFLOW_ID RUN_ID
lightx2v workflow stream WORKFLOW_ID RUN_ID
lightx2v workflow outputs WORKFLOW_ID RUN_ID
lightx2v workflow cancel WORKFLOW_ID RUN_ID
lightx2v workflow cancel-node WORKFLOW_ID RUN_ID NODE_ID
```

运行前先调用 `workflow inputs`，确认当前运行范围所需的输入节点 ID。运行输入以这些 ID 为键；文本值可以放在 `--inputs` JSON 中，本地图片、音频、视频文件可以用 `--input-file NODE_ID=PATH` 绑定，CLI 会自动转成 data URL。

```json
{
  "prompt_input": "一句简短商品文案"
}
```

```bash
lightx2v workflow run WORKFLOW_ID \
  --inputs @inputs.json \
  --input-file image_input=./product.png \
  --poll
```

需要实时监听时使用 `workflow stream`，它会输出 `run_status` 和 `run_outputs` SSE 事件；也可以使用 `status` 轮询。运行未结束时，`outputs` 会返回 `pending: true`。

数字人口播工作流示例：

```bash
cat > inputs.json <<'JSON'
{
  "script_input": "大家好，我是 LightX2V 生成的数字人。"
}
JSON

lightx2v workflow run WORKFLOW_ID \
  --inputs @inputs.json \
  --input-file portrait_input=./portrait.png \
  --poll

lightx2v workflow outputs WORKFLOW_ID RUN_ID
```

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
