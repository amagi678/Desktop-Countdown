import tkinter as tk
from tkinter import simpledialog, messagebox, colorchooser
import datetime
import json
import os
import sys
import winreg


class CountdownApp:
    def __init__(self, root):
        self.root = root
        self.root.title("桌面倒计时")
        self.root.overrideredirect(True)  # 隐藏标题栏
        self.root.attributes('-topmost', True)  # 置顶

        # 加载设置
        self.load_settings()

        # 初始化UI
        self.setup_ui()

        # 鼠标拖动相关变量
        self._offsetx = 0
        self._offsety = 0
        self._dragging = False
        self._resizing = False

        # 开始倒计时
        self.update_countdown()

        # 设置开机自启动(根据设置)
        self.update_auto_start()

    def load_settings(self):
        # 默认设置
        self.settings = {
            "target_date": "2026-01-01 00:00:00",
            "custom_text": "距离2026年1月1日还有",
            "position": (100, 100),
            "size": (200, 100),
            "bg_color": "#333333",
            "fg_color": "#FFFFFF",
            "transparent": False,
            "auto_start": True,  # 新增：开机自启动开关
            "title_font_size": 10,  # 新增：标题字体大小
            "text_font_size": 10,  # 新增：文本字体大小
            "countdown_font_size": 12  # 新增：倒计时字体大小
        }

        # 尝试加载保存的设置
        try:
            if os.path.exists("countdown_settings.json"):
                with open("countdown_settings.json", "r") as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
        except:
            pass

        # 应用透明设置
        if self.settings["transparent"]:
            self.root.wm_attributes('-transparentcolor', self.settings["bg_color"])

    def save_settings(self):
        with open("countdown_settings.json", "w") as f:
            json.dump(self.settings, f)

    def setup_ui(self):
        # 设置窗口初始大小和位置
        self.root.geometry(
            f"{self.settings['size'][0]}x{self.settings['size'][1]}+{self.settings['position'][0]}+{self.settings['position'][1]}")

        # 主框架
        self.main_frame = tk.Frame(self.root, bg=self.settings["bg_color"], bd=2, relief=tk.RAISED)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题栏框架 - 用于拖动
        self.title_frame = tk.Frame(self.main_frame, bg=self.settings["bg_color"])
        self.title_frame.pack(fill=tk.X, padx=5, pady=2)

        # 标题标签
        self.title_label = tk.Label(
            self.title_frame,
            text="倒计时",
            bg=self.settings["bg_color"],
            fg=self.settings["fg_color"],
            font=("微软雅黑", self.settings["title_font_size"])
        )
        self.title_label.pack(side=tk.LEFT)

        # 设置按钮
        self.settings_btn = tk.Label(
            self.title_frame,
            text="⚙",
            bg=self.settings["bg_color"],
            fg=self.settings["fg_color"],
            font=("Arial", self.settings["title_font_size"]),
            cursor="hand2"
        )
        self.settings_btn.pack(side=tk.RIGHT)
        self.settings_btn.bind("<Button-1>", self.show_settings_menu)

        # 自定义文本标签
        self.text_label = tk.Label(
            self.main_frame,
            text=self.settings["custom_text"],
            bg=self.settings["bg_color"],
            fg=self.settings["fg_color"],
            font=("微软雅黑", self.settings["text_font_size"])
        )
        self.text_label.pack(pady=(5, 0))

        # 倒计时标签
        self.countdown_label = tk.Label(
            self.main_frame,
            text="",
            bg=self.settings["bg_color"],
            fg=self.settings["fg_color"],
            font=("微软雅黑", self.settings["countdown_font_size"], "bold")
        )
        self.countdown_label.pack(pady=(0, 5))

        # 设置菜单
        self.settings_menu = tk.Menu(self.root, tearoff=0)
        self.settings_menu.add_command(label="更改目标时间", command=self.change_target_date)
        self.settings_menu.add_command(label="更改显示文字", command=self.change_custom_text)
        self.settings_menu.add_command(label="更改颜色", command=self.change_colors_with_picker)
        self.settings_menu.add_command(label="切换透明", command=self.toggle_transparent)
        self.settings_menu.add_command(label="调整窗口大小", command=self.adjust_window_size)
        self.settings_menu.add_command(label="调整字体大小", command=self.adjust_font_size)
        self.settings_menu.add_checkbutton(label="关闭开机自启动", command=self.toggle_auto_start,
                                           variable=tk.BooleanVar(value=self.settings["auto_start"]))
        self.settings_menu.add_command(label="关于软件", command=self.show_about)
        self.settings_menu.add_separator()
        self.settings_menu.add_command(label="退出", command=self.root.quit)

        # 绑定鼠标事件 - 拖动
        self.title_frame.bind("<Button-1>", self.start_move)
        self.title_frame.bind("<B1-Motion>", self.on_move)
        self.title_frame.bind("<ButtonRelease-1>", self.stop_move)

        # 绑定窗口大小调整事件
        self.resize_handle = tk.Frame(self.main_frame, bg=self.settings["bg_color"], cursor="sizing", height=8)
        self.resize_handle.pack(side=tk.BOTTOM, fill=tk.X)
        self.resize_handle.bind("<Button-1>", self.start_resize)
        self.resize_handle.bind("<B1-Motion>", self.on_resize_drag)
        self.resize_handle.bind("<ButtonRelease-1>", self.stop_resize)

        # 窗口边缘调整大小
        self.root.bind("<Button-1>", self.start_edge_resize)
        self.root.bind("<B1-Motion>", self.on_edge_resize)
        self.root.bind("<ButtonRelease-1>", self.stop_edge_resize)

    def toggle_transparent(self):
        self.settings["transparent"] = not self.settings["transparent"]
        if self.settings["transparent"]:
            self.root.wm_attributes('-transparentcolor', self.settings["bg_color"])
        else:
            self.root.wm_attributes('-transparentcolor', '')
        self.save_settings()

    def toggle_auto_start(self):
        self.settings["auto_start"] = not self.settings["auto_start"]
        self.update_auto_start()
        self.save_settings()

    def show_about(self):
        about_info = """作者：小盆友真聪明
    B站UID：382061364
    GitHub：https://github.com/amagi678/Desktop-Countdown

    版本：1.0
    这是一个桌面倒计时悬浮窗程序"""
        messagebox.showinfo("关于软件", about_info)

    def update_auto_start(self):
        """更新开机自启动设置"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )

            if self.settings["auto_start"]:
                # 获取当前脚本的路径
                if getattr(sys, 'frozen', False):
                    app_path = sys.executable
                else:
                    app_path = os.path.abspath(__file__)
                    if not app_path.endswith('.pyw'):
                        app_path = app_path[:-3] + '.pyw'

                winreg.SetValueEx(key, "DesktopCountdown", 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, "DesktopCountdown")
                except WindowsError:
                    pass

            winreg.CloseKey(key)
        except Exception as e:
            print(f"设置开机自启动失败: {e}")

    def adjust_window_size(self):
        """调整窗口大小"""
        size_window = tk.Toplevel(self.root)
        size_window.title("调整窗口大小")
        size_window.attributes('-topmost', True)

        tk.Label(size_window, text="宽度:").grid(row=0, column=0, padx=5, pady=5)
        width_entry = tk.Entry(size_window)
        width_entry.insert(0, str(self.settings["size"][0]))
        width_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(size_window, text="高度:").grid(row=1, column=0, padx=5, pady=5)
        height_entry = tk.Entry(size_window)
        height_entry.insert(0, str(self.settings["size"][1]))
        height_entry.grid(row=1, column=1, padx=5, pady=5)

        def apply_size():
            try:
                new_width = int(width_entry.get())
                new_height = int(height_entry.get())

                # 最小尺寸限制
                new_width = max(new_width, 150)
                new_height = max(new_height, 80)

                self.settings["size"] = (new_width, new_height)
                self.root.geometry(f"{new_width}x{new_height}")
                self.save_settings()
                size_window.destroy()
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")

        tk.Button(size_window, text="应用", command=apply_size).grid(row=2, column=0, columnspan=2, pady=5)

    def adjust_font_size(self):
        """调整字体大小"""
        font_window = tk.Toplevel(self.root)
        font_window.title("调整字体大小")
        font_window.attributes('-topmost', True)

        tk.Label(font_window, text="标题字体大小:").grid(row=0, column=0, padx=5, pady=5)
        title_font_entry = tk.Entry(font_window)
        title_font_entry.insert(0, str(self.settings["title_font_size"]))
        title_font_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(font_window, text="文本字体大小:").grid(row=1, column=0, padx=5, pady=5)
        text_font_entry = tk.Entry(font_window)
        text_font_entry.insert(0, str(self.settings["text_font_size"]))
        text_font_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(font_window, text="倒计时字体大小:").grid(row=2, column=0, padx=5, pady=5)
        countdown_font_entry = tk.Entry(font_window)
        countdown_font_entry.insert(0, str(self.settings["countdown_font_size"]))
        countdown_font_entry.grid(row=2, column=1, padx=5, pady=5)

        def apply_font_size():
            try:
                self.settings["title_font_size"] = int(title_font_entry.get())
                self.settings["text_font_size"] = int(text_font_entry.get())
                self.settings["countdown_font_size"] = int(countdown_font_entry.get())

                # 应用新字体大小
                self.title_label.config(font=("微软雅黑", self.settings["title_font_size"]))
                self.settings_btn.config(font=("Arial", self.settings["title_font_size"]))
                self.text_label.config(font=("微软雅黑", self.settings["text_font_size"]))
                self.countdown_label.config(font=("微软雅黑", self.settings["countdown_font_size"], "bold"))

                self.save_settings()
                font_window.destroy()
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")

        tk.Button(font_window, text="应用", command=apply_font_size).grid(row=3, column=0, columnspan=2, pady=5)

    def start_move(self, event):
        self._offsetx = event.x
        self._offsety = event.y
        self._dragging = True

    def on_move(self, event):
        if self._dragging:
            x = self.root.winfo_pointerx() - self._offsetx
            y = self.root.winfo_pointery() - self._offsety
            self.root.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        self._dragging = False
        self.settings["position"] = (self.root.winfo_x(), self.root.winfo_y())
        self.save_settings()

    def start_resize(self, event):
        self._resizing = True
        self._start_width = self.root.winfo_width()
        self._start_height = self.root.winfo_height()
        self._start_x = event.x_root
        self._start_y = event.y_root

    def on_resize_drag(self, event):
        if self._resizing:
            new_width = self._start_width
            new_height = self._start_height + (event.y_root - self._start_y)
            new_height = max(new_height, 80)  # 最小高度
            self.root.geometry(f"{new_width}x{new_height}")

    def stop_resize(self, event):
        self._resizing = False
        self.settings["size"] = (self.root.winfo_width(), self.root.winfo_height())
        self.save_settings()

    def start_edge_resize(self, event):
        # 检查是否点击了窗口边缘
        if event.x < 5:  # 左边缘
            self._resize_edge = "left"
        elif event.x > self.root.winfo_width() - 5:  # 右边缘
            self._resize_edge = "right"
        else:
            self._resize_edge = None
            return

        self._resizing = True
        self._start_width = self.root.winfo_width()
        self._start_x = event.x_root

    def on_edge_resize(self, event):
        if not self._resizing or not hasattr(self, '_resize_edge'):
            return

        if self._resize_edge == "left":
            # 左侧调整
            delta = event.x_root - self._start_x
            new_width = self._start_width - delta
            new_x = self.root.winfo_x() + delta
        elif self._resize_edge == "right":
            # 右侧调整
            delta = event.x_root - self._start_x
            new_width = self._start_width + delta
            new_x = self.root.winfo_x()
        else:
            return

        new_width = max(new_width, 150)  # 最小宽度
        self.root.geometry(f"{new_width}x{self.root.winfo_height()}+{new_x}+{self.root.winfo_y()}")

    def stop_edge_resize(self, event):
        if hasattr(self, '_resize_edge'):
            self._resizing = False
            self.settings["size"] = (self.root.winfo_width(), self.root.winfo_height())
            self.settings["position"] = (self.root.winfo_x(), self.root.winfo_y())
            self.save_settings()

    def show_settings_menu(self, event=None):
        try:
            x = self.root.winfo_rootx() + self.settings_btn.winfo_x() + self.settings_btn.winfo_width()
            y = self.root.winfo_rooty() + self.settings_btn.winfo_y() + self.settings_btn.winfo_height()
            self.settings_menu.tk_popup(x, y)
        finally:
            self.settings_menu.grab_release()

    def change_target_date(self):
        new_date = simpledialog.askstring(
            "更改目标时间",
            "请输入目标时间 (YYYY-MM-DD HH:MM:SS):",
            initialvalue=self.settings["target_date"]
        )
        if new_date:
            try:
                datetime.datetime.strptime(new_date, "%Y-%m-%d %H:%M:%S")
                self.settings["target_date"] = new_date
                self.save_settings()
            except ValueError:
                messagebox.showerror("错误", "日期格式不正确，请使用 YYYY-MM-DD HH:MM:SS 格式")

    def change_custom_text(self):
        new_text = simpledialog.askstring(
            "更改显示文字",
            "请输入要显示的文字:",
            initialvalue=self.settings["custom_text"]
        )
        if new_text is not None:
            self.settings["custom_text"] = new_text
            self.text_label.config(text=new_text)
            self.save_settings()

    def change_colors_with_picker(self):
        # 选择背景颜色
        bg_color = colorchooser.askcolor(
            title="选择背景颜色",
            initialcolor=self.settings["bg_color"]
        )
        if bg_color[1]:
            old_bg = self.settings["bg_color"]
            self.settings["bg_color"] = bg_color[1]

            # 如果当前是透明状态，需要更新透明色
            if self.settings["transparent"]:
                self.root.wm_attributes('-transparentcolor', self.settings["bg_color"])

        # 选择文字颜色
        fg_color = colorchooser.askcolor(
            title="选择文字颜色",
            initialcolor=self.settings["fg_color"]
        )
        if fg_color[1]:
            self.settings["fg_color"] = fg_color[1]

        # 应用新颜色
        self.main_frame.config(bg=self.settings["bg_color"])
        self.title_frame.config(bg=self.settings["bg_color"])
        self.title_label.config(
            bg=self.settings["bg_color"],
            fg=self.settings["fg_color"]
        )
        self.settings_btn.config(
            bg=self.settings["bg_color"],
            fg=self.settings["fg_color"]
        )
        self.text_label.config(
            bg=self.settings["bg_color"],
            fg=self.settings["fg_color"]
        )
        self.countdown_label.config(
            bg=self.settings["bg_color"],
            fg=self.settings["fg_color"]
        )
        self.resize_handle.config(bg=self.settings["bg_color"])

        self.save_settings()

    def update_countdown(self):
        try:
            target = datetime.datetime.strptime(self.settings["target_date"], "%Y-%m-%d %H:%M:%S")
            now = datetime.datetime.now()

            if now < target:
                delta = target - now
                days = delta.days
                hours, remainder = divmod(delta.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                countdown_text = f"{days}天 {hours:02d}小时 {minutes:02d}分 {seconds:02d}秒"
                self.countdown_label.config(text=countdown_text)
            else:
                self.countdown_label.config(text="时间已到！")
        except:
            self.countdown_label.config(text="日期格式错误")

        # 每秒更新一次
        self.root.after(1000, self.update_countdown)


if __name__ == "__main__":
    root = tk.Tk()
    app = CountdownApp(root)
    root.mainloop()
