# Custom-desktop-pets
一个完全可定制的桌面宠物程序，支持 GIF 动图皮肤、随机互动、拖拽、全屏自动暂停等特性。绿色便携，配置即开即用。内附完整教程<br>
Customize your desktop pets. You can upload your own little cats and dogs as desktop pets. It comes with a complete tutorial for making them.
<img width="496" height="372" alt="image" src="https://github.com/user-attachments/assets/3681248c-6967-47cf-92ae-9fbe1d576d9f" />
## 功能特点

- 🐱 **完全可换肤**：支持分别指定“待机”和“行走”GIF，自动拆帧生成皮肤。
- 🎲 **随机互动**：可添加多个随机动画，单击/双击宠物随机播放，或定时自动播放。
- 🖱️ **桌面交互**：拖拽移动、锁定位置、点击穿透、自动行走/静止模式。
- 🧰 **系统托盘**：右键托盘图标访问所有功能和设置。
- 📦 **绿色便携**：所有数据保存在程序同目录下的 `CatPet_Data` 文件夹，配置即打包，分享即用。
- 💾 **完整记忆**：皮肤、位置、开关状态、速度、缩放等全部自动保存。
- 🎮 **游戏模式**：检测到全屏应用（游戏/视频）时自动暂停行走，不打扰。
## 下载与运行

### 方式一：直接运行（无需安装）推荐！
1. 从 [Releases](../../releases) 下载 `DesktopPet.zip`
2. 解压到任意文件夹
3. 双击 `DesktopPet.exe` 启动
4. 托盘区会出现猫爪图标，右键可打开菜单
### 方式二：从源码运行
```bash
git clone https://github.com/EagleVast/Custom-desktio-pets.git
cd Custom-desktio-pets
pip install PyQt5 pywin32 Pillow
python desktop_pet.py
```
自行打包为 EXE
```
pip install pyinstaller
pyinstaller --onefile --windowed --name=CatPet --icon=a.ico desktop_pet.py
```
## 使用指南
### 基础操作
- 更换基础皮肤

托盘菜单 → “更换基础皮肤”，分别选择待机 GIF 和行走 GIF，程序自动生成皮肤并应用。

- 添加随机动画

托盘菜单 → “随机动画管理” → 添加点击动画或定时动画。

-- 点击动画：单击/双击宠物时随机播放。

-- 定时动画：每隔一段时间自动播放（可在设置中调整间隔）。

- 移动模式

支持“自动行走”（屏幕边缘来回走）和“静止”两种模式。

- 穿透模式

开启后鼠标可直接穿透宠物点击背后窗口；关闭时可拖拽宠物。

- 位置锁定

锁定后宠物不能被拖拽或移动。

- 缩放

在设置窗口中调整宠物大小（50%–200%），保持原始宽高比。
### 设置窗口
通过托盘菜单 → “设置” 打开，包含以下标签页：
<img width="800" height="284" alt="image" src="https://github.com/user-attachments/assets/e9a25530-18c4-4ee6-9919-27962678c358" />

## 文件结构(便携式)
```text
DesktopPet.exe
CatPet_Data/
├── config.ini          # 全局配置（位置、速度、皮肤名等）
├── random_anims.json   # 随机动画列表
├── skins/              # 所有皮肤文件夹
│   ├── default/        # 默认皮肤（红色方块示例）
│   └── 你添加的皮肤/
└── logs/               # 错误日志
```
## 如何将自己的配置分享给其他人
将 DesktopPet.exe 与同目录下的 CatPet_Data 文件夹一起压缩成 zip（例如 DesktopPet_我的配置.zip），发送给朋友。对方解压后直接运行 exe 即可看到您设置好的所有内容。
## 常见问题
### ❓ 为什么皮肤加载失败？
- GIF 文件可能过大（超过 100 帧或宽度超过 200px），程序会自动压缩，但仍建议使用短小 GIF。
- 确保 GIF 是有效的动画文件。

---

### ❌ 程序崩溃怎么办？
- 查看 `CatPet_Data/logs/error.log`，获取详细错误信息。可提交 Issue 附上日志内容。

---

### 🚪 如何完全退出程序？
- 右键托盘图标 → “退出”。关闭窗口仅隐藏到托盘。

---

### ⏰ 开机自启不生效？
- 某些安全软件可能拦截注册表操作。可以手动将 `DesktopPet.exe` 的快捷方式放入 `shell:startup` 文件夹。

---

### 📦 为什么我配置好的设置发给别人后不见了？
- 您必须将 `CatPet_Data` 文件夹一起打包。单独发送 exe 只会生成默认配置。
## 开发依赖
Python 3.8+<br>
PyQt5<br>
pywin32<br>
Pillow
## 贡献与反馈
欢迎提交 Issue 或 Pull Request。如果有有趣的 GIF 皮肤，也欢迎分享！<br>
Enjoy your digital pet! 🐾

## GIF制作参考
```text
GIF简单制作流程：
	静态GIF：
		jpg裁剪后导入抠图为png，修改后缀为gif
	动态GIF：
		视频裁剪后进行gif裁剪，裁掉多余的背景然后导入转为gif(建议360p+10帧)，最后gif抠图去掉背景即可

免登录修图网站：
	GIF裁剪：https://tool.lu/gifcropper/
	GIF抠图：https://adworker.ai/zh/tools/gif-background-remover/
	视频转GIF：https://converttool.org/zh-cn/video-tools/video-to-gif
	抠png：https://koukoukou.cn/(免费三张，做静态够用了)
		以上网址均为网上寻找，真假自辩，仅做分享，谨防上当受骗！
```
