# 背景音乐

本目录已经内置两首**原创合成曲**，直接随游戏播放，不涉及任何版权采样；两首都以 **CC0 1.0（公共领域）** 发布，可自由使用，详见 [LICENSE.txt](LICENSE.txt)。

| 文件 | 曲名 | 时长 | 用途 |
| --- | --- | --- | --- |
| `menu.wav` | **Neon Range** | 21.3s 无缝循环 | 开始界面：暗色合成器 Pad + 琶音 + 低频脉冲 |
| `results.wav` | **Target Cleared** | 12.0s | 结算界面：冲击音 + 上行和弦 + 铃音尾声 |

两首都由 [generate_music.py](generate_music.py) 纯程序合成（Python + numpy，可重复生成），没有采样任何现有歌曲。

## 换成自己的音乐

把音频放到本目录，按下面的优先级命名即可覆盖内置曲：

| 播放时机 | 文件名（按优先级） |
| --- | --- |
| 开始界面 | `we-never-remix.mp3/ogg/m4a/wav` → `menu.mp3/ogg/m4a` → 内置 `menu.wav` |
| 结算界面 | `die-for-you.mp3/ogg/m4a/wav` → `results.mp3/ogg/m4a` → 内置 `results.wav` |

例如：

```text
aim-trainer/
├── index.html
└── music/
    ├── menu.wav              ← 内置（可保留）
    ├── results.wav           ← 内置（可保留）
    ├── we-never-remix.mp3    ← 你的开始界面音乐，优先于内置
    └── die-for-you.mp3       ← 你的结算音乐，优先于内置
```

> 想完全用内置曲，就删掉自己加的文件即可。

## 用 URL 参数指定任意音频

```text
index.html?menuMusic=music/我的开始曲.mp3&resultMusic=music/我的结算曲.mp3
```

## 播放与排错

1. 刷新页面后**先点一下页面**（浏览器会拦截带声音的自动播放）。
2. 菜单右下角「音乐：开/关」可随时切换；如果一直找不到音乐，会显示红色提示。
3. 控制台运行 `AimTrainer.getState().music` 可查看实际加载路径、是否解码成功（`menuAvailable` / `resultAvailable`）和时长。
4. 支持 mp3 / ogg / m4a / wav；iPhone 建议 mp3 或 m4a（Safari 对 ogg 支持较差）。
5. 文件名或扩展名必须和真实格式一致；`music/` 必须和 `index.html` 同级。
6. 本地 `file://` 打不开音频时，可在 `aim-trainer` 的上级目录运行 `python -m http.server 8000`，用 `http://localhost:8000/aim-trainer/` 打开。
7. 音量：开始界面约 42%，结算约 50%，在 `index.html` 的 `makeTrack(...)` 调用里可调。

## 重新生成内置音乐

```bash
python music/generate_music.py
```

需要 Python 3 + numpy。脚本是确定性的，重复运行会生成相同的 `menu.wav` / `results.wav`。
