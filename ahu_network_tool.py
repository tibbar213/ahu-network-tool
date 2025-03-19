import tkinter as tk
from tkinter import ttk, messagebox
import requests
import socket
import json
import os
import threading
import time
from PIL import Image, ImageTk, ImageDraw, ImageFont
import pystray
import re

class CampusNetworkGUI:
    # 校园网认证服务器地址和信息
    AUTH_SERVER = "172.16.253.3"
    AC_IP = "172.16.253.1"
    
    def __init__(self):
        # 初始化主窗口
        self.root = tk.Tk()
        self.root.title("校园网登录工具")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        
        # 定义基本颜色
        self.colors = {
            'primary': "#1976D2",   # 主色调
            'accent': "#03A9F4",    # 强调色
            'bg': "#F5F5F5",        # 背景色
            'text': "#212121",      # 文本色
            'success': "#4CAF50",   # 成功色
            'error': "#FF5252"      # 错误色
        }
        
        # 状态变量
        self.auto_start_var = tk.BooleanVar()
        self.keep_connected_var = tk.BooleanVar()
        self.connection_status = tk.StringVar(value="未连接")
        self.is_connected = False
        
        # 初始化线程
        self.keep_connected_thread = None
        
        # 初始化组件
        self.setup_theme()
        self.create_icon()
        self.create_widgets()
        self.load_config()
        self.create_tray_icon()
        
        # 事件绑定
        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)
        
        # 检查初始连接状态
        self.check_connection_status()
        
        # 启动定时更新状态
        self.start_status_update()
        
    def setup_theme(self):
        """设置GUI主题和样式"""
        style = ttk.Style()
        style.configure("TFrame", background=self.colors['bg'])
        style.configure("TLabel", background=self.colors['bg'], foreground=self.colors['text'], font=("微软雅黑", 10))
        style.configure("TButton", font=("微软雅黑", 10))
        style.configure("Header.TLabel", font=("微软雅黑", 16, "bold"), foreground=self.colors['primary'])
        style.configure("Status.TLabel", font=("微软雅黑", 12))
        style.configure("TCheckbutton", background=self.colors['bg'], font=("微软雅黑", 10))
        
        # 设置根窗口背景
        self.root.configure(bg=self.colors['bg'])
    
    def create_icon(self):
        """创建应用图标"""
        icon = Image.new('RGB', (64, 64), self.colors['primary'])
        draw = ImageDraw.Draw(icon)
        
        try:
            font = ImageFont.truetype("msyh.ttc", 36)
        except IOError:
            font = ImageFont.load_default()
            
        # 计算文本尺寸和位置
        try:
            # 尝试使用不同的API获取文本尺寸
            try:
                text_width, text_height = font.getsize("C")
            except AttributeError:
                try:
                    bbox = font.getbbox("C")
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except AttributeError:
                    text_width, text_height = 30, 30
                    
            position = ((64 - text_width) / 2, (64 - text_height) / 2 - 5)
            draw.text(position, "C", font=font, fill="#FFFFFF")
        except Exception:
            # 如果文本渲染失败，创建一个简单的圆形
            draw.ellipse((10, 10, 54, 54), fill="#FFFFFF")
        
        self.app_icon = icon
        self.root.iconphoto(True, ImageTk.PhotoImage(self.app_icon))
        
    def create_widgets(self):
        """创建GUI组件"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header_frame, text="校园网登录工具", style="Header.TLabel").pack()
        
        # 登录信息区域
        self._create_login_section(main_frame)
        
        # 按钮区域
        self._create_button_section(main_frame)
        
        # 状态区域
        self._create_status_section(main_frame)
        
        # 选项区域
        self._create_options_section(main_frame)
        
        # 底部信息
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        ttk.Label(footer_frame, text="© 2025 校园网登录工具", font=("微软雅黑", 8)).pack(side=tk.RIGHT)
    
    def _create_login_section(self, parent):
        """创建登录信息区域"""
        input_frame = ttk.LabelFrame(parent, text="登录信息")
        input_frame.pack(fill=tk.X, pady=10)
        
        # 账号输入框
        account_frame = ttk.Frame(input_frame)
        account_frame.pack(fill=tk.X, pady=5, padx=10)
        ttk.Label(account_frame, text="账号:").pack(side=tk.LEFT, padx=(0, 10))
        self.account_entry = ttk.Entry(account_frame, width=30)
        self.account_entry.pack(side=tk.RIGHT, padx=5)
        
        # 密码输入框
        password_frame = ttk.Frame(input_frame)
        password_frame.pack(fill=tk.X, pady=5, padx=10)
        ttk.Label(password_frame, text="密码:").pack(side=tk.LEFT, padx=(0, 10))
        self.password_entry = ttk.Entry(password_frame, show="*", width=30)
        self.password_entry.pack(side=tk.RIGHT, padx=5)
    
    def _create_button_section(self, parent):
        """创建按钮区域"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=20)
        
        self.login_button = ttk.Button(button_frame, text="登录", command=self.login, width=15)
        self.login_button.pack(side=tk.LEFT, padx=20)
        
        self.logout_button = ttk.Button(button_frame, text="登出", command=self.logout, width=15)
        self.logout_button.pack(side=tk.RIGHT, padx=20)
    
    def _create_status_section(self, parent):
        """创建状态显示区域"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(status_frame, text="当前状态: ").pack(side=tk.LEFT)
        
        # 状态指示器（彩色圆点）
        self.status_indicator = tk.Canvas(status_frame, width=15, height=15, 
                                          bg=self.colors['bg'], highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=5)
        self.status_dot = self.status_indicator.create_oval(2, 2, 13, 13, 
                                                           fill=self.colors['error'], outline="")
        
        ttk.Label(status_frame, textvariable=self.connection_status, 
                 style="Status.TLabel").pack(side=tk.LEFT)
    
    def _create_options_section(self, parent):
        """创建选项区域"""
        options_frame = ttk.LabelFrame(parent, text="选项")
        options_frame.pack(fill=tk.X, pady=10)
        
        # 开机自启复选框
        self.auto_start_checkbox = ttk.Checkbutton(
            options_frame, 
            text="开机自启", 
            variable=self.auto_start_var,
            command=self.on_auto_start_changed
        )
        self.auto_start_checkbox.pack(pady=10, padx=10, anchor=tk.W)
        
        # 保持连接复选框
        self.keep_connected_checkbox = ttk.Checkbutton(
            options_frame, 
            text="保持连接", 
            variable=self.keep_connected_var,
            command=self.on_keep_connected_changed
        )
        self.keep_connected_checkbox.pack(pady=10, padx=10, anchor=tk.W)
    
    def create_tray_icon(self):
        """创建系统托盘图标"""
        menu = (
            pystray.MenuItem("显示", self.show_window),
            pystray.MenuItem("开机自启", self.toggle_auto_start, 
                           checked=lambda item: self.auto_start_var.get()),
            pystray.MenuItem("保持连接", self.toggle_keep_connected, 
                           checked=lambda item: self.keep_connected_var.get()),
            pystray.MenuItem("退出", self.quit_app)
        )
        
        self.icon = pystray.Icon(
            "campus_network",
            self.app_icon,
            "校园网登录工具",
            menu
        )
        
        # 添加单击事件
        self.icon.on_click = self.on_icon_click
        
        # 在新线程中运行图标
        threading.Thread(target=self.icon.run, daemon=True).start()
    
    def update_tray_menu(self):
        """更新托盘菜单状态"""
        def update_menu():
            menu = (
                pystray.MenuItem("显示", self.show_window),
                pystray.MenuItem("开机自启", self.toggle_auto_start, 
                               checked=lambda item: self.auto_start_var.get()),
                pystray.MenuItem("保持连接", self.toggle_keep_connected, 
                               checked=lambda item: self.keep_connected_var.get()),
                pystray.MenuItem("退出", self.quit_app)
            )
            self.icon.menu = menu
            self.icon.update_menu()
        
        # 在主线程中更新菜单
        self.root.after(0, update_menu)
    
    def check_connection_status(self):
        """检查网络连接状态"""
        if self.can_connect():
            self.is_connected = True
            self.connection_status.set("已连接")
            self.status_indicator.itemconfig(self.status_dot, fill=self.colors['success'])
            if hasattr(self, 'icon'):
                self.icon.title = "校园网登录工具 - 已连接"
        else:
            self.is_connected = False
            self.connection_status.set("未连接")
            self.status_indicator.itemconfig(self.status_dot, fill=self.colors['error'])
            if hasattr(self, 'icon'):
                self.icon.title = "校园网登录工具 - 未连接"
    
    def get_host_ip(self):
        """获取本机IP地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def can_connect(self):
        """测试网络连接状态"""
        try:
            response = requests.get("http://www.baidu.com", timeout=5)
            return bool(re.search(r'STATUS OK', response.text))
        except Exception:
            return False
    
    def _get_auth_header(self):
        """获取认证请求头"""
        return {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Connection": "keep-alive",
            "Cookie": "PHPSESSID=djndiqfdhmebmpaa4j0u2d3uv1",
            "Referer": f"http://{self.AUTH_SERVER}/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Host": f"{self.AUTH_SERVER}:801"
        }
    
    def login(self):
        """登录校园网"""
        account = self.account_entry.get()
        password = self.password_entry.get()
        
        if not account or not password:
            messagebox.showerror("错误", "请输入账号和密码")
            return
            
        # 开始登录尝试
        self._try_login(account, password, 0)
    
    def _try_login(self, account, password, retry_count):
        """尝试登录，失败时自动重试"""
        ip = self.get_host_ip()
        url = f"http://{self.AUTH_SERVER}:801/eportal/?c=Portal&a=login&callback=dr1003&login_method=1&user_account={account}" \
              f"&user_password={password}%20&wlan_user_ip={ip}&wlan_user_ipv6=&wlan_user_mac=000000000000&wlan_ac_ip={self.AC_IP}" \
              f"&wlan_ac_name=&jsVersion=3.3.2&v=1709"
              
        try:
            requests.post(url, headers=self._get_auth_header())
            # 等待1秒后检查状态
            self.root.after(1000, lambda: self._check_login_result(account, password, retry_count))
        except Exception as e:
            self._handle_login_error(e, account, password, retry_count)
    
    def _check_login_result(self, account, password, retry_count):
        """检查登录结果"""
        if self.is_connected:
            self.save_config()
            messagebox.showinfo("成功", "登录成功！")
        else:
            self._handle_login_error("登录失败", account, password, retry_count)
    
    def _handle_login_error(self, error, account, password, retry_count):
        """处理登录错误"""
        if retry_count < 5:  # 如果重试次数小于5次
            retry_count += 1
            # 等待2秒后重试
            self.root.after(2000, lambda: self._try_login(account, password, retry_count))
        else:
            messagebox.showerror("错误", f"登录失败，请检查网络连接{str(error)}")
            self.check_connection_status()
    
    def logout(self):
        """登出校园网"""
        ip = self.get_host_ip()
        url = f"http://{self.AUTH_SERVER}:801/eportal/?c=Portal&a=logout&callback=dr1004&login_method=1&user_account=drcom" \
              f"&user_password=123&ac_logout=0&register_mode=1&wlan_user_ip={ip}&wlan_user_ipv6=&wlan_vlan_id=0" \
              f"&wlan_user_mac=000000000000&wlan_ac_ip={self.AC_IP}&wlan_ac_name=&jsVersion=3.3.2&v=4080"
              
        try:
            requests.post(url, headers=self._get_auth_header())
            # 等待1秒后检查状态
            self.root.after(1000, self.check_connection_status)
            messagebox.showinfo("成功", "已登出！")
        except Exception as e:
            messagebox.showerror("错误", f"登出出错：{str(e)}")
            self.check_connection_status()
    
    def on_auto_start_changed(self):
        """GUI复选框：开机自启状态变更回调"""
        if self.auto_start_var.get():
            self.setup_auto_start()
        else:
            self.remove_auto_start()
        self.save_config()
        self.update_tray_menu()
    
    def on_keep_connected_changed(self):
        """GUI复选框：保持连接状态变更回调"""
        if self.keep_connected_var.get():
            self.start_keep_connected()
        else:
            self.stop_keep_connected()
        self.save_config()
        self.update_tray_menu()
    
    def toggle_auto_start(self, icon=None, item=None):
        """托盘菜单：切换开机自启状态"""
        self.auto_start_var.set(not self.auto_start_var.get())
        self.on_auto_start_changed()
    
    def toggle_keep_connected(self, icon=None, item=None):
        """托盘菜单：切换保持连接状态"""
        self.keep_connected_var.set(not self.keep_connected_var.get())
        self.on_keep_connected_changed()
    
    def setup_auto_start(self):
        """设置开机自启"""
        try:
            startup_folder = os.path.join(os.getenv('APPDATA'), 
                                         'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
            script_path = os.path.abspath(__file__)
            batch_path = os.path.join(startup_folder, 'CampusNetworkLogin.bat')
            
            batch_content = f'@echo off\npythonw "{script_path}"\n'
            
            with open(batch_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)
        except Exception as e:
            print(f"设置开机自启失败：{str(e)}")
    
    def remove_auto_start(self):
        """取消开机自启"""
        try:
            startup_folder = os.path.join(os.getenv('APPDATA'), 
                                         'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
            batch_path = os.path.join(startup_folder, 'CampusNetworkLogin.bat')
            if os.path.exists(batch_path):
                os.remove(batch_path)
        except Exception as e:
            print(f"取消开机自启失败：{str(e)}")
    
    def start_keep_connected(self):
        """启动保持连接线程"""
        if not self.keep_connected_thread or not self.keep_connected_thread.is_alive():
            self.keep_connected_thread = threading.Thread(target=self.keep_connected_loop, daemon=True)
            self.keep_connected_thread.start()
    
    def stop_keep_connected(self):
        """停止保持连接线程"""
        if self.keep_connected_thread and self.keep_connected_thread.is_alive():
            self.keep_connected_thread = None
    
    def keep_connected_loop(self):
        """保持连接的后台线程"""
        while self.keep_connected_var.get():
            if not self.can_connect():
                self._auto_login()
            time.sleep(30)  # 每30秒检查一次
    
    def _auto_login(self):
        """自动登录（无弹窗提示）"""
        account = self.account_entry.get()
        password = self.password_entry.get()
        
        if not account or not password:
            return
            
        try:
            ip = self.get_host_ip()
            url = f"http://{self.AUTH_SERVER}:801/eportal/?c=Portal&a=login&callback=dr1003&login_method=1&user_account={account}" \
                  f"&user_password={password}%20&wlan_user_ip={ip}&wlan_user_ipv6=&wlan_user_mac=000000000000&wlan_ac_ip={self.AC_IP}" \
                  f"&wlan_ac_name=&jsVersion=3.3.2&v=1709"
                  
            requests.post(url, headers=self._get_auth_header())
            
            # 如果连接成功，更新状态
            if self.can_connect():
                self.root.after(0, self.check_connection_status)
        except Exception:
            pass  # 忽略错误
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.account_entry.insert(0, config.get('account', ''))
                    self.password_entry.insert(0, config.get('password', ''))
                    self.auto_start_var.set(config.get('auto_start', False))
                    self.keep_connected_var.set(config.get('keep_connected', False))
                    
                    # 如果设置了保持连接，启动相应线程
                    if self.keep_connected_var.get():
                        self.start_keep_connected()
        except Exception as e:
            print(f"加载配置失败：{str(e)}")
    
    def save_config(self):
        """保存配置到文件"""
        try:
            config = {
                'account': self.account_entry.get(),
                'password': self.password_entry.get(),
                'auto_start': self.auto_start_var.get(),
                'keep_connected': self.keep_connected_var.get()
            }
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置失败：{str(e)}")
    
    def hide_window(self):
        """隐藏主窗口"""
        self.root.withdraw()
    
    def show_window(self, icon=None):
        """显示主窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def on_icon_click(self, icon, event):
        """托盘图标点击事件"""
        if event.button == 'left':
            self.show_window()
    
    def quit_app(self, icon=None):
        """退出应用"""
        if hasattr(self, 'icon'):
            self.icon.stop()
        self.root.destroy()
    
    def run(self):
        """运行应用"""
        # 如果配置了开机自启，则启动时隐藏窗口
        if self.auto_start_var.get():
            self.hide_window()
        self.root.mainloop()
    
    def start_status_update(self):
        """启动定时更新状态"""
        self.check_connection_status()
        # 每30秒更新一次状态
        self.root.after(30000, self.start_status_update)


if __name__ == "__main__":
    app = CampusNetworkGUI()
    app.run() 