import sys
import os
import json
import glob
import winreg
import shutil
import random
import traceback
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QMenu, QSystemTrayIcon,
                             QAction, QFileDialog, QMessageBox, QDialog,
                             QVBoxLayout, QCheckBox, QSlider, QLabel,
                             QSpinBox, QTabWidget, QPushButton, QListWidget,
                             QListWidgetItem, QHBoxLayout, QProgressDialog)
from PyQt5.QtCore import (Qt, QTimer, QPoint, QSettings, QCoreApplication, QSize,
                          QThread, pyqtSignal, QMutex)
from PyQt5.QtGui import (QPainter, QPixmap, QIcon, QColor, QImage, QTransform,
                         QPen, QBrush, QCursor, QPixmapCache)

import win32gui
import win32con
import win32api

# ---------------------------- 便携模式：数据目录在 exe 同级 ----------------------------
def get_data_dir():
    """获取便携数据目录（exe所在目录下的 CatPet_Data）"""
    if getattr(sys, 'frozen', False):
        # 打包后的 exe
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境运行脚本
        base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "CatPet_Data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

# 全局常量 - 所有数据都在便携目录下
APP_NAME = "CatPet"
APP_DIR = get_data_dir()                     # 主数据目录
LOG_DIR = os.path.join(APP_DIR, "logs")
SKINS_DIR = os.path.join(APP_DIR, "skins")
RANDOM_DIR = os.path.join(APP_DIR, "random_anims")
DEFAULT_SKIN = "default"
CONFIG_FILE = os.path.join(APP_DIR, "config.ini")
RANDOM_CONFIG = os.path.join(APP_DIR, "random_anims.json")

# ---------------------------- 全局异常钩子 ----------------------------
def global_exception_hook(exctype, value, tb):
    msg = f"未捕获异常: {exctype} {value}\n{traceback.format_tb(tb)}"
    log_error(msg)
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = global_exception_hook

# ---------------------------- 日志 ----------------------------
def log_error(msg):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, "error.log"), "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()}: {msg}\n")

# ---------------------------- 工具函数 ----------------------------
def is_fullscreen_window():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return False
        rect = win32gui.GetWindowRect(hwnd)
        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        return (rect[2] - rect[0] >= screen_width and
                rect[3] - rect[1] >= screen_height)
    except:
        return False

def set_clickthrough(hwnd, enable):
    try:
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if enable:
            ex_style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
        else:
            ex_style &= ~win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
    except:
        pass

def hide_from_taskbar(hwnd):
    try:
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        ex_style |= win32con.WS_EX_TOOLWINDOW
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
    except:
        pass

# ---------------------------- GIF 拆帧工具 ----------------------------
from PIL import Image
def gif_to_pngs(gif_path, output_dir, prefix, max_frames=100, max_width=200, progress_callback=None):
    from PIL import Image
    try:
        os.makedirs(output_dir, exist_ok=True)
        gif = Image.open(gif_path)
        frames = []
        i = 0
        while True:
            try:
                if progress_callback:
                    progress_callback(i, "拆帧中...")
                gif.seek(i)
                frame = gif.convert("RGBA")
                if frame.width > max_width:
                    ratio = max_width / frame.width
                    new_size = (max_width, int(frame.height * ratio))
                    frame = frame.resize(new_size, Image.LANCZOS)
                frame_path = os.path.join(output_dir, f"{prefix}_{i:03d}.png")
                frame.save(frame_path, "PNG")
                frames.append(frame_path)
                i += 1
                if i >= max_frames:
                    log_error(f"警告：{gif_path} 帧数超过 {max_frames}，已截断")
                    break
            except EOFError:
                break
        return frames
    except Exception as e:
        log_error(f"GIF拆帧失败: {e}")
        return []

