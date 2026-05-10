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
