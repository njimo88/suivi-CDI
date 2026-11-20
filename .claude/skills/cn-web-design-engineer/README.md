# 网页设计工程师 Skill

**一个能将 AI 生成的网页从"能用"提升到"惊艳"的 AI Agent 技能。**

[中文文档](./README.zh-CN.md) · [Back to collection root](../../README.md)

![Web Design Skill](https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design-skill.webp)

---

## 这是什么？

这是一个可复用的 **Skill**（结构化系统提示），面向支持 `SKILL.md` 格式的 AI 编程 Agent——例如 [Claude Code](https://docs.anthropic.com/en/docs/claude-code)、[Cursor](https://cursor.com) 等——能显著提升 AI 生成的 HTML/CSS/JavaScript 作品的设计质量。

它将 [Claude Design](https://www.anthropic.com/news/claude-design-anthropic-labs) 系统提示中的核心设计理念，提炼为一个开放、可移植、可定制的技能文件，可即插即用到任意项目中。

### 问题

现代 LLM 已经能从简单提示生成可用的网页。但它们的输出往往会收敛到同一种审美：Inter 字体、蓝色主按钮、紫粉渐变、大圆角卡片、用 emoji 当图标、编造的用户评价。技术上没错，视觉上却千篇一律。

### 解决方案

这个技能通过以下方式，将 **设计品味** 注入 AI 的决策过程：

- **反陈词滥调规则**——一份明确的、被过度使用的 AI 设计模式黑名单
- **设计体系声明**——强制 AI 在写代码*之前*阐明色彩、字体、间距与动效的选择
- **oklch 色彩理论**——基于感知一致性的色彩派生，而非随机猜测 hex
- **精选字体与配色组合**——高质量起点，取代默认的 Inter + #3b82f6
- **占位符哲学**——诚实的 `[icon]` 标记，而非画得很差的山寨 SVG
- **五旋钮设计研判（Design Read）**——将受众、作品、品牌与约束，转化为可见的变化度 / 动效 / 密度 / 素材 / 保真度决策
- **保留感知的改版**——在触碰已有产品前，先区分扩展、保留与重塑三种模式
- **语境化失败模式**——识别反复出现的布局、内容、图像、动效与仪表盘失败，而不会把品味变成一刀切的禁令
- **结构化工作流**——需求 → 背景 → 已校准的设计体系 → v0 草稿 → 完整构建 → 验收核查
- **按需浏览器验收**——仅在用户明确要求验收或浏览器测试时，才运行可执行的响应式 / 交互 / 运行时 QA

---

## 快速开始

### 面向 Claude Code / Cursor / AI Agent

将这个技能文件夹复制到你的项目中：

```
your-project/
├── .agents/skills/web-design-engineer/   # or .claude/skills/web-design-engineer/
│   ├── SKILL.md                          # 主技能文件
│   └── references/
│       ├── advanced-patterns.md          # 代码模板库（幻灯片引擎、设备边框、动效时间轴、数据可视化）
│       ├── block-library.md               # 已实现可复用模块的索引
│       ├── browser-acceptance.md          # 仅在明确要求时才运行的可执行浏览器 QA 框架
│       ├── design-calibration.md          # 设计研判 + 五个旋钮 + 可选的图片优先分支
│       ├── design-directions.md          # 设计方向顾问（6 大流派，差异化的 3 选推荐）
│       ├── failure-patterns.md            # 语境化的 AI 设计失败分类与修复
│       ├── redesign-protocol.md          # Extension / Preserve / Overhaul 审查与受保护契约
│       ├── style-recipes/                # 25 个带锚点的风格配方——每个锚点一个 .md 文件，按需加载
│       │   ├── INDEX.md                   #   目录索引 + 3 个交叉索引 + 跨流派反模式
│       │   ├── linear.md / aesop.md / pentagram.md / ...    #   25 个单配方文件
│       └── critique-guide.md             # 5 维度评分标准 + 常见问题清单
└── ...
```

或从集合根目录使用 Claude Code 插件市场——见 [顶层 README](../../README.md#install)。

当你的请求涉及可视化 / 交互前端工作时，Agent 会自动加载该技能。

### 涵盖范围

| 输出类型 | 示例 |
|---|---|
| 网页与落地页 | 营销站点、产品页、作品集 |
| 交互原型 | 带设备边框的可点击应用样机 |
| 幻灯片 | HTML 演示文稿（1920×1080，键盘导航） |
| 数据可视化 | 使用 Chart.js 或 D3.js 的仪表盘 |
| 动画 | CSS/JS 动效设计、时间轴驱动的演示 |
| 设计体系 | 令牌探索、组件变体 |

---

## 工作原理

### 已校准的工作流

```
1. 理解需求        →  仅在信息不足时才提问
2. 收集设计背景    →  代码 > 截图；归类已有作品的改版模式
3. 产出设计研判    →  五个旋钮将需求连接到可见的决策
4. 声明设计体系    →  色彩、字体、间距、动效——用 Markdown，在写代码之前
5. 尽早展示 v0 草稿 →  占位符 + 布局 + 令牌；让用户纠偏
6. 完整构建        →  组件、状态、动效；在关键决策点暂停
7. 验收核查        →  轻量自查；仅在明确要求时才运行浏览器框架
```

### 核心设计原则

**反 AI 陈词滥调清单。** 该技能明确禁止：

- 紫粉蓝渐变背景
- 左边框强调卡片
- Inter / Roboto / Arial / Fraunces / system-ui 字体
- 用 emoji 替代图标
- 编造的数据、虚假的 Logo 墙、占位感十足的推荐语

**oklch 色彩体系。** 颜色在感知一致的 oklch 空间中派生。相同的明度值在人眼看来*确实*是同样的亮度——不像 HSL，其中 50% 的黄看起来比 50% 的蓝亮得多。

**精选起点。** 六种预先验证、适用于常见场景的"色彩 × 字体"组合：

| 风格 | 色彩 | 字体 | 适用场景 |
|---|---|---|---|
| 现代科技 | 蓝紫 | Space Grotesk + Inter | SaaS、开发者工具 |
| 雅致编辑 | 暖棕 | Newsreader + Outfit | 内容、博客 |
| 高端品牌 | 近黑 | Sora + Plus Jakarta Sans | 奢侈品、金融 |
| 活泼消费 | 珊瑚色 | Plus Jakarta Sans + Outfit | 电商、社交 |
| 极简专业 | 蓝绿 | Outfit + Space Grotesk | 仪表盘、B2B |
| 匠人暖意 | 焦糖 | Caveat + Newsreader | 食品、教育 |

**带锚点的风格配方库（25 个具名配方，渐进式加载）。** 当用户点名某个锚点（"Linear 风格"、"Aesop 感觉"、"Pentagram 级排版"）时，Agent 只读取 `references/style-recipes/<anchor>.md` 中**与之对应的那一个文件**（约 50 行）。目录索引、3 个交叉索引与跨流派反模式，都位于 `references/style-recipes/INDEX.md`（约 150 行）。整份目录绝不会一次性加载。这 25 个配方分布在 7 个流派中（6 个方向顾问流派，外加一个只能通过直接锚点名访问的 *Specialty / Genre* 流派）：

| 流派 | 配方 |
|---|---|
| 编辑式 / 极简 | `apple-hig` · `muji-kenya-hara` · `aesop` · `dieter-rams-braun` · `monocle-magazine` |
| 信息架构 | `pentagram` · `vignelli-swiss-helvetica` · `bloomberg-terminal` · `tufte-dataink` · `nyt-the-daily` |
| 现代工具 / Builder SaaS | `linear` · `vercel-mesh` · `raycast` · `notion-pre-ai` |
| 动效 / 实验 | `field-io` · `active-theory` · `resn-storytelling` |
| 野兽派 / 原始 | `are-na` · `bloomberg-businessweek-turley` · `balenciaga-post-2017` |
| 温暖人文 | `mailchimp-freddie` · `stripe-press` · `headspace-meditation` |
| Specialty / Genre | `y2k-retrofuturism` · `mid-century-modern` |

---

## 风格配方画廊

该技能内置 **25 个具名配方**，每个都对应一个真实的品牌、工作室或设计师。每个配方在演示画廊中都有一件可运行的完整页面作品——不是共享模板，不是缩略图情绪板，而是该配方真正被设计成的形态：Aesop 的药妆产品页、Bloomberg Terminal 的交易工作站、Mid-Century 的 Saul Bass 海报、Retrofuturism 的 Y2K 门户。在下方按流派浏览，挑选调性与你的需求匹配的，或阅读 `references/style-recipes/<recipe>.md` 中的规格文件。点击任意预览图可打开 2:1 全分辨率画框。

> 画框是由实时的 React + Vite 画廊 [`demo/web-design-engineer-demo`](../../demo/web-design-engineer-demo/) 渲染出的真实作品——与配方规格使用相同的字体、相同的配色、相同的标志性手法。每个演示位于 `src/recipes/<id>.tsx`。

### 编辑式 / 极简 · 5 个配方

> 留白、考究的字体、安静的奢华——药妆店、博物馆图录、硬件产品页。

<table>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/apple-hig.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/apple-hig.webp" alt="apple-hig preview" /></a>
<br /><strong><code>apple-hig</code></strong>
<br /><sub>SF Pro Display、充裕留白、柔和浮起感——Apple Store 的腔调</sub>
<br /><sub><b>最佳场景</b> · 硬件产品页 · 设备发布 · 高端消费电子</sub>
</td>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/muji-kenya-hara.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/muji-kenya-hara.webp" alt="muji-kenya-hara preview" /></a>
<br /><strong><code>muji-kenya-hara</code></strong>
<br /><sub>以空为画布、灰烬与纸张、每件物品都悬于空气之中</sub>
<br /><sub><b>最佳场景</b> · 器物图录 · 家居品牌 · 慢生活门店</sub>
</td>
</tr>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/aesop.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/aesop.webp" alt="aesop preview" /></a>
<br /><strong><code>aesop</code></strong>
<br /><sub>暖麂皮色、鼠尾草与琥珀、读起来像文学杂志的衬线文案</sub>
<br /><sub><b>最佳场景</b> · 药妆产品页 · 美妆与健康 · 独立零售</sub>
</td>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/dieter-rams-braun.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/dieter-rams-braun.webp" alt="dieter-rams-braun preview" /></a>
<br /><strong><code>dieter-rams-braun</code></strong>
<br /><sub>十大原则、单色网格、技术正视图——形式即功能</sub>
<br /><sub><b>最佳场景</b> · 工业设计档案 · 硬件规格 · 品牌理念页</sub>
</td>
</tr>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/monocle-magazine.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/monocle-magazine.webp" alt="monocle-magazine preview" /></a>
<br /><strong><code>monocle-magazine</code></strong>
<br /><sub>世界主义简报、海军蓝与珊瑚色、带脚注的好奇心</sub>
<br /><sub><b>最佳场景</b> · 杂志目录 · 城市与旅行简报 · 生活方式刊物</sub>
</td>
<td align="center" width="50%" valign="middle">
<br />
<strong>当需求这样说时</strong>
<br /><sub>"精致" · "高端" · "安静" · "编辑感" · "少即是多"</sub>
<br /><br />
<sub>规格见 <a href="./references/style-recipes/">style-recipes/</a></sub>
<br /><br />
</td>
</tr>
</table>

### 信息架构 · 5 个配方

> 理性、数据驱动、克制——导视系统、终端界面、带脚注的随笔、记录报章。

<table>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/pentagram.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/pentagram.webp" alt="pentagram preview" /></a>
<br /><strong><code>pentagram</code></strong>
<br /><sub>以一款粗体字作为画面、网格为脚手架、只用墨与地</sub>
<br /><sub><b>最佳场景</b> · 视觉识别样张 · 字体主导的作品集 · 画廊公告</sub>
</td>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/vignelli-swiss-helvetica.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/vignelli-swiss-helvetica.webp" alt="vignelli-swiss-helvetica preview" /></a>
<br /><strong><code>vignelli-swiss-helvetica</code></strong>
<br /><sub>每个字号都用 Helvetica、六原色、纽约地铁线路图</sub>
<br /><sub><b>最佳场景</b> · 导视与交通 · 公共信息海报 · 品牌体系样张</sub>
</td>
</tr>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/bloomberg-terminal.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/bloomberg-terminal.webp" alt="bloomberg-terminal preview" /></a>
<br /><strong><code>bloomberg-terminal</code></strong>
<br /><sub>海军黑底上的琥珀色、处处等宽字体、密度优先于舒适</sub>
<br /><sub><b>最佳场景</b> · 交易仪表盘 · 运维控制台 · 重度用户的密集型工具</sub>
</td>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/tufte-dataink.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/tufte-dataink.webp" alt="tufte-dataink preview" /></a>
<br /><strong><code>tufte-dataink</code></strong>
<br /><sub>正文里嵌迷你火花线、小倍图、零图表垃圾</sub>
<br /><sub><b>最佳场景</b> · 数据叙事 · 研究综述 · 学术论文</sub>
</td>
</tr>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/nyt-the-daily.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/nyt-the-daily.webp" alt="nyt-the-daily preview" /></a>
<br /><strong><code>nyt-the-daily</code></strong>
<br /><sub>Cheltenham 压过 Imperial、日期线高于一切、大报的庄重</sub>
<br /><sub><b>最佳场景</b> · 新闻特稿 · 播客流枢纽 · 长报道</sub>
</td>
<td align="center" width="50%" valign="middle">
<br />
<strong>当需求这样说时</strong>
<br /><sub>"数据密集" · "导视" · "紧凑" · "理性" · "权威纪实"</sub>
<br /><br />
<sub>规格见 <a href="./references/style-recipes/">style-recipes/</a></sub>
<br /><br />
</td>
</tr>
</table>

### 现代工具 / Builder SaaS · 4 个配方

> 发丝级细节、温暖的暗色、单一强调色——2020 年代后期的开发者工具美学。

<table>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/linear.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/linear.webp" alt="linear preview" /></a>
<br /><strong><code>linear</code></strong>
<br /><sub>温暖的暗色、发丝级边框、紫色的点缀、快捷键标签</sub>
<br /><sub><b>最佳场景</b> · 开发者工具落地页 · 事务 / 项目类 SaaS · API 与基建产品</sub>
</td>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/vercel-mesh.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/vercel-mesh.webp" alt="vercel-mesh preview" /></a>
<br /><strong><code>vercel-mesh</code></strong>
<br /><sub>纯黑、几何网格渐变、Geist Sans、命令行般的清晰</sub>
<br /><sub><b>最佳场景</b> · 部署 / 运行时工具 · 框架发布 · 技术主视觉页</sub>
</td>
</tr>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/raycast.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/raycast.webp" alt="raycast preview" /></a>
<br /><strong><code>raycast</code></strong>
<br /><sub>红色虚空上的玻璃卡片、键盘优先、紧凑的列表单元</sub>
<br /><sub><b>最佳场景</b> · 命令面板 · 启动器应用 · 键盘驱动的工具</sub>
</td>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/notion-pre-ai.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/notion-pre-ai.webp" alt="notion-pre-ai preview" /></a>
<br /><strong><code>notion-pre-ai</code></strong>
<br /><sub>米白页面、拖拽手柄圆点、随性的 emoji 标题、四处可见的标注框</sub>
<br /><sub><b>最佳场景</b> ·  workspace 文档 · 内部 wiki · 友好的生产力应用</sub>
</td>
</tr>
</table>

### 动效 / 实验 · 3 个配方

> 大胆、生成式、感官化——当需求要求"电影感"、"WebGL"或"冲奖级"。

<table>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/field-io.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/field-io.webp" alt="field-io preview" /></a>
<br /><strong><code>field-io</code></strong>
<br /><sub>编辑字体背后的粒子系统、代码艺术质感、暗色工作室</sub>
<br /><sub><b>最佳场景</b> · 创意科技工作室 · 生成艺术案例 · WebGL 作品集</sub>
</td>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/active-theory.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/active-theory.webp" alt="active-theory preview" /></a>
<br /><strong><code>active-theory</code></strong>
<br /><sub>WebGL 野心、满幅字体、深黑之上的糖果色</sub>
<br /><sub><b>最佳场景</b> · 电影感产品发布 · 营销活动站点 · 冲奖级微型站</sub>
</td>
</tr>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/resn-storytelling.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/resn-storytelling.webp" alt="resn-storytelling preview" /></a>
<br /><strong><code>resn-storytelling</code></strong>
<br /><sub>超现实、丰盈、每一帧都是静帧画面、压在纹理噪点上的标题</sub>
<br /><sub><b>最佳场景</b> · 叙事滚动 · 娱乐 / IP 站点 · 代理商 reel</sub>
</td>
<td align="center" width="50%" valign="middle">
<br />
<strong>当需求这样说时</strong>
<br /><sub>"电影感" · "WebGL" · "体验式" · "Awwwards 级"</sub>
<br /><br />
<sub>规格见 <a href="./references/style-recipes/">style-recipes/</a></sub>
<br /><br />
</td>
</tr>
</table>

### 野兽派 / 原始 · 3 个配方

> 反设计、诚实、未打磨——系统默认的网页、小报封面、反奢华的奢华。

<table>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/are-na.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/are-na.webp" alt="are-na preview" /></a>
<br /><strong><code>are-na</code></strong>
<br /><sub>刻意使用系统字体、浏览器默认的蓝色链接、诚实的网页</sub>
<br /><sub><b>最佳场景</b> · 研究频道 · 独立社区 · 反设计的内容工具</sub>
</td>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/bloomberg-businessweek-turley.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/bloomberg-businessweek-turley.webp" alt="bloomberg-businessweek-turley preview" /></a>
<br /><strong><code>bloomberg-businessweek-turley</code></strong>
<br /><sub>黄色警示 + 黑墨、拼贴式的字体、手裁的标题</sub>
<br /><sub><b>最佳场景</b> · 编辑封面 · 评论文章 · 营销海报</sub>
</td>
</tr>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/balenciaga-post-2017.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/balenciaga-post-2017.webp" alt="balenciaga-post-2017 preview" /></a>
<br /><strong><code>balenciaga-post-2017</code></strong>
<br /><sub>全大写、破碎的网格、白底上 Deadpan 的产品、反奢华的奢华</sub>
<br /><sub><b>最佳场景</b> · 时装系列 · 上新公告 · 反主流的奢侈</sub>
</td>
<td align="center" width="50%" valign="middle">
<br />
<strong>当需求这样说时</strong>
<br /><sub>"原始" · "诚实" · "反设计" · "小报风" · "令人不适"</sub>
<br /><br />
<sub>规格见 <a href="./references/style-recipes/">style-recipes/</a></sub>
<br /><br />
</td>
</tr>
</table>

### 温暖人文 · 3 个配方

> 亲切、有机、手作感——小企业的拉拉队、手工装订的书、每日重置。

<table>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/mailchimp-freddie.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/mailchimp-freddie.webp" alt="mailchimp-freddie preview" /></a>
<br /><strong><code>mailchimp-freddie</code></strong>
<br /><sub>Cavendish 黄、手绘涂鸦、对话式文案、中小企业的拉拉队</sub>
<br /><sub><b>最佳场景</b> · 新手引导流程 · 中小企业营销工具 · 友好的消费应用</sub>
</td>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/stripe-press.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/stripe-press.webp" alt="stripe-press preview" /></a>
<br /><strong><code>stripe-press</code></strong>
<br /><sub>奶油纸、GT Super、手工装订的奢华、把想法当作物体</sub>
<br /><sub><b>最佳场景</b> · 图书详情页 · 长文随笔 · 出版方 / 媒体站点</sub>
</td>
</tr>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/headspace-meditation.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/headspace-meditation.webp" alt="headspace-meditation preview" /></a>
<br /><strong><code>headspace-meditation</code></strong>
<br /><sub>橙色的太阳、圆润的色块、手绘的宁静、每日一次重置</sub>
<br /><sub><b>最佳场景</b> · 冥想与健康 · 习惯 / 情绪类应用 · 温馨的消费卡片</sub>
</td>
<td align="center" width="50%" valign="middle">
<br />
<strong>当需求这样说时</strong>
<br /><sub>"友好" · "亲切" · "有人味" · "温馨" · "手作感"</sub>
<br /><br />
<sub>规格见 <a href="./references/style-recipes/">style-recipes/</a></sub>
<br /><br />
</td>
</tr>
</table>

### Specialty / Genre · 2 个配方

> 时代编码、年代编码、主题编码——只能通过直接锚点名访问。

<table>
<tr>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/y2k-retrofuturism.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/y2k-retrofuturism.webp" alt="y2k-retrofuturism preview" /></a>
<br /><strong><code>y2k-retrofuturism</code></strong>
<br /><sub>铬色斜角、磨砂玻璃、熔岩色块、处处 MSN 蓝</sub>
<br /><sub><b>最佳场景</b> · Y2K 怀旧 · 早期网页门户 · Z 世代品牌噱头</sub>
</td>
<td align="center" width="50%">
<a href="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/mid-century-modern.webp"><img src="https://cdn.jsdelivr.net/gh/ConardLi/assets@main/imgs/web-design/mid-century-modern.webp" alt="mid-century-modern preview" /></a>
<br /><strong><code>mid-century-modern</code></strong>
<br /><sub>芥末黄、砖红、青蓝；剪纸几何；1957 年的乐观主义</sub>
<br /><sub><b>最佳场景</b> · 海报致敬 · 文化活动 · 复古印刷的品牌腔调</sub>
</td>
</tr>
</table>

### 自己运行画廊

```bash
cd demo/web-design-engineer-demo
npm install && npm run dev    # http://localhost:5181/
```

基于哈希路由的 URL（`#/linear`、`#/aesop`、…）可深链到任意配方。按 `H` 切换配方 HUD，按 `Esc` 返回画廊。关于布局细节，见该演示自己的 [README](../../demo/web-design-engineer-demo/README.md)。

---

## 前后对比：开启 / 关闭技能

仓库的 [`demo/web-design-demo/`](../../demo/web-design-demo) 目录中，收录了在完全相同提示下、有无该技能生成页面的并排对比。打开 [`demo/web-design-demo/demo2/index.html`](../../demo/web-design-demo/demo2/index.html) 即可查看并排对比。

### 演示 1：太空探索博物馆

**提示词：** *"为一个虚构的'太空探索博物馆'构建首页——全屏主视觉、4 个展览板块、一条含 6+ 里程碑的时间轴、一个预订 CTA，以及页脚。深邃、沉浸、宇宙感。"*

| | 关闭技能 | 开启技能 |
|---|---|---|
| **文件** | `demo/web-design-demo/demo2/demo1.html` | `demo/web-design-demo/demo2/demo1-with-skill.html` |
| **色彩体系** | 硬编码的 hex 值（#7cf0ff、#b388ff） | 基于 oklch 的令牌体系，使用 CSS 自定义属性 |
| **字体** | Orbitron + Noto Serif SC | Instrument Serif + Space Grotesk + JetBrains Mono |
| **布局** | 标准落地页结构 | 编辑杂志式的网格构图布局 |
| **细节** | 浓重的发光效果、霓虹渐变 | 克制的配色、排版层级、装饰性数据元素 |
| **整体观感** | 热情的初级设计师 | 经验丰富的设计总监 |

### 演示 2：摄影师作品集

**提示词：** *"为一个独立摄影师的作品集构建首页。"*

| | 开启技能 |
|---|---|
| **文件** | `demo/web-design-demo/demo2/demo2-with-skill.html` |
| **角色** | 虚构一位北欧摄影师"Mira Høst"，并构建完整的视觉识别 |
| **色彩** | 纸感暖白（#f2efe8）+ 墨黑（#161513）——极度克制的双色配色 |
| **字体** | Instrument Serif（展示）+ Space Grotesk（UI），大量使用斜体 |
| **布局** | 杂志编辑式结构，含编号板块、非对称网格、侧栏 |
| **动效** | 主视觉图上缓慢的 Ken Burns 效果（24 秒循环），叠加胶片颗粒质感 |
| **导航** | `mix-blend-mode: difference` 报头——在浅色 / 深色板块间无缝过渡 |

> 启发本技能的 Claude Design 原始系统提示，已保存在 [`dist/prompt/claude-design-system-prompt.md`](../../dist/prompt/claude-design-system-prompt.md)。

---

## 背景

本技能灵感来自 [Claude Design](https://www.anthropic.com/news/claude-design-anthropic-labs) 的系统提示。Claude Design 是 Anthropic 于 2026 年 4 月推出的视觉设计产品，其系统提示（约 420 行）编码了一整套成熟的设计原则、反模式与工作流约束，使其输出始终保持高质量。

本项目将那些核心理念提炼、打磨成一个可移植的技能，可与任意 AI 编程 Agent 协同工作——让你无需受产品绑定或用量限制，也能获得 Claude Design 级别的设计品味。

相对于原始 Claude Design 提示，本项目的关键增补：

- **设计体系声明步骤**——强制 AI 在编码前用自然语言阐明设计令牌
- **v0 草稿策略**——一套让进行中工作尽早可见的具体方法
- **扩充的反陈词滥调清单**——从真实 AI 输出中识别出的额外模式
- **占位符哲学**——一套专业处理缺失素材的完整框架
- **色彩 × 字体组合表**——六个经过验证的视觉体系起点
- **设计方向顾问**——面向含糊请求、横跨六流派的对话式工具，并明确交接给配方库
- **25 配方带锚点的风格库**——每个配方都绑定真实的品牌 / 工作室 / 设计师，附带可复制的具体数值；抵御 AI 默认的糊弄输出
- **高级模式库**——面向常见 UI 模式的即用型代码模板

---

## 许可协议

MIT
