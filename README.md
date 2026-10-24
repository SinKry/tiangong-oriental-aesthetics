# 天宫东方美学

面向东方神话、云海天宫、神龙、仙山、空中龙宫与天塔等题材的提示词技能。根据主题、图片或视频，创作或倒推具有宏大史诗感、氛围感与视觉张力的生图和视频提示词。

这是完整原版技能，包含独立参考指南与视频提帧助手。

## 能做什么

- **输入主题词**：默认提供5组差异化生图提示词，并配套视频建议和视频提示词。
- **上传图片**：分析主题、构图、尺度、材质与光影，倒推生图提示词，并设计适合画面的动态。
- **上传视频**：提取关键帧、复核镜头边界，逐段返回时间范围、生图提示词和视频提示词。
- **提供轨迹图**：解读实际路线，设计第一人称穿越，明确干净画面与路径标注的不同用途。

技能默认输出提示词，不会自行调用图片或视频生成服务。

## 创作方法

生图采用 **奇观主视觉 + 超常尺度 + 强构图 + 光色层次**。

光影描述包含光源方向、受光与遮挡、材质响应、云雾散射和远近层次。配色、时段、构图与奇观主体随主题变化，不固定为金色夕阳或凤凰宫殿。

视频根据画面条件选择轨迹图引导、第一人称飞跃或宏大场景展示，并综合安排运镜、场景动态、人物动作和光影变化。

**默认世界是天空与云海。** 即使输入“龙宫”或“月下龙宫”，也默认创作为云海之上的龙宫。只有明确指定海底、水下、海面等环境时才切换；图片和视频逆向则忠实还原参考素材。

## 在 Codex 中使用

把仓库克隆到本地技能目录，保留 `SKILL.md` 与参考文件的相对位置。

Windows PowerShell：

```powershell
git clone https://github.com/SinKry/tiangong-oriental-aesthetics.git "$env:USERPROFILE/.codex/skills/tiangong-oriental-aesthetics"
```

macOS / Linux：

```bash
git clone https://github.com/SinKry/tiangong-oriental-aesthetics.git ~/.codex/skills/tiangong-oriental-aesthetics
```

若已存在同名技能，请先检查现有内容再更新。自定义了 `CODEX_HOME` 时，使用该目录下的 `skills` 文件夹。

调用示例：

```text
使用 $tiangong-oriental-aesthetics，主题：月下龙宫。

使用天宫东方美学，分析我上传的图片，给出生图还原提示词和最适合的视频运镜提示词。

使用天宫东方美学，拆分这段拼接视频，返回每个镜头的关键帧、时间范围及配套提示词。

根据这张轨迹图设计第一人称云海天宫飞行，标注图只指导路径，成片不要保留标记。
```

## 文件结构

```text
SKILL.md                       技能入口与工作流程
agents/openai.yaml             显示名称与默认调用提示
references/image-prompts.md    生图公式与光色方法
references/video-prompts.md    三种视频模式与路线处理
references/video-analysis.md   视频提帧、分镜及逐段逆向
scripts/inspect_video.py       视频证据提取助手
```

## 可选的视频提帧助手

提示词创作本身不依赖额外程序。使用提帧助手时，需要 Python 3.10 或以上版本，以及 PATH 中可用的 `ffmpeg` 和 `ffprobe`；无需额外 Python 图像库。

```bash
python scripts/inspect_video.py "video.mp4" --output "video-analysis"
```

输出逐帧图片、接触表和 `manifest.json` 时间清单。输出目录必须是新目录，原视频保持不变。

```bash
python scripts/inspect_video.py "video.mp4" --start 12 --end 16 --interval 0.2 --output "video-analysis-detail"
```

自动场景变化检测只提供候选，切镜和运动方向需要进一步视觉核对。轨迹图提示词也不能保证生成模型精确走线或彻底去除首帧批注，优先提供干净外观图与独立路径参考图。
