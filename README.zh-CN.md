# LightX2V CLI 使用教程

**把创作需求交给 Agent，也可以用终端精确控制每一步。**

适用版本：CLI 0.3.3 · 内容更新：2026-11-27 · 文档修订：2026-11-27-r1

> **新版发布前说明**：本教程按 0.3.3 完整能力编写。目前官方 GitHub 主分支仍为 0.2.0；浏览器授权和公共画布功能需要新版 CLI 与兼容服务共同支持。开发服务已完成非生成查询验证，公网公共画布自检入口尚未通过。正式使用前请先检查版本和 `doctor`；不要把成功安装旧版当作新版已可用。具体核验范围见文末。

[平台](https://x2v.light-ai.top) · [CLI 仓库](https://github.com/ModelTC/lightx2v-studio-cli) · [API 文档](https://x2v.light-ai.top/api-docs) · [OpenAPI](https://x2v.light-ai.top/openapi.json) · [飞书教程](https://my.feishu.cn/wiki/P7e4wqY1uie5kAklYlncbxckn8b)

## 阅读导航

1. CLI 是什么，能帮你做什么
2. 快速开始：Agent 与终端两条路线
3. 安装、登录与环境检查
4. 图片、视频与音频生成
5. 任务管理与结果交付
6. 创建和编辑画布
7. 分镜脚本完整流程
8. 可以直接交给 Agent 的六类案例
9. 积分、状态和异常恢复
10. 常见问题与命令速查

第一次使用，先读第 2、3 章；要制作连续短剧，再读第 6、7 章；任务超时或结果不明时，直接查第 9 章。

## 1. CLI 是什么，能帮你做什么

LightX2V CLI 是 LightX2V 的命令行客户端。它把素材生成和画布操作开放给终端、脚本和能够执行本地命令的 Agent，例如 Codex、Claude Code、Cursor。

你可以直接输入命令，也可以告诉 Agent“用这张产品图做一个竖屏广告，先给我分镜，确认后再生成”。Agent 负责把需求拆成步骤，通过 CLI 保存脚本、准备参考素材、运行指定节点，并整理结果。

| 你使用的入口 | 负责什么 | 你得到什么 |
| --- | --- | --- |
| 网页画布 | 查看、编辑、预览和检查创作内容 | 可继续编辑的项目 |
| CLI | 调用当前账户可用的模型、画布和运行接口 | 任务回执、画布变更、下载文件 |
| 外部 Agent | 理解需求、组织流程、调用 CLI、处理错误 | 按需求组织的脚本与素材交付 |

CLI 支持图片与视频任务、内置 TTS、音色克隆，以及兼容服务上的节点、连接、编组、文本和结构化分镜脚本。具体模型、参数和账户权限以当前服务返回为准。

**两个生成入口要分清：**

- `lightx2v run`：直接提交一个素材任务。它不等于在你指定的画布里创建节点。
- `lightx2v workflow ...`：读取或编辑画布，再运行指定节点、编组或整张画布。想在网页继续调整项目，优先走这条路线。

CLI 也不是本地视频剪辑软件。“生成片段”不自动等于“剪辑成片”；拼接、字幕、配乐混音和最终质检，需要 Agent 使用另行可用的工具完成，并说明使用了什么工具。

## 2. 快速开始：Agent 与终端两条路线

### 2.1 路线 A：发送给 Agent

准备一个能够运行终端命令的 Agent，以及可使用 LightX2V 的账户。把下面整段文字发给 Agent，**不要把这段自然语言粘贴到终端**。

> 请帮我配置 LightX2V CLI。先阅读官方仓库 https://github.com/ModelTC/lightx2v-studio-cli 的当前安装说明，检查 Python 和已安装的 CLI 版本；不要重复安装。按官方来源安装或更新，确认版本支持本教程所需的 0.3.3 能力。可用时安装官方 lightx2v-ai-video-generation Skill。发起浏览器授权让我确认；如果你在远程或无界面环境，使用 headless 授权，只把授权网址和短码交给我，确认后在同一环境续查。不要读取、展示或把密钥写进聊天。连接后查询 models 和 doctor，分别报告素材生成、公共画布是否可用。先不要提交生成任务。如果公开安装包或服务还未支持新版，请明确告诉我缺少什么。

配置完成后，可以继续发：

> 我想用产品参考图制作一个 9:16 的短片。先读取模型能力，创建一张名为“产品广告”的画布，上传我提供的图片并保存分镜草案。先交付画布链接、分镜、拟用模型和运行范围；暂不运行生成。需要生成时先给我可获取的估价，不完整的估价要说明。

**成功标准**：Agent 报告实际 CLI 版本、连接的服务、模型查询结果和画布可用性；保存画布后给出真实画布标识或服务返回的链接。只回复“已配置”不够。

Skill 可辅助 Agent 理解流程，但不是所有命令的前置依赖。新版 Script 字段和请求格式可以直接向服务查询，不能用旧 Skill 覆盖服务返回的规范。

### 2.2 路线 B：粘贴到终端

以下示例使用 Bash / zsh。先完成第 3 章安装与授权，再执行只读检查：

```bash
lightx2v --version
lightx2v --help
lightx2v login
lightx2v models --json
lightx2v doctor --json
```

| 步骤 | 预期结果 |
| --- | --- |
| 检查版本 | 输出当前版本；新版功能要求 0.3.3 |
| 查看帮助 | 能看到需要使用的命令，而不是 `invalid choice` |
| 登录 | 在网页完成授权，CLI 返回成功 |
| 查询模型 | 返回账户可用的 `task` / `model_cls` |
| 自检画布 | 返回 `public-canvas-v1`，检查启用状态与账户准入 |

确认账户有相应模型权限、你也准备好开始生成后，再执行首个素材任务：

```bash
lightx2v run t2i/Qwen-Image-2512 \
  --prompt "浅灰背景上的一盏陶瓷台灯，柔和自然光，产品摄影" \
  --shape 512,512 \
  -o ./output/lamp.png
```

这里的模型来自查询示例，实际使用前仍应确认它在你的模型列表中，且支持相应尺寸。**该命令会提交生成，可能消耗积分。**

成功时可以看到 `task_id`、任务成功状态和本地保存路径。打开文件确认内容可读，再把这个任务视为交付完成。失败或等待超时后先查询原 `task_id`，不要立即重复执行生成命令。

### 2.3 示例中的占位符怎么替换

`WORKFLOW_ID`、`NODE_ID`、`RUN_ID`、`TASK_ID` 等大写名称是占位符，必须替换成真实回执中的值。`@inputs.json` 表示读取本地 JSON 文件；`@item_id` 在画布编辑 JSON 内表示引用同一批次先前创建的项目，两者含义不同。

命令中不要写 `<NODE_ID>` 这样的尖括号：Shell 可能把它解释为文件重定向。Windows 用户使用 PowerShell 时，将多行 Bash 命令改写成单行；不要直接复制 Bash 的反斜杠续行或 heredoc。

## 3. 安装、登录与环境检查

### 3.1 安装与更新

需要 Python 3.10+。从 GitHub 安装还需要 Git 和可访问官方仓库的网络。

**macOS / Linux：官方脚本**

```bash
curl -fsSL https://raw.githubusercontent.com/ModelTC/lightx2v-studio-cli/main/install.sh | sh
```

**隔离安装：pipx**（先按 pipx 官方说明安装 pipx）

```bash
pipx install "git+https://github.com/ModelTC/lightx2v-studio-cli.git"
lightx2v --version
```

已经用 pipx 安装时，可以运行 `pipx upgrade lightx2v-cli`。避免同时用多个 Python / pipx 环境安装，造成执行到旧版本。

**Python 虚拟环境：macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade "git+https://github.com/ModelTC/lightx2v-studio-cli.git"
lightx2v --version
```

这是官方 Git 安装方式加上隔离环境。不要使用 `sudo pip` 绕过系统 Python 的管理限制。

Windows 可采用 Python 虚拟环境和同一 Git 安装来源；本轮尚未在 Windows 实机验证，不把它标为已验证路径。本仓库未提供即梦那样的专用 PowerShell / CMD 安装器。

```bash
lightx2v update
lightx2v --version
```

更新后再次检查版本和帮助。更新不保证尚未发布的能力已经可用；正式安装来源发布新版前，仍会安装当前公开版本。

### 3.2 浏览器授权

```bash
lightx2v login
lightx2v models
```

在浏览器核对目标服务与账户，完成授权，再回到终端。浏览器已经登录网站，不代表 CLI 已经授权；授权后也要查询一次模型确认连接正常。

新版浏览器授权凭证有效期为 30 天，可在网站 API Key 管理中撤销；以实际授权页和服务策略为准。不要把凭证、配置文件或完整授权响应发给其他人。

### 3.3 远程服务器或无界面环境

```bash
lightx2v login --headless --json
```

把返回的网页授权地址和短码交给实际账户使用者。完成网页确认后，在**同一台机器、同一 CLI 环境、同一服务地址**继续：

```bash
lightx2v login --resume --json
lightx2v models --json
```

`login --resume` 的退出码 `3` 表示仍在等待授权，按返回的 `retry_after` 续查。不要不断新建授权请求，不要把内部 `device_code` 交给用户或复制到聊天。

### 3.4 手动 API Key 与服务地址

对于已有 API Key，或还未支持浏览器授权的服务：

```bash
lightx2v login --api-key
```

在隐藏输入提示中粘贴自己的 Key。不要把真实 Key 直接写进命令行参数、脚本仓库或截图。

需要连接其他合法部署时，指定服务根地址，而不是 `/api/v1` 路径：

```bash
lightx2v login --base-url https://YOUR_SERVICE_ORIGIN
```

默认服务是 `https://x2v.light-ai.top`。远程授权要求 HTTPS；本机开发地址可使用本地 HTTP。更换服务后要重新核对账户与授权，不要把一个服务的 Key 发到另一个服务。

CI 可通过秘密变量注入 `LIGHTX2V_API_KEY`；服务地址可用 `LIGHTX2V_BASE_URL`。兼容变量还有 `LIGHTX2V_CLOUD_API_KEY`、`LIGHTX2V_CLOUD_URL`、`API_BASE_URL`。环境变量优先于配置文件，故“登录后仍连错服务”时应先检查是否存在旧环境变量，但不要输出变量中的密钥。

### 3.5 公共画布自检

```bash
lightx2v doctor --json
```

检查 `protocol` 是否为 `public-canvas-v1`，并区分 `supported`、`enabled`、`account_allowed` 和 `new_operations_allowed`。服务有代码、服务已启用、账户允许使用，是不同条件。

公共画布需要兼容后端和账户 Canvas 权益。自检返回 404、协议不可用或权限不足时，先解决服务版本或权限；不要靠复制网页 Cookie 绕过限制。外部 CLI 操作公共画布不依赖网页小光聊天会话或 Agent Worker。

### 3.6 安装 Agent Skill

安装了 Node.js / npx 的环境可执行：

```bash
npx skills add ModelTC/LightX2V-Skills@lightx2v-ai-video-generation -g -y
```

按目标 Agent 的 Skill 加载规则启用。公共画布流程也可参考仓库内的 [Canvas Skill](https://github.com/ModelTC/lightx2v-studio-cli/blob/main/skills/lightx2v-canvas/SKILL.md)；该链接随新版代码发布后可用。Skill 提供流程指导，实际模型、参数与 Script 字段仍查实时能力。

## 4. 图片、视频与音频生成

### 4.1 先查模型，再填参数

```bash
lightx2v models --json
lightx2v run --help
```

目标写为 `task/model_cls`，不是网页显示名称。例如 `t2i/Qwen-Image-2512`。模型出现在其他人的教程中，不代表你的账户也能运行。

`models` 提供模型目录；更详细的模型参数约束需查当前 API 文档 / OpenAPI，或在画布中查询 `workflow capabilities`。不要假设所有模型都接受同一画幅、分辨率、时长或参考数量。

| 参数 | 用途 |
| --- | --- |
| `--prompt` | 创作提示词；素材 `run` 必须提供它或在 JSON 中提供 `prompt` |
| `--image` / `--video` / `--audio` | 将本地素材读入相应单个输入字段 |
| `--aspect-ratio` | 模型支持的画幅比例，如 `9:16` |
| `--resolution-level` | 模型分辨率档位，如 `768p`；具体取值查模型 |
| `--shape` | 自定义尺寸，顺序是**高,宽**；不能替代分辨率档位 |
| `--duration` | 模型支持的秒数，不是所有任务都支持 |
| `--input @file.json` | 额外提交字段；字段结构以当前模型接口为准 |
| `-o` | 输出文件；直接素材下载可能覆盖同名文件，建议每次用新路径 |
| `--timeout` | 本地等待时限，默认 600 秒，不是服务端自动取消时间 |
| `--no-download` | 只返回结果地址，不自动保存 |

额外 JSON 合入请求后，显式便利参数会覆盖对应字段；例如同时提供 JSON 的 `prompt` 和 `--prompt`，以命令行的 `--prompt` 为准。不要让 `--input` 改写目标的 `task` / `model_cls`，造成实际提交与命令表面不一致。

下面是使用方式示例，均需先核对模型可用性；本轮未新提交这些计费任务，不将示例视为效果保证。

### 4.2 文生图与参考图改图

**发送给 Agent：**

> 用我提供的产品图生成一张竖屏广告图。先查询支持参考图的模型，保留产品形状、颜色和标识，给我提示词和参数，确认后再提交，最后交付原图与结果路径。

**粘贴到终端：文生图**

```bash
lightx2v run t2i/Qwen-Image-2512 \
  --prompt "一只透明玻璃杯，柔和晨光，浅色桌面，产品摄影" \
  --shape 512,512 -o ./output/glass.png
```

**粘贴到终端：单参考图改图**

```bash
lightx2v run i2i/Qwen-Image-Edit-2511 \
  --image ./product.png \
  --prompt "保留产品外观，将背景改为暖色木质桌面，柔和窗光" \
  -o ./output/product-edit.png
```

成功标准：任务成功、文件可读、参考产品未被意外替换。路径不存在时先修复本地路径；模型不支持参数时查接口，不要反复原样提交。

### 4.3 文生视频、图生视频与多参考

**发送给 Agent：**

> 根据参考图制作竖屏视频，保持主体身份和产品结构一致。先确认模型支持的时长、分辨率、参考素材数量和音频能力，再给我运行方案。只执行我确认的片段，失败时先诊断原任务。

**带音视频模型的文生视频示例：**

```bash
lightx2v run t2av/MiniMax-H3 \
  --prompt "夜色街角，镜头缓慢推进一间亮着暖光的咖啡店，轻微城市环境声" \
  --aspect-ratio 9:16 --resolution-level 768p --duration 8 \
  -o ./output/cafe.mp4
```

**单图生成带音视频示例：**

```bash
lightx2v run i2av/MiniMax-H3 \
  --image ./reference.png \
  --prompt "保持参考人物身份，人物抬头微笑，镜头缓慢推近，室内安静" \
  --aspect-ratio 9:16 --resolution-level 768p --duration 8 \
  -o ./output/portrait.mp4
```

不要把 `--shape` 当作 MiniMax-H3 的清晰度选择。清晰度档位应使用 `--resolution-level`，并按当前模型核对取值。

多图、多段音频、首尾帧和角色声音映射不应通过重复 `--image` 等单输入参数猜测实现。查询 `ref2av` / 对应模型的真实输入结构；参考复杂时用第 6 章画布连接，并显式检查素材顺序。成功后还需检查视频能否播放、有无声音、人物与参考是否对应。

### 4.4 音频生成：声音设计与配乐/音效

单独设计声音或生成音效、配乐时，使用画布的 `audio-generation` 工具。它与直接任务目录中的视频任务、内置 TTS 是不同入口，不要虚构一个 `lightx2v audio` 命令。

**发送给 Agent：**

> 在当前画布为这名角色设计固定声音。先读取 audio-generation 的模型、参考音频端口和可调参数；用普通话、克制温和的女声，试听台词为“今天，我们从这里出发。”先保存节点，不运行。确认后生成一段干净单人试听，交付音频和节点位置。

**粘贴到终端：先选择画布，再查询能力**

```bash
lightx2v workflow use WORKFLOW_ID --json
lightx2v workflow capabilities --tool-id audio-generation --json
```

将下面的 `MODEL_ID` 替换为当前能力返回的模型 ID，按模型约束补齐设置：

```bash
lightx2v workflow node create --tool-id audio-generation \
  --name "角色声音试听" \
  --parameters '{"model":"MODEL_ID"}' \
  --text-inputs '{"in-text":"普通话，克制温和的女声。只朗读：今天，我们从这里出发。干净单人声音。"}' \
  --operation-id voice-node-001 --json
```

这一步只保存节点。是否支持参考音频、配乐、音效或特定声音控制，要以该模型能力为准；不要把某个供应商的能力推广为所有音频模型都支持。返回真实节点后按第 6.6 节估价并运行该节点。成功标准是音频可播放、台词正确、没有把状态“已提交”当作已生成。

### 4.5 内置音色 TTS

适合输入确定台词、选择内置音色的语音合成。

```bash
lightx2v voices --limit 5
lightx2v voices --version 2.0 --json
```

从同一条音色记录取得 `VoiceType` 与 `ResourceID`，分别填入下列占位符：

```bash
lightx2v tts --text "你好，欢迎使用 LightX2V。" \
  --voice-type VOICE_TYPE --resource-id RESOURCE_ID \
  -o ./output/speech.mp3
```

可用控制项包括 `--context-texts`、`--emotion`、`--emotion-scale`、`--speech-rate`、`--loudness-rate`、`--pitch`；支持范围与效果以音色和服务为准。不要把不同记录的音色 ID 和资源 ID 拼在一起。默认输出是 `speech.mp3`。

### 4.6 音色克隆与复用

适合使用自己有权使用的参考声音，保存音色后反复合成新台词。

```bash
lightx2v voice-clone create ./voice-sample.wav \
  --text "参考音频实际说出的内容" --save-name "角色A"
lightx2v voice-clone list
```

`--text` 是参考音频的转写，不是让它新生成的台词；省略时由服务端 ASR 处理。未在创建时保存，可以稍后保存：

```bash
lightx2v voice-clone save SPEAKER_ID "角色A"
lightx2v voice-clone tts --speaker-id SPEAKER_ID \
  --text "这是使用保存音色生成的新台词。" \
  -o ./output/character-a.wav
```

合成支持 `--style`、`--speed`、`--volume`、`--pitch`、`--language`，具体约束查帮助与接口。默认输出 `cloned-voice.wav`。不再需要时才明确执行 `lightx2v voice-clone delete SPEAKER_ID`，不要在普通重试流程中自动删除音色。

## 5. 任务管理与结果交付

本章是直接素材任务；画布运行使用 `workflow status` 等命令，不能混用 ID。

```bash
lightx2v query TASK_ID --json
lightx2v list --status SUCCEED --page 1 --page-size 20 --json
lightx2v result TASK_ID -o ./output/recovered-result.png
```

`query` 查询一次状态；`result` 获取成功任务的结果，省略 `-o` 时只取地址。需要明确输出类型时使用 `--name`，其值必须对应当前任务的输出名称。

| 目的 | 命令 | 注意 |
| --- | --- | --- |
| 查看进度或错误 | `lightx2v query TASK_ID` | 先保留原始 task_id |
| 查找以前的任务 | `lightx2v list --page 1 --page-size 20` | 以真实任务状态筛选 |
| 下载成功结果 | `lightx2v result TASK_ID -o PATH` | 选择新路径，避免覆盖已有文件 |
| 取消正在运行的任务 | `lightx2v cancel TASK_ID` | 是服务端动作，随后再查询确认状态 |
| 恢复失败或已取消任务 | `lightx2v resume TASK_ID` | 会请求服务恢复执行，可能涉及计费；不等于只继续查询 |
| 删除已结束的任务记录 | `lightx2v delete TASK_ID` | 不应假设等同于删除所有媒体或返还积分 |

素材 `run` 默认每 2 秒查询，最多本地等待 600 秒。超时不证明任务失败，也不自动取消服务端任务。用原 ID 查询，成功后单独下载；只有明确决定恢复执行时才用 `resume`。

**交付检查**：文件存在、可打开；图片尺寸或视频时长符合要求；音视频可播放；结果对应本次任务。Agent 应同时给出任务 ID、参数摘要和本地结果位置，失败项单列，不用别的任务结果替代。

## 6. 创建和编辑画布

### 6.1 创建、选择与读取

```bash
lightx2v doctor --json
lightx2v workflow list --page-size 5 --json
lightx2v workflow create --name "我的创作画布" \
  --operation-id canvas-001 --json
lightx2v workflow use WORKFLOW_ID --json
lightx2v workflow get WORKFLOW_ID --json
lightx2v workflow capabilities --json
```

把创建回执中的画布 ID 填入 `workflow use`。它保存当前项目的服务、账户和画布上下文；换目录或账户后，不要假设仍指向同一张画布。大多数新增便捷命令可以省略当前画布 ID，显式指定时可用 `--workflow-id`。

`workflow create --name` 与旧式 `workflow create --input @workflow.json` 是不同入口：前者是公共创建及操作恢复流程；后者保留旧 JSON 建图语义，不要把二者的幂等保证混为一谈。

### 6.2 上传素材与创建节点

```bash
lightx2v workflow upload --file ./product.png \
  --name "产品参考" --operation-id upload-product-001 --json
lightx2v workflow node create --tool-id text-document \
  --name "创作说明" --body "竖屏产品短片，先保存方案再生成。" \
  --x 0 --y 0 --operation-id brief-001 --json
lightx2v workflow nodes --query "产品" --limit 20 --json
```

读取返回的真实节点 ID、素材引用和保存结果。上传完成不必然等于素材已绑定到画布：要确认回执已保存 / 已绑定，再读取节点核对。不要只看到 `upload_persisted` 就宣布画布更新完成。

创建生成节点前先查询具体工具。例如：

```bash
lightx2v workflow capabilities --tool-id text-to-image --json
lightx2v workflow node get NODE_ID --include configuration --include inputs --json
```

使用能力返回的 `allowed_models`、端口和参数 schema。图像输入、音频输入、视频输入需要持久素材引用；不要把数据库路径或临时下载地址冒充可持久化素材。

### 6.3 节点、连接与参考顺序

```bash
lightx2v workflow node move NODE_ID --x 640 --y 0 \
  --operation-id move-001 --json
lightx2v workflow node update NODE_ID --name "产品主图" \
  --operation-id rename-node-001 --json
lightx2v workflow node copy NODE_ID --x 640 --y 480 \
  --operation-id copy-001 --json
lightx2v workflow connect SOURCE_NODE_ID TARGET_NODE_ID \
  --source-port out-image --target-port in-image \
  --operation-id connect-001 --json
```

端口名称必须先从当前工具能力中确认，上例只示范图片端口。删除连接用 `workflow disconnect CONNECTION_ID`；删除节点用 `workflow node delete NODE_ID`，这两种写操作也应各自提供稳定 `--operation-id`。

多参考模型的素材顺序会影响提示词对应关系。先读取目标节点的输入标识，再重排：

```bash
lightx2v workflow reorder-inputs TARGET_NODE_ID \
  --target-port in-image \
  --input-id INPUT_ID_A --input-id INPUT_ID_B \
  --operation-id order-001 --json
```

这里用的是读取到的真实输入 ID，不要凭节点名字猜。调整后重新读取，检查参考图 A/B 与提示词中的角色仍一一对应。

### 6.4 编组与布局

```bash
lightx2v workflow group create --name "角色参考" \
  --node-id NODE_A --node-id NODE_B --operation-id group-001 --json
lightx2v workflow group list --json
lightx2v workflow group get GROUP_ID --json
lightx2v workflow group add GROUP_ID --node-id NODE_C \
  --operation-id add-member-001 --json
lightx2v workflow group remove GROUP_ID --node-id NODE_C \
  --operation-id remove-member-001 --json
```

`group move SOURCE_GROUP --target-group-id TARGET_GROUP` 用于转移成员，不是移动组的屏幕坐标；位置调整使用节点移动或实时编辑 schema 支持的布局动作。父子编组用 `group set-parent`，原父组信息需从最新读取结果取得；解除编组用 `group ungroup`，复制组用 `group copy`。

Agent 可以读取当前节点尺寸与组关系后计算布局，再提交位置变更。不要把“可以布局”理解为 CLI 自带一个未经查询的 `auto-layout` 命令。成员冲突时重新读取并按当前服务的编组规则处理，不盲目重试旧载荷。

### 6.5 批量编辑与文本协作

多个有关联的修改可写入 `ops.json`，调用：

```bash
lightx2v workflow edit --input @ops.json \
  --operation-id edit-batch-001 --json
```

最小示例：创建文档与生图节点，并连接文档文本。先确认工具、模型和端口约束，替换 `MODEL_ID`：

```json
{
  "items": [
    {"item_id":"brief","action":"create","tool_id":"text-document","body":"浅灰背景上的陶瓷台灯，柔和自然光"},
    {"item_id":"image","action":"create","tool_id":"text-to-image","parameters":{"model":"MODEL_ID"},"position":{"x":640,"y":0}},
    {"item_id":"link","action":"connect","source_node_id":"@brief","source_port_id":"out-text","target_node_id":"@image","target_port_id":"in-text"}
  ]
}
```

准确请求结构取自 `capabilities.edit_schema`。CLI 会补充当前版本并记录原请求；需要显式锁定时传 `--version`。批次保存成功后仍未开始生成。

编辑节点提示词或文档时，先读取文本，再按唯一锚点替换：

```bash
lightx2v workflow text get NODE_ID --kind document --json
lightx2v workflow text edit NODE_ID --kind document \
  --input '{"edits":[{"old":"柔和自然光","new":"午后侧逆光"}]}' \
  --operation-id text-edit-001 --json
```

`--kind prompt` 用于提示词，`--kind document` 用于文档。输入只选一种：`source` 全文替换、`append` 追加、`edits` 唯一锚点修改。旧文本不存在、重复多次或修订冲突时，重新读取再决定新修改；不要无提示覆盖他人的编辑。

### 6.6 估价、运行、等待与下载

先独立估价，检查完整性和运行范围：

```bash
lightx2v workflow quote WORKFLOW_ID \
  --mode single --node-id NODE_ID --json
```

确认开始生成后，提交同一范围：

```bash
lightx2v workflow run WORKFLOW_ID \
  --mode single --node-id NODE_ID \
  --operation-id run-node-001 --json
lightx2v workflow wait WORKFLOW_ID RUN_ID --until outputs --json
lightx2v workflow download WORKFLOW_ID --run-id RUN_ID \
  -o ./delivery/run-001 --zip --json
```

| 运行范围 | 参数 | 使用前检查 |
| --- | --- | --- |
| 指定节点 | `--mode single --node-id NODE_ID` | 依赖是否已有有效输入 |
| 节点及下游 | `--mode downstream --node-id NODE_ID` | 会触发哪些下游任务 |
| 上游范围 | `--mode upstream --node-id NODE_ID` | 需要运行的依赖范围，以服务返回为准 |
| 指定编组 | `--group-id GROUP_ID` | 组内成员和依赖；不能与 node-id 混用 |
| 整张画布 | `--mode full` | 是否真的需要运行全部节点 |

带 `--node-id` 时必须显式选择 single / downstream / upstream；默认 full 与节点 ID 组合会被拒绝。运行可能包含上游依赖，先用相同范围的 `workflow inputs` 和估价核对；`--no-include-upstream` 只在你明确理解影响时使用。

模板需要外部输入时，先查 `workflow inputs WORKFLOW_ID`。`--inputs @inputs.json` 以输入节点 ID 为键；本地文件可用 `--input-file NODE_ID=./product.png`。把相同输入用于 quote 和 run，避免估价与实际运行不一致。

读取进度可用 `workflow status WORKFLOW_ID RUN_ID`、`workflow stream WORKFLOW_ID RUN_ID`、`workflow outputs WORKFLOW_ID RUN_ID`。`wait --until terminal` 观察终态；`--until outputs` 还检查输出可用性。`outputs` 返回 `pending: true` 时继续观察原运行。

下载必须指定确切 `--run-id`，还可按 `--node-id` 或 `--group-id` 过滤。检查返回的完整性、失败项及 manifest 校验信息；部分文件失败就报告部分交付。画布下载不覆盖已有文件，冲突时换一个新的目录，不能悄悄用节点后来选中的产物替代本次运行结果。

## 7. 分镜脚本完整流程

Script 是可读写的结构化创作内容，不只是一个长提示词。典型顺序是：**保存故事与片段 → 准备锚点 → 运行并核对锚点 → 准备视频提示词 → 视频预检 → 保存生成组 → 运行指定组 → 采用和下载结果。**

### 7.1 先查询字段和完整示例

```bash
lightx2v workflow script schema --json
lightx2v workflow script schema --section anchors --json
lightx2v workflow script schema --section shots --json
lightx2v workflow script schema --field shots.dialogue.speaker_id --json
lightx2v workflow script examples --json
lightx2v workflow script guide --topic workflow --json
lightx2v workflow script guide --topic anchor-prompts --json
```

这些查询不需要先创建画布，但仍需要配置身份和服务准入。schema 默认返回目录，section / field 返回更具体定义。公共动作请求结构通过 `schema --action ACTION` 查询；具体例子从 examples 目录选择，不猜字段。

### 7.2 保存脚本草案

```bash
lightx2v workflow script examples --case create-script --json
lightx2v workflow script examples --case create-script --payload-only > create-script.json
```

先阅读示例的 `replace` 说明，再编辑文件：改为自己的故事、当前画布 `version`、角色和镜头。示例文件不是一条可以不检查就运行的生产请求。

```bash
lightx2v workflow edit --input @create-script.json \
  --operation-id script-create-001 --json
```

成功回执中的 `script_documents` 提供保存的节点和修订信息。后续使用真实 `SCRIPT_NODE_ID` 与 `SCRIPT_REVISION`。

写作规则：角色描述要包含明确身份、外貌、服装、构图与光线；场景描述明确空间关系；视觉变体用 `variant_of` 继承身份并写出造型变化。声音提示词既写声音特点，也写实际试听台词；变体声音按规范继承或显式覆盖。一个 shot 对应一个生成视频片段，片段内的镜头变化写入画面和运镜，不把每次切镜都误写成独立视频单元。

### 7.3 分页读取、修改镜头和对白

```bash
lightx2v workflow script read SCRIPT_NODE_ID --json
lightx2v workflow script read SCRIPT_NODE_ID --section shots --view detail \
  --revision SCRIPT_REVISION --offset 0 --limit 20 --json
lightx2v workflow script read SCRIPT_NODE_ID --section anchors --view detail --json
lightx2v workflow script read SCRIPT_NODE_ID --section shots --id s1 --view detail --json
```

稳定 ID 用于定位，名字用于阅读；后续分页固定同一 `revision`，避免翻页过程中混入新版本。`subjects`、`outputs`、`media_sources`、`production` 等读取区段用于核对主体、产物来源及生产登记。

局部修改的 `edit-shot.json` 示例，替换节点、修订和真实 shot ID：

```json
{
  "node_id":"SCRIPT_NODE_ID",
  "expected_revision":"SCRIPT_REVISION",
  "operations":[
    {"op":"update","collection":"shots","id":"s1","patch":{"duration_seconds":8}}
  ]
}
```

```bash
lightx2v workflow script schema --action edit --json
lightx2v workflow script edit --input @edit-shot.json \
  --operation-id shot-edit-001 --json
```

未修改的顶层字段保留；对白列表等整体值如何替换以当前 schema 为准。改对白可查询 `examples --case edit-dialogue`，说话人用真实锚点 ID。改完重新读取并使用新的修订，不能一直沿用旧 `SCRIPT_REVISION`。

### 7.4 准备、生成与同步锚点

```bash
lightx2v workflow script schema --action prepare-anchors --json
lightx2v workflow script examples --case prepare-anchors --json
lightx2v workflow script examples --case prepare-anchors --payload-only > anchors.json
```

按示例替换节点、最新修订、目标锚点与模型设置；模型和参数查实时 capabilities。然后保存锚点生成节点：

```bash
lightx2v workflow script prepare-anchors --input @anchors.json \
  --operation-id anchors-prepare-001 --json
```

**prepare-anchors 只保存，不启动图片或音频生成。** 读取回执中的真实生成组和节点；需要生成时，先估价，确认后按第 6.6 节运行指定范围。不要因为角色已有可复用素材就重复生成。

结果完成后，对账绑定已有产物：

```bash
lightx2v workflow script sync-anchors \
  --input '{"node_id":"SCRIPT_NODE_ID"}' \
  --operation-id anchors-sync-001 --json
lightx2v workflow operation get anchors-sync-001 --kind sync --json
```

同一 sync ID 重放的是同一次对账；之后产生新结果，要用新的 sync ID 发起新一轮观察。`pending` 表示仍待对账，不能强行当成锚点已准备好。

### 7.5 视频提示词：查询、生成候选和保存

```bash
lightx2v workflow script schema --action prompts --json
lightx2v workflow script examples --case prompts --json
```

先用 `mode=options` 查询适用模型，例如将下面内容保存为 `prompt-options.json`：

```json
{"node_id":"SCRIPT_NODE_ID","revision":"SCRIPT_REVISION","mode":"options","target":"video"}
```

```bash
lightx2v workflow script prompts --input @prompt-options.json --json
```

`compose` 用于确定性组合；`optimize` 会请求 AI 优化，需要按服务要求选择带 preset 的 `generation_model`。它虽然不会启动视频生成，但不是纯查询；是否涉及模型调用及费用以当前服务为准，不能一概写成免费。

多片段可用 `shot_ids` 一次请求候选，共用同一修订；检查全部 candidates 后，按 `schema --action edit` 的 `adopt_prompt` 规则一次保存，不逐镜头反复读写造成修订冲突。候选返回不等于已保存，也不等于视频已生成。

公共批量视频使用 `shot.video_prompt`，或请求里显式指定的 `target.prompt`；不要依赖旧字段 `image_to_video_prompt`。

### 7.6 预检、创建视频编组与运行

先获取示例并替换真实值：

```bash
lightx2v workflow script examples --case preview-video --payload-only > preview.json
lightx2v workflow script preview --input @preview.json --json
```

检查 `shots`、`issues`、`issue_help`、`needs_review`、`too_large`，以及每个片段解析出的提示词和锚点素材顺序。缺素材、引用错误或内容过大时先修正，不把预检问题留给计费任务。

```bash
lightx2v workflow script examples --case create-group --payload-only > create-group.json
```

将**同一次预检**的输入复制到建组文件，并填入原返回的 `preview_digest` 和 `shot_digests`（建组字段名是 `preview_shots`）。不能用空对象替代，也不能换了修订和参数还使用旧 digest。

```bash
lightx2v workflow script create-group --input @create-group.json \
  --operation-id video-group-001 --json
```

这一步仅保存节点、连接和编组。拿到真实组 ID 后，先 `workflow quote --group-id`，确认范围和费用，再 `workflow run --group-id`。等待、下载使用该次真实 RUN_ID。

### 7.7 采用指定产物

```bash
lightx2v workflow script read SCRIPT_NODE_ID --section outputs --view detail --json
lightx2v workflow script examples --case select-output --json
lightx2v workflow script examples --case select-output --payload-only > selection.json
```

从 outputs 选择真实单元、准确 ref、来源节点、运行、端口及输出序号，更新 `expected_revision`，再提交：

```bash
lightx2v workflow script select-output --input @selection.json \
  --operation-id select-output-001 --json
```

`selection: null` 用于取消选定。不要默认选择“最新结果”就是本次要采用的结果；重试后尤其要核对来源。

## 8. 可以直接交给 Agent 的六类案例

以下是**发送给 Agent 的需求模板**。先补充自己的素材路径、项目与预算，再使用；不是终端命令，也不是自动授权无限重试。

### 8.1 产品广告：参考图到多片段

> 素材：产品图路径 PRODUCT_IMAGE，可选参考视频 REFERENCE_VIDEO。目标：制作约 15 秒、9:16 的产品广告。先读参考与模型能力，列出卖点、分镜和所需参考，创建“产品广告”画布并保存方案，不先提交生成。产品外观和标识保持一致，不编造功效。向我确认分镜和估价后，只运行确认的节点。交付画布链接、各片段文件、模型参数、任务/运行 ID 和失败清单。如需剪辑成片，先说明可用剪辑工具，不能把片段当作成片交付。

### 8.2 连续短剧：脚本、锚点到镜头

> 素材：故事或剧本 SCRIPT_FILE，角色/场景参考 REFERENCE_FILES。目标：先完成一段约 60 秒的连续短剧方案。使用结构化 Script 保存角色、场景、服装变体、对白和视频片段，写清每段起止状态与衔接。已有参考足够时复用，不重复生成。先交付分镜和锚点方案让我确认；随后分阶段估价与生成，先锚点后视频。保持人物、声音和空间连续，失败只处理受影响片段。交付画布、脚本、逐段视频及明确的未完成项，合成成片需另行核对工具能力。

### 8.3 多参考角色视频：身份和顺序一致

> 素材：角色 A 图 IMAGE_A、角色 B 图 IMAGE_B、场景图 SCENE_IMAGE，以及可选声音 AUDIO_A/AUDIO_B。目标：制作一段模型支持时长的双人对话视频。先检查模型支持的参考种类与数量，给每张图和每段声音建立明确角色映射。把映射、人物站位、台词和镜头动作保存到画布；预检参考顺序和说话人，给我确认后再生成。交付对应运行的视频、参数、参考映射与一致性检查结果。

### 8.4 角色声音制作：先试听，再复用

> 素材：角色描述 CHARACTER_BRIEF，可选有权使用的声音样本 VOICE_SAMPLE。目标：为角色建立可复用声音。先比较当前可用的内置 TTS、音色克隆或音频生成路径，说明选择理由。试听只朗读“今天，我们从这里出发。”，不要背景音乐。先保存方案并说明是否涉及生成，确认后提交一次试听；交付音频、可复用音色/节点 ID、台词与参数。已有合格试听直接复用，不批量重做。

### 8.5 已有画布修改：保留有效内容

> 目标画布：WORKFLOW_ID。请先读取节点、尺寸、编组、连接和已有结果，概述当前结构。仅整理布局和命名，把参考素材与生成节点分区，保留原提示词、素材顺序、有效连接与产物。若需要转移编组成员，依据最新组关系处理。不要运行生成、取消任务或删除内容。完成后重新读取验证，并交付修改摘要和画布链接。

### 8.6 批量交付：按运行核对文件

> 目标画布：WORKFLOW_ID，范围：GROUP_ID 或明确节点列表，输出目录 OUTPUT_DIR，预算上限由我补充。先检查输入完整性并给出同范围估价；估价不完整时说明未知部分，不自动提交。确认后为每次运行保存 operation_id、run_id 和原始参数。断线先查询原操作，超时继续等待原运行；任何新生成或恢复执行均应在已授权范围内。按确切 run 下载，生成可核对的文件清单、失败原因与恢复建议，不覆盖已有交付。

## 9. 积分、状态和异常恢复

### 9.1 哪些操作会执行生成

| 操作 | 是否启动媒体生成 | 说明 |
| --- | --- | --- |
| 查询 models / doctor / capabilities / schema / guide / examples | 否 | 获取当前能力和规范 |
| 创建或编辑节点、连接、编组、脚本 | 否 | 保存内容，不等于运行 |
| 上传、prepare-anchors、sync-anchors、preview、create-group、select-output | 否 | 可能保存或采用已有内容；不自动生成媒体 |
| Script prompts 的 options / compose | 否 | 查询选项或确定性组合 |
| Script prompts 的 optimize | 不生成视频，但会请求 AI 优化 | 不应当作纯只读查询或保证免费 |
| workflow quote | 否 | 独立估价，不是运行授权 |
| run / workflow run / tts / voice-clone create、tts / resume | 可能执行或恢复模型任务 | 按服务和当前账户规则计费 |

`run --quote` 会先报价、然后直接提交，**不是“只报价”模式，也不提供人工确认暂停**。要求先看费用再决定时，优先使用画布的独立 quote / run 两步流程；直接素材接口的独立报价见 API 文档，当前 CLI 没有对应顶层只报价命令。

画布 `quote` 的 `complete: false` 表示估价不完整，不代表未估出的部分免费。实际积分、失败/取消是否扣费或返还，以服务回执和账户账单为准，不照搬其他平台价格，也不保证所有模型退费规则一致。

### 9.2 分清这些 ID 和状态

| 标识 | 代表什么 | 用在哪里 |
| --- | --- | --- |
| task_id | 直接素材任务 | query / result / cancel / resume |
| workflow_id | 一张画布 | workflow get / use |
| node_id、group_id | 画布中的节点、编组 | 编辑、确定运行和下载范围 |
| operation_id | 一次公共写操作的请求身份 | 恢复创建、编辑、上传、运行等操作 |
| run_id | 一次画布运行 | status / wait / outputs / download |
| version / revision | 画布版本 / Script 修订 | 防止基于过时状态覆盖内容 |

`accepted` 只说明运行已受理，`saved` 只说明内容保存。直接素材任务常见状态为 `RUNNING`、`SUCCEED`、`FAILED`、`CANCEL`；画布运行采用其自身状态结构，不要大小写转换后混着判断。恢复身份和阶段以实际回执为准。

### 9.3 超时或断线后怎么做

**直接素材任务：**

```bash
lightx2v query TASK_ID --json
lightx2v result TASK_ID -o ./output/recovered.png
```

只有成功后才下载。没拿到 task_id 就失去连接时，先查任务列表和提交时间；不要假设直接 `run` 具有公共画布 operation_id 的幂等保证。

**画布写操作结果未知：**

```bash
lightx2v workflow operation get WORKFLOW_ID run-node-001 --kind run --json
```

有 run_id 后继续查询该运行。查询不到时保留原请求日志，按恢复提示重发**相同 operation_id 和相同载荷**。不能换 ID、变更版本或“顺便修改”参数，否则可能产生另一项操作。

确定被拒绝的版本冲突、组成员冲突或文本锚点冲突，先读取最新状态，再有意识地构造新的修改及新 ID；不要把“明确失败后的新意图”和“结果未知的原请求重放”混为一谈。

**画布运行等待超时：**

```bash
lightx2v workflow wait WORKFLOW_ID RUN_ID --until outputs --timeout 600 --json
```

停止本地等待或按 Ctrl-C 不等于取消服务端运行。确实要取消时，明确执行 `workflow cancel WORKFLOW_ID RUN_ID`；只取消一个节点及相关下游时使用 `workflow cancel-node WORKFLOW_ID RUN_ID NODE_ID`，随后核对状态。

### 9.4 退出码和 JSON

| 命令范围 | 退出码 | 含义 |
| --- | --- | --- |
| 公共画布命令 | 0 | 本次命令完成；仍需按返回字段区分已保存、已受理、运行完成 |
| 公共画布命令 | 1 | 确定失败、服务拒绝或下载部分失败等，读取错误内容 |
| 公共画布命令 | 2 | 参数、配置、本地文件等问题 |
| 公共画布等待 | 3 | 本地等待超时，服务端可能仍在运行 |
| 公共画布写操作 | 4 | 结果未知，保留原 ID 和原载荷进行恢复 |
| 公共画布观察 | 130 | 本地被中断，不代表服务端已取消 |
| login --resume | 3 | 授权仍在等待，应按 retry_after 续查 |
| 直接素材等其他命令 | 以各命令实现为准 | 直接 run 等失败/等待超时通常返回 1，不套用公共画布的 3/4 规则 |

Agent / 自动化建议使用 `--json`，并分别保留 stdout 与 stderr。公共画布通常输出一个 JSON 对象，恢复文件和操作身份可写到 stderr；直接素材 `run --json` 是多行事件流，不能直接假设整个文件是一个 JSON 对象。

```bash
lightx2v workflow wait WORKFLOW_ID RUN_ID --until outputs --json \
  > wait.json 2> wait.stderr
```

脚本应检查退出码和 JSON 内的成功、完整性及状态字段；不能仅用“进程退出 0”判断视频已经生成。

### 9.5 本地配置与恢复文件

| 位置 | 内容 | 处理原则 |
| --- | --- | --- |
| `~/.config/lightx2v/config.json` | 服务地址与凭证 | 不提交 Git，不粘贴到聊天 |
| 项目 `.lightx2v/project.json` | 当前服务、账户与画布上下文 | 切换服务或账户后重新 use |
| 项目 `.lightx2v/operations/` | 公共操作原请求、身份及回执 | 结果未知时保留，恢复前不要删除 |
| 项目 `.lightx2v/text-contexts/`、`text-client.json` | 文本协作上下文 | 不是可任意复用到其他账户的模板 |
| 你指定的 output / delivery 目录 | 已下载产物及交付清单 | 下载后检查可读性与对应运行 |

CLI 从当前目录向父目录寻找已有 `.lightx2v/project.json`；不同项目应使用明确独立的工作目录，避免误操作父目录绑定的画布。日志和操作记录也可能包含提示词、文件信息及私有素材引用，分享故障材料前先去除敏感内容。

## 10. 常见问题与命令速查

### 10.1 常见问题

**不会命令行，可以用吗？** 可以把第 2.1 节发给有终端能力的 Agent。你仍需要完成账户授权、提供素材，并检查分镜与生成结果。CLI 本身不代替 Agent 的创作和判断。

**command not found？** 先检查 Python / pipx 安装是否成功，重开终端或激活安装使用的虚拟环境。Bash / zsh 可用 `command -v lightx2v` 检查实际入口；不要安装多份后靠重复运行碰运气。

**安装成功却没有新版命令？** 检查 `--version` 与 `--help`。安装源还没发布新版时，反复 update 不会得到开发工作树的命令；服务过旧也会导致协议不可用。需要同时核对客户端与服务。

**网页登录了，CLI 仍提示未授权？** 网页登录与 CLI 授权不是同一状态。重新完成 login，检查服务地址和环境变量覆盖。凭证过期或已撤销时重新授权；不要把浏览器 Cookie 当 API Key。

**doctor 可调用但仍不能创建画布？** 检查启用状态、账户准入、新操作准入与 Canvas 权益，不只看 `supported: true`。

**参数明明在旧教程里，为什么不支持？** 查当前 models、capabilities 和 schema，区分模型显示名、model_cls 与工具 ID；画幅、尺寸、分辨率档位和时长是不同参数。

**显示“提交成功”，为什么还没有结果？** 提交、排队、执行、产物可用、下载完成是不同阶段。用原任务或运行 ID 继续观察；只提交成功不应宣布交付。

**任务失败是不是一定不扣积分？** 不能统一保证。先看失败阶段、服务回执与账单；取消和恢复也不是固定免费操作。

**Agent 总是换个 ID 重试？** 让它保留 operation_id、请求载荷和恢复文件。公共写操作结果未知时只查询或原样重放；确定冲突后才基于最新状态建立新的编辑意图。

**音频或视频下载地址过期了？** 重新通过该任务的 result，或确切画布 run 的 outputs / download 获取当前可用结果。不要更换成其他任务的文件，也不要把平台 Key 附加到 CDN 地址。

**Script 建组后为什么没有生成？** prepare-anchors / create-group 只保存生成节点。读取组 ID 后，需要另行估价并运行。

**如何退出或撤销授权？** 当前 CLI 没有 `logout` 命令。到网站 API Key 管理撤销对应凭证；需要清理本地配置时明确操作该配置，不要删除尚需恢复的项目操作日志。

**怎么反馈问题？** 附 CLI 版本、系统、服务地址、脱敏后的命令、错误码、相关 task_id / workflow_id / run_id / operation_id，以及预期与实际结果。不要附 API Key、授权 device_code 或完整私有素材。

### 10.2 完整命令索引

| 命令 | 用途 |
| --- | --- |
| `--version` / `--help` | 版本与帮助 |
| `login` | 浏览器授权、headless / resume、手动 Key |
| `models` | 任务模型目录 |
| `run` | 直接提交、等待和下载素材 |
| `query` / `list` / `result` | 查单任务、任务列表、获取结果 |
| `cancel` / `resume` / `delete` | 取消、恢复执行、删除已结束记录 |
| `voices` / `tts` | 内置音色查询与台词合成 |
| `voice-clone create / save / list / tts / delete` | 克隆音色与管理 |
| `doctor` | 公共画布协议与账户就绪检查 |
| `workflow list / get / inputs` | 列出、读取画布、查看运行输入 |
| `workflow create / use / rename / delete` | 创建、选择、改名、删除画布 |
| `workflow capabilities / nodes` | 查能力与搜索节点 |
| `workflow upload / edit` | 上传素材、批量编辑 |
| `workflow node create / update / move / copy / delete / get` | 节点操作 |
| `workflow connect / disconnect / reorder-inputs` | 连线与参考顺序 |
| `workflow group list / get / create / update / add / remove` | 编组读取和成员维护 |
| `workflow group move / set-parent / ungroup / copy` | 转移成员、父组、解除和复制 |
| `workflow text get / edit` | 协作读取和编辑提示词或文档 |
| `workflow quote / run` | 独立估价与正式运行 |
| `workflow runs / status / stream / outputs / wait` | 运行列表、状态、事件、结果和等待 |
| `workflow cancel / cancel-node` | 取消运行或节点及相关下游 |
| `workflow operation get` | 恢复查询操作回执 |
| `workflow download` | 按确切运行下载与打包 |
| `workflow script schema / examples / guide / read` | Script 规范、示例、指南和内容 |
| `workflow script edit / prepare-anchors / sync-anchors` | 修改记录、准备和同步锚点 |
| `workflow script prompts / preview / create-group / select-output` | 提示词候选、预检、建组、采用产物 |
| `update` / `completion bash或zsh` | 更新和 Shell 补全 |

所有层级均可加 `--help` 查看准确参数，例如 `lightx2v workflow group set-parent --help`。不要假设 `--json`、`--base-url` 等参数是可放在任意位置的全局参数；按对应子命令帮助使用。

### 10.3 Shell 补全

Bash：

```bash
eval "$(lightx2v completion bash)"
```

zsh：

```bash
eval "$(lightx2v completion zsh)"
```

当前补全脚本可能只覆盖部分命令，准确命令与参数仍以 `--help` 为准。

### 10.4 本版核验范围与后续更新

本教程依据 0.3.3 开发代码、真实命令帮助，以及兼容开发服务的 doctor、模型目录、画布读取、capabilities、Script schema / examples 查询编写。文中生成、克隆、取消与恢复执行示例本轮未新增计费实跑；不把“参数解析通过”当作真实生成成功。

当前公网公共画布入口尚未就绪，官方主分支安装来源也尚未包含全部新版功能；正式上线前需完成新版发布、公开入口干净安装、目标服务授权及非生成流程复验。Windows 实机和所有模型组合尚未验证。

GitHub 中文教程与飞书教程维护同一份章节和命令内容；后续 CLI 命令、参数、默认行为、安装授权、计费或异常恢复变化，应同时更新两处，记录版本、修订和更新时间。同步未成功时明确报告，不能只改一处就宣布完成。

开源许可证：MIT。英文入口与更多安装说明见 [CLI 仓库](https://github.com/ModelTC/lightx2v-studio-cli)。