# ---------------------------- 随机动画管理 ----------------------------
class RandomAnimManager:
    def __init__(self):
        self.click_anims = []
        self.timer_anims = []
        self.load()
    def load(self):
        if os.path.exists(RANDOM_CONFIG):
            try:
                with open(RANDOM_CONFIG, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.click_anims = data.get("click_anims", [])
                self.timer_anims = data.get("timer_anims", [])
            except:
                pass
    def save(self):
        with open(RANDOM_CONFIG, "w", encoding="utf-8") as f:
            json.dump({"click_anims": self.click_anims, "timer_anims": self.timer_anims}, f, indent=2)
    def add_click_anim(self, skin_name, action_name):
        self.click_anims.append((skin_name, action_name))
        self.save()
    def add_timer_anim(self, skin_name, action_name):
        self.timer_anims.append((skin_name, action_name))
        self.save()
    def remove_click_anim(self, index):
        del self.click_anims[index]
        self.save()
    def remove_timer_anim(self, index):
        del self.timer_anims[index]
        self.save()
    def get_random_click(self):
        if self.click_anims:
            return random.choice(self.click_anims)
        return None
    def get_random_timer(self):
        if self.timer_anims:
            return random.choice(self.timer_anims)
        return None

# ---------------------------- 皮肤管理 ----------------------------
class SkinManager:
    def __init__(self):
        self.current_skin = None
        self.actions = {}
        self.fps = 10
        self.mirror = True
        self.original_sizes = {}
        os.makedirs(SKINS_DIR, exist_ok=True)
    def create_skin_from_gifs(self, skin_name, idle_gif_path, walk_gif_path, progress_parent=None):
        skin_path = os.path.join(SKINS_DIR, skin_name)
        if os.path.exists(skin_path):
            shutil.rmtree(skin_path)
        os.makedirs(skin_path)
        def progress_callback(current, msg):
            if progress_parent:
                QApplication.processEvents()
        idle_frames = gif_to_pngs(idle_gif_path, skin_path, "idle", max_frames=100, max_width=200,
                                  progress_callback=progress_callback)
        walk_frames = gif_to_pngs(walk_gif_path, skin_path, "walk", max_frames=100, max_width=200,
                                  progress_callback=progress_callback)
        if idle_frames:
            shutil.copy(idle_frames[0], os.path.join(skin_path, "click_000.png"))
            shutil.copy(idle_frames[0], os.path.join(skin_path, "drag_000.png"))
            shutil.copy(idle_frames[0], os.path.join(skin_path, "special_000.png"))
        config = {
            "fps": 10, "mirror_walk": True,
            "animations": {
                "idle": {"pattern": "idle_*.png", "loop": True, "frame_time": 0.1},
                "walk": {"pattern": "walk_*.png", "loop": True, "frame_time": 0.08},
                "click": {"pattern": "click_*.png", "loop": False, "next": "idle", "frame_time": 0.1},
                "drag": {"pattern": "drag_*.png", "loop": True, "frame_time": 0.05},
                "idle_special": {"pattern": "special_*.png", "loop": False, "next": "idle", "frame_time": 0.12}
            }
        }
        with open(os.path.join(skin_path, "config.json"), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return self.load_skin(skin_name)
    def add_random_animation(self, base_skin_name, gif_path, action_name, progress_parent=None):
        skin_path = os.path.join(SKINS_DIR, base_skin_name)
        if not os.path.exists(skin_path):
            return False
        frames = gif_to_pngs(gif_path, skin_path, action_name, max_frames=100, max_width=200)
        if not frames:
            return False
        config_path = os.path.join(skin_path, "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        cfg["animations"][action_name] = {
            "pattern": f"{action_name}_*.png",
            "loop": False, "next": "idle", "frame_time": 0.1
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        return self.load_skin(base_skin_name)
    def load_skin(self, skin_name):
        skin_path = os.path.join(SKINS_DIR, skin_name)
        config_path = os.path.join(skin_path, "config.json")
        if not os.path.exists(config_path):
            log_error(f"Skin {skin_name} config not found")
            return False
        try:
            QPixmapCache.clear()
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.actions = {}
            for act, data in cfg.get("animations", {}).items():
                frames = []
                pattern = data.get("pattern", "")
                if pattern:
                    files = sorted(glob.glob(os.path.join(skin_path, pattern)))
                    for f in files:
                        pix = QPixmap(f)
                        if not pix.isNull():
                            frames.append(pix)
                self.actions[act] = {
                    "frames": frames,
                    "loop": data.get("loop", True),
                    "next": data.get("next", None),
                    "frame_time": data.get("frame_time", 0.1)
                }
                if frames:
                    self.original_sizes[act] = (frames[0].width(), frames[0].height())
            self.fps = cfg.get("fps", 10)
            self.mirror = cfg.get("mirror_walk", True)
            self.current_skin = skin_name
            return True
        except Exception as e:
            log_error(f"Load skin error: {e}")
            return False
    def get_action_frames(self, action):
        return self.actions.get(action, {"frames": []})["frames"]
    def get_action_info(self, action):
        return self.actions.get(action, {"loop": True, "frame_time": 0.1})
    def get_original_size(self, action):
        return self.original_sizes.get(action, (100, 100))
    def has_action(self, action):
        return action in self.actions and len(self.actions[action]["frames"]) > 0

# ---------------------------- 主窗口 ----------------------------
class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        self.skin_mgr = SkinManager()
        self.random_mgr = RandomAnimManager()
        self.current_action = "idle"
        self.current_frame = 0
        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(self.next_frame)
        self.pet_pos = QPoint(100, 100)
        self.dragging = False
        self.drag_offset = QPoint()
        self.move_mode = "stop"
        self.walk_speed = 80
        self.walk_direction = 1
        self.locked = False
        self.clickthrough = True
        self.fullscreen_pause = False
        self.idle_timer = QTimer()
        self.idle_timer.setSingleShot(True)
        self.idle_timeout = 30
        self.idle_timer.timeout.connect(self.on_idle_timeout)

        self.random_timer = QTimer()
        self.random_interval = 60
        self.random_timer.timeout.connect(self.trigger_random_timer_anim)
        self.random_timer.start(self.random_interval * 1000)

        self.is_paused = False
        self.scale_percent = 100
        self.scale = 1.0
        self.auto_start = False

        # 窗口标志
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setMouseTracking(True)
        self.resize(100, 100)

        # 系统托盘
        self.tray_icon = self.create_default_tray_icon()
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.tray_icon)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

        self.show()
        hwnd = int(self.winId())
        hide_from_taskbar(hwnd)
        self.setWindowOpacity(1.0)

        # 加载配置（包括位置、皮肤等）
        self.load_config()

        # 加载默认皮肤（如果配置中没有有效的皮肤，则使用默认）
        if not self.restore_last_skin():
            self.load_default_skin()

        self.current_action = "idle"
        self.update_action()
        self.apply_scale()

        # 移动宠物到保存的位置，如果位置无效则右下角
        if not self.move_to_saved_position():
            self.move_to_bottom_right()

        self.apply_clickthrough()

        self.init_timers()
        # 全屏检测
        self.fullscreen_checker = QTimer()
        self.fullscreen_checker.timeout.connect(self.check_fullscreen)
        self.fullscreen_checker.start(1000)

    # ------------------ 记忆功能辅助方法 ------------------
    def restore_last_skin(self):
        """尝试加载上次使用的皮肤，返回是否成功"""
        last_skin = self.settings.value("last_skin", DEFAULT_SKIN, type=str)
        if last_skin and self.skin_mgr.load_skin(last_skin):
            return True
        return False

    def move_to_saved_position(self):
        """移动到保存的位置，如果位置有效则返回True"""
        x = self.settings.value("pet_pos_x", -1, type=int)
        y = self.settings.value("pet_pos_y", -1, type=int)
        if x >= 0 and y >= 0:
            self.pet_pos = QPoint(x, y)
            self.move(self.pet_pos)
            return True
        return False

    # ------------------ 原有方法 ------------------
    def create_default_tray_icon(self):
        pix = QPixmap(64, 64)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 165, 0)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(8, 8, 48, 48)
        painter.setBrush(QBrush(Qt.white))
        painter.drawEllipse(20, 24, 8, 8)
        painter.drawEllipse(36, 24, 8, 8)
        painter.setBrush(QBrush(Qt.black))
        painter.drawEllipse(22, 26, 4, 4)
        painter.drawEllipse(38, 26, 4, 4)
        painter.setBrush(QBrush(Qt.black))
        painter.drawEllipse(30, 34, 4, 4)
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(16, 32, 8, 28)
        painter.drawLine(16, 36, 8, 40)
        painter.drawLine(48, 32, 56, 28)
        painter.drawLine(48, 36, 56, 40)
        painter.end()
        return QIcon(pix)

    def move_to_bottom_right(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        margin = 20
        x = screen_geometry.right() - self.width() - margin
        y = screen_geometry.bottom() - self.height() - margin
        self.pet_pos = QPoint(x, y)
        self.move(self.pet_pos)

    def load_default_skin(self):
        default_path = os.path.join(SKINS_DIR, DEFAULT_SKIN)
        if not os.path.exists(default_path):
            os.makedirs(default_path, exist_ok=True)
            sample_cfg = {
                "fps": 10, "mirror_walk": True,
                "animations": {
                    "idle": {"pattern": "idle_*.png", "loop": True, "frame_time": 0.1},
                    "walk": {"pattern": "walk_*.png", "loop": True, "frame_time": 0.08},
                    "click": {"pattern": "click_*.png", "loop": False, "next": "idle", "frame_time": 0.1},
                    "drag": {"pattern": "drag_*.png", "loop": True, "frame_time": 0.05},
                    "idle_special": {"pattern": "special_*.png", "loop": False, "next": "idle", "frame_time": 0.12}
                }
            }
            with open(os.path.join(default_path, "config.json"), "w") as f:
                json.dump(sample_cfg, f, indent=2)
            for anim in ["idle", "walk", "click", "drag", "special"]:
                for i in range(4):
                    img = QImage(64, 64, QImage.Format_ARGB32)
                    img.fill(QColor(255, 0, 0, 200))
                    img.save(os.path.join(default_path, f"{anim}_{i}.png"))
        self.skin_mgr.load_skin(DEFAULT_SKIN)

    def load_config(self):
        self.settings = QSettings(CONFIG_FILE, QSettings.IniFormat)
        # 原有设置
        self.clickthrough = self.settings.value("clickthrough", True, type=bool)
        self.move_mode = self.settings.value("move_mode", "stop")
        self.walk_speed = self.settings.value("walk_speed", 80, type=int)
        self.idle_timeout = self.settings.value("idle_timeout", 30, type=int)
        self.scale_percent = self.settings.value("scale_percent", 100, type=int)
        self.scale = self.scale_percent / 100.0
        self.auto_start = self.settings.value("auto_start", False, type=bool)
        self.random_interval = self.settings.value("random_interval", 60, type=int)
        self.locked = self.settings.value("locked", False, type=bool)
        self.set_auto_start(self.auto_start)
        self.random_timer.start(self.random_interval * 1000)

    def save_config(self):
        self.settings.setValue("clickthrough", self.clickthrough)
        self.settings.setValue("move_mode", self.move_mode)
        self.settings.setValue("walk_speed", self.walk_speed)
        self.settings.setValue("idle_timeout", self.idle_timeout)
        self.settings.setValue("scale_percent", self.scale_percent)
        self.settings.setValue("auto_start", self.auto_start)
        self.settings.setValue("random_interval", self.random_interval)
        # 保存位置、皮肤、锁定状态
        self.settings.setValue("pet_pos_x", self.pet_pos.x())
        self.settings.setValue("pet_pos_y", self.pet_pos.y())
        if self.skin_mgr.current_skin:
            self.settings.setValue("last_skin", self.skin_mgr.current_skin)
        self.settings.setValue("locked", self.locked)
        self.settings.sync()

    def set_auto_start(self, enable):
        key = winreg.HKEY_CURRENT_USER
        path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(key, path, 0, winreg.KEY_SET_VALUE) as regkey:
                if enable:
                    winreg.SetValueEx(regkey, APP_NAME, 0, winreg.REG_SZ, sys.executable)
                else:
                    winreg.DeleteValue(regkey, APP_NAME)
        except Exception as e:
            log_error(f"Auto start error: {e}")

    def init_timers(self):
        self.frame_timer.start(100)
        self.walk_timer = QTimer()
        self.walk_timer.timeout.connect(self.update_walk)
        self.walk_timer.start(30)

    def next_frame(self):
        try:
            frames = self.skin_mgr.get_action_frames(self.current_action)
            if not frames:
                return
            info = self.skin_mgr.get_action_info(self.current_action)
            frame_time = info.get("frame_time", 0.1)
            self.frame_timer.setInterval(int(frame_time * 1000))
            self.current_frame = (self.current_frame + 1) % len(frames)
            self.update()
        except Exception as e:
            log_error(f"next_frame error: {e}")

    def apply_scale(self):
        try:
            frames = self.skin_mgr.get_action_frames(self.current_action)
            if frames:
                orig_w, orig_h = frames[0].width(), frames[0].height()
                new_w = int(orig_w * self.scale)
                new_h = int(orig_h * self.scale)
                self.resize(new_w, new_h)
                self.update_geometry()
        except Exception as e:
            log_error(f"apply_scale error: {e}")

    def set_action(self, action, force=False):
        if not force and self.current_action == action:
            return
        frames = self.skin_mgr.get_action_frames(action)
        if not frames:
            return
        self.current_action = action
        self.current_frame = 0
        self.apply_scale()
        self.update()
        info = self.skin_mgr.get_action_info(action)
        if not info["loop"] and info.get("next"):
            duration = info["frame_time"] * len(frames)
            QTimer.singleShot(int(duration * 1000), lambda: self.set_action(info["next"]))
        elif not info["loop"] and not info.get("next"):
            QTimer.singleShot(int(info["frame_time"] * len(frames) * 1000), lambda: self.set_action("idle"))

    def update_action(self):
        if self.is_paused or self.locked:
            self.set_action("idle")
            return
        if self.dragging:
            self.set_action("drag")
            return
        if self.move_mode == "auto" and not self.locked and not self.fullscreen_pause:
            self.set_action("walk")
        else:
            self.set_action("idle")

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            frames = self.skin_mgr.get_action_frames(self.current_action)
            if not frames:
                return
            pix = frames[self.current_frame % len(frames)]
            if self.scale != 1.0:
                new_size = pix.size() * self.scale
                pix = pix.scaled(new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if self.current_action == "walk" and self.skin_mgr.mirror and self.walk_direction == -1:
                pix = pix.transformed(QTransform().scale(-1, 1))
            painter.drawPixmap(0, 0, pix)
        except Exception as e:
            log_error(f"paintEvent error: {e}")

    def update_geometry(self):
        self.move(self.pet_pos)

    def update_walk(self):
        try:
            if self.locked or self.dragging or self.move_mode != "auto" or self.fullscreen_pause:
                return
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            pet_rect = self.geometry()
            new_x = self.pet_pos.x() + self.walk_speed * self.walk_direction / 30.0
            if new_x <= screen_rect.left():
                new_x = screen_rect.left()
                self.walk_direction = 1
            elif new_x + pet_rect.width() >= screen_rect.right():
                new_x = screen_rect.right() - pet_rect.width()
                self.walk_direction = -1
            self.pet_pos.setX(int(new_x))
            self.update_geometry()
            if self.current_action != "walk":
                self.set_action("walk")
        except Exception as e:
            log_error(f"update_walk error: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.locked:
                return
            self.dragging = True
            self.drag_offset = event.globalPos() - self.pet_pos
            self.set_action("drag")
            self.update_action()
            self.idle_timer.stop()

    def mouseMoveEvent(self, event):
        if self.dragging and not self.locked:
            new_pos = event.globalPos() - self.drag_offset
            self.pet_pos = new_pos
            self.update_geometry()
            self.update_action()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            self.update_action()
            self.save_config()   # 拖拽结束后保存位置
            if self.move_mode == "auto":
                QTimer.singleShot(2000, self.resume_walk)

    def mouseDoubleClickEvent(self, event):
        self.trigger_random_click()

    def trigger_random_click(self):
        anim = self.random_mgr.get_random_click()
        if anim:
            skin_name, action_name = anim
            if skin_name == self.skin_mgr.current_skin and self.skin_mgr.has_action(action_name):
                self.set_action(action_name, force=True)

    def trigger_random_timer_anim(self):
        if self.is_paused or self.fullscreen_pause or self.dragging:
            return
        anim = self.random_mgr.get_random_timer()
        if anim:
            skin_name, action_name = anim
            if skin_name == self.skin_mgr.current_skin and self.skin_mgr.has_action(action_name):
                if self.current_action in ["idle", "walk"]:
                    self.set_action(action_name, force=True)

    def on_idle_timeout(self):
        if self.current_action == "idle":
            self.trigger_random_timer_anim()

    # ------------------ 托盘菜单 ------------------
    def show_tray_menu(self):
        menu = QMenu()

        act_click = QAction("穿透模式 (开/关)", None)
        act_click.setCheckable(True)
        act_click.setChecked(self.clickthrough)
        act_click.triggered.connect(self.toggle_clickthrough)
        menu.addAction(act_click)

        act_lock = QAction("锁定位置", None)
        act_lock.setCheckable(True)
        act_lock.setChecked(self.locked)
        act_lock.triggered.connect(self.toggle_lock)
        menu.addAction(act_lock)

        move_menu = menu.addMenu("移动模式")
        act_auto = QAction("自动行走", None)
        act_auto.setCheckable(True)
        act_auto.setChecked(self.move_mode == "auto")
        act_auto.triggered.connect(lambda: self.set_move_mode("auto"))
        move_menu.addAction(act_auto)
        act_stop = QAction("静止", None)
        act_stop.setCheckable(True)
        act_stop.setChecked(self.move_mode == "stop")
        act_stop.triggered.connect(lambda: self.set_move_mode("stop"))
        move_menu.addAction(act_stop)

        random_menu = menu.addMenu("随机动画管理")
        act_add_click = QAction("添加随机点击动画 (GIF)", None)
        act_add_click.triggered.connect(self.add_random_click_anim)
        random_menu.addAction(act_add_click)
        act_add_timer = QAction("添加随机定时动画 (GIF)", None)
        act_add_timer.triggered.connect(self.add_random_timer_anim)
        random_menu.addAction(act_add_timer)
        act_manage = QAction("管理/删除随机动画", None)
        act_manage.triggered.connect(self.manage_random_anims)
        random_menu.addAction(act_manage)

        act_skin_walk = QAction("更换基础皮肤 (行走+待机GIF)", None)
        act_skin_walk.triggered.connect(self.change_base_skin)
        menu.addAction(act_skin_walk)

        act_set = QAction("设置...", None)
        act_set.triggered.connect(self.open_settings)
        menu.addAction(act_set)

        act_quit = QAction("退出", None)
        act_quit.triggered.connect(self.quit_app)
        menu.addAction(act_quit)

        menu.exec_(QCursor.pos())

    def add_random_click_anim(self):
        self._add_random_anim("click")
    def add_random_timer_anim(self):
        self._add_random_anim("timer")
    def _add_random_anim(self, anim_type):
        gif_path, _ = QFileDialog.getOpenFileName(None, "选择GIF动画", "", "GIF Files (*.gif)")
        if not gif_path:
            return
        progress = QProgressDialog("正在处理GIF，请稍候...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        import uuid
        action_name = f"rand_{anim_type}_{uuid.uuid4().hex[:8]}"
        try:
            success = self.skin_mgr.add_random_animation(self.skin_mgr.current_skin, gif_path, action_name)
        finally:
            progress.close()
        if success:
            if anim_type == "click":
                self.random_mgr.add_click_anim(self.skin_mgr.current_skin, action_name)
            else:
                self.random_mgr.add_timer_anim(self.skin_mgr.current_skin, action_name)
            QMessageBox.information(None, "成功", f"已添加随机{anim_type}动画")
            self.save_config()
        else:
            QMessageBox.warning(None, "错误", "添加动画失败，GIF可能损坏或过大")

    def manage_random_anims(self):
        dlg = RandomAnimManageDialog(self.random_mgr, self)
        dlg.exec_()

    def change_base_skin(self):
        idle_path, _ = QFileDialog.getOpenFileName(None, "选择待机动画 GIF", "", "GIF Files (*.gif)")
        if not idle_path:
            return
        walk_path, _ = QFileDialog.getOpenFileName(None, "选择行走动画 GIF", "", "GIF Files (*.gif)")
        if not walk_path:
            return
        progress = QProgressDialog("正在创建皮肤，请稍候...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        new_skin_name = f"skin_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            success = self.skin_mgr.create_skin_from_gifs(new_skin_name, idle_path, walk_path, progress_parent=self)
        finally:
            progress.close()
        if success:
            self.skin_mgr.load_skin(new_skin_name)
            self.current_action = "idle"
            self.update_action()
            self.save_config()
            QMessageBox.information(None, "成功", "基础皮肤已更换")
        else:
            QMessageBox.warning(None, "错误", "皮肤创建失败，请检查GIF文件")

    def toggle_clickthrough(self):
        self.clickthrough = not self.clickthrough
        self.apply_clickthrough()
        self.save_config()

    def apply_clickthrough(self):
        hwnd = int(self.winId())
        set_clickthrough(hwnd, self.clickthrough)

    def toggle_lock(self):
        self.locked = not self.locked
        self.update_action()
        self.save_config()

    def set_move_mode(self, mode):
        self.move_mode = mode
        self.update_action()
        self.save_config()

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec_():
            self.load_config()
            self.apply_clickthrough()
            self.apply_scale()
            self.update_action()
            self.save_config()

    def check_fullscreen(self):
        full = is_fullscreen_window()
        if full != self.fullscreen_pause:
            self.fullscreen_pause = full
            self.is_paused = full
            self.update_action()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()
            self.raise_()
        elif reason == QSystemTrayIcon.Context:
            self.show_tray_menu()

    def quit_app(self):
        self.save_config()
        self.frame_timer.stop()
        self.walk_timer.stop()
        self.fullscreen_checker.stop()
        self.random_timer.stop()
        self.tray.hide()
        QApplication.quit()

    def resume_walk(self):
        if not self.dragging and not self.locked and self.move_mode == "auto":
            self.update_action()

# ---------------------------- 随机动画管理对话框 ----------------------------
class RandomAnimManageDialog(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("管理随机动画")
        self.resize(400, 300)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("点击动画列表（单击/双击触发）:"))
        self.click_list = QListWidget()
        for idx, (skin, act) in enumerate(self.manager.click_anims):
            self.click_list.addItem(f"{skin} - {act}")
        layout.addWidget(self.click_list)
        btn_remove_click = QPushButton("删除选中的点击动画")
        btn_remove_click.clicked.connect(self.remove_click)
        layout.addWidget(btn_remove_click)
        layout.addWidget(QLabel("定时动画列表（每隔一段时间自动触发）:"))
        self.timer_list = QListWidget()
        for idx, (skin, act) in enumerate(self.manager.timer_anims):
            self.timer_list.addItem(f"{skin} - {act}")
        layout.addWidget(self.timer_list)
        btn_remove_timer = QPushButton("删除选中的定时动画")
        btn_remove_timer.clicked.connect(self.remove_timer)
        layout.addWidget(btn_remove_timer)
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        self.setLayout(layout)
    def remove_click(self):
        row = self.click_list.currentRow()
        if row >= 0:
            self.manager.remove_click_anim(row)
            self.click_list.takeItem(row)
    def remove_timer(self):
        row = self.timer_list.currentRow()
        if row >= 0:
            self.manager.remove_timer_anim(row)
            self.timer_list.takeItem(row)

# ---------------------------- 设置对话框 ----------------------------
class SettingsDialog(QDialog):
    def __init__(self, pet):
        super().__init__(pet)
        self.pet = pet
        self.setWindowTitle("详细设置")
        self.resize(400, 400)
        layout = QVBoxLayout()
        tabs = QTabWidget()
        # 通用
        general = QWidget()
        glayout = QVBoxLayout()
        self.cb_autostart = QCheckBox("开机自启")
        self.cb_autostart.setChecked(pet.auto_start)
        glayout.addWidget(self.cb_autostart)
        self.btn_tray_icon = QPushButton("更换托盘图标...")
        self.btn_tray_icon.clicked.connect(self.change_tray_icon)
        glayout.addWidget(self.btn_tray_icon)
        general.setLayout(glayout)
        tabs.addTab(general, "通用")
        # 动画
        anim = QWidget()
        alayout = QVBoxLayout()
        self.walk_speed_spin = QSpinBox()
        self.walk_speed_spin.setRange(10, 500)
        self.walk_speed_spin.setValue(pet.walk_speed)
        alayout.addWidget(QLabel("行走速度 (像素/秒):"))
        alayout.addWidget(self.walk_speed_spin)
        self.idle_spin = QSpinBox()
        self.idle_spin.setRange(5, 300)
        self.idle_spin.setValue(pet.idle_timeout)
        alayout.addWidget(QLabel("闲置触发时间 (秒):"))
        alayout.addWidget(self.idle_spin)
        alayout.addWidget(QLabel("宠物大小缩放:"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(50, 200)
        self.scale_slider.setValue(pet.scale_percent)
        self.scale_slider.setTickInterval(10)
        self.scale_slider.setTickPosition(QSlider.TicksBelow)
        self.scale_label = QLabel(f"{pet.scale_percent}%")
        self.scale_slider.valueChanged.connect(lambda v: self.scale_label.setText(f"{v}%"))
        alayout.addWidget(self.scale_slider)
        alayout.addWidget(self.scale_label)
        alayout.addWidget(QLabel("随机动画触发间隔 (秒):"))
        self.random_interval_spin = QSpinBox()
        self.random_interval_spin.setRange(10, 600)
        self.random_interval_spin.setValue(pet.random_interval)
        alayout.addWidget(self.random_interval_spin)
        anim.setLayout(alayout)
        tabs.addTab(anim, "动画")
        # 提醒（预留）
        remind = QWidget()
        rlayout = QVBoxLayout()
        self.cb_chime = QCheckBox("整点报时 (暂未实现)")
        self.cb_chime.setEnabled(False)
        rlayout.addWidget(self.cb_chime)
        remind.setLayout(rlayout)
        tabs.addTab(remind, "提醒")
        # 性能
        perf = QWidget()
        playout = QVBoxLayout()
        self.cb_game = QCheckBox("全屏游戏时自动暂停行走")
        self.cb_game.setChecked(True)
        self.cb_game.setEnabled(False)
        playout.addWidget(self.cb_game)
        perf.setLayout(playout)
        tabs.addTab(perf, "性能")
        layout.addWidget(tabs)
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)
        self.setLayout(layout)
    def change_tray_icon(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片文件", "", "Images (*.png *.ico *.jpg)")
        if file_path:
            icon = QIcon(file_path)
            if not icon.isNull():
                self.pet.tray.setIcon(icon)
                self.pet.settings.setValue("tray_icon", file_path)
                self.pet.settings.sync()
            else:
                QMessageBox.warning(self, "错误", "无法加载图片")
    def accept(self):
        self.pet.auto_start = self.cb_autostart.isChecked()
        self.pet.set_auto_start(self.pet.auto_start)
        self.pet.walk_speed = self.walk_speed_spin.value()
        self.pet.idle_timeout = self.idle_spin.value()
        new_scale = self.scale_slider.value()
        if new_scale != self.pet.scale_percent:
            self.pet.scale_percent = new_scale
            self.pet.scale = new_scale / 100.0
            self.pet.apply_scale()
            self.pet.update()
        self.pet.random_interval = self.random_interval_spin.value()
        self.pet.random_timer.start(self.pet.random_interval * 1000)
        self.pet.save_config()
        super().accept()

# ---------------------------- 主函数 ----------------------------
def main():
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    pet = DesktopPet()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()