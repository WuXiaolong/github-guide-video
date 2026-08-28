# github-guide-video · GitHub 仓库推荐视频生成器

你只需要丢一个 GitHub 链接过来，等几分钟，就能拿到一支**带口播配音和背景音乐的 30 秒以内推荐视频**（1080p MP4），画面和配音逐句对齐，适合发朋友圈、B 站、X/Twitter 或者给项目 README 当宣传素材。

## 它能做什么

一句话：**你给仓库链接，它还你一支口播推荐视频。**

- 🎬 画面用 [HyperFrames](https://hyperframes.heygen.com) 渲染——所谓"写 HTML 就能出视频"，自动为你的仓库设计开场、卖点、数据、结尾四幕画面
- 🎙️ 口播用微软 Edge TTS 生成，默认是"云希"阳光男声，也可以换温柔女声、沉稳男声等 6 种声线
- 🎵 自动配背景音乐，且**音乐音量严格是口播的一半**，不会盖住人声
- ✅ 每次成片都自动做"音画同步体检"：口播有没有跟上画面、音乐比例对不对、画面有没有坏帧

## 安装（一次就好）

技能仓库地址：**https://github.com/WuXiaolong/github-guide-video**

对 Agent 直接说：`帮我安装下 https://github.com/WuXiaolong/github-guide-video 这个skill`。

或者在终端里执行一条命令，把仓库克隆到如千问办公的技能目录即可：

**macOS / Linux：**

```bash
git clone https://github.com/WuXiaolong/github-guide-video.git ~/.qwenworkcn/skills/github-guide-video
```

**Windows（PowerShell）：**

```powershell
git clone https://github.com/WuXiaolong/github-guide-video.git "$env:USERPROFILE\.qwenworkcn\skills\github-guide-video"
```

装完后**重启一下千问办公**（新开会话也行），让技能被加载。之后在技能列表里就能看到它了。

> 国内网络如果克隆慢，可以走镜像：`git clone https://ghproxy.net/https://github.com/WuXiaolong/github-guide-video.git ~/.qwenworkcn/skills/github-guide-video`
>
> 没装 git 的话，也可以打开仓库页面点 **Code → Download ZIP**，解压后把 `github-guide-video` 文件夹整个放进 `~/.qwenworkcn/skills/` 目录（Windows 是 `C:\Users\你的用户名\.qwenworkcn\skills\`），效果一样。

更新时重新执行一次克隆命令覆盖即可（或者 `git -C ~/.qwenworkcn/skills/github-guide-video pull`）。

## 怎么用（真的很简单）

**最简用法**——一句话：

```
用 github-guide-video 给 https://github.com/xxx/yyy 做个推荐视频
```

然后等 6-8 分钟就好。期间不需要你做任何事。

**想指定配音**：

```
--voice 温柔女声
```

可选声线：阳光男声（默认）、温柔女声、沉稳男声、磁性深沉、元气少女、英文（en-US 男/女声）。

**想用自己的背景音乐**：

```
--bgm /path/to/你的音乐.mp3
```

不指定的话，会自动用技能自带的 bgm-source.mp3。

## 你会拿到什么

一支 `.mp4` 文件（1920×1080，30fps，30 秒以内），典型结构：

| 时间 | 画面 | 旁白在说什么 |
|---|---|---|
| 开场 | 痛点提问，比如"还在手搓 XX 吗？" | 抓住观众注意力 |
| 中段 | 产品名 + 核心卖点/数据卡片 | 这个仓库是什么、强在哪 |
| 结尾 | 安装命令 + 仓库地址 | 怎么用，去哪里找 |

## 背后发生了什么（不用记，仅供好奇）

你不用懂这些，工具会全自动完成——但如果你想了解它为什么可靠：

1. **抓资料**：读取仓库的 README，提炼最有说服力的 3 个数字和 1 条命令（视频只有 30 秒，装不下更多）
2. **先写稿再配图**：先生成每一段配音，用配音的真实时长来决定画面节奏——保证"念到哪，画面演到哪"
3. **配音生成**：分幕调用 Edge TTS，网络不好会自动重试
4. **混音**：背景音乐先做响度对齐，再压到口播一半的音量（直接减半音量会让音乐盖过人声，这是踩过坑的）
5. **渲染 + 体检**：浏览器逐帧渲染成 MP4，随后自动检查画面坏帧、音乐全程存在、音量比例正确，全部通过才交付

## 常见问题

**Q：需要我先装什么吗？**
一般不用。技能会自动检查 Node.js 22+、FFmpeg、HyperFrames CLI、Edge TTS，缺什么会提示你装一句命令的事。

**Q：为什么渲染要几分钟？**
视频是浏览器逐帧"拍"出来的（30 秒视频约 900 帧），这是保证画面精确同步的代价。已经做过一轮深度优化（曾需 20+ 分钟，现在 6-8 分钟）。

**Q：出来的文案不满意？**
直接说，比如"第二句改成 XXX""数据换成 star 数"，改完自动重新渲染，几分钟就好。

**Q：支持英文仓库吗？**
支持。仓库内容是英文也能做成中文口播；想整支英文口播就加 `--voice english`。

## 文件说明（面向开发者/贡献者）

```
github-guide-video/
├── SKILL.md              # 核心指令：给 AI 执行者的完整工作流程（8 步）
├── reference.md          # 进阶参考：编写契约、音画同步公式、踩坑记录
├── .skill-metadata.yaml  # 推荐查询（中英双语）
├── assets/
│   ├── bgm-source.mp3    # 默认背景音乐素材
│   └── project-template/ # 缓存的空白项目模板（免去网络初始化）
└── scripts/
    ├── make_vo.sh        # TTS 生成：自动重试 + 裁静音 + 输出精确时长
    └── verify_render.py  # 成片体检：黑边/静音/音量比/关键帧，单遍解码
```
