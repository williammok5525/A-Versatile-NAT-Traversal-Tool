import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import json
import os
from datetime import datetime
import webbrowser
from tunnel_core import TunnelManager
from file_server import FileServer
from utils import *

class NetworkTunnelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多功能内网穿透工具 v2.0")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 设置主题
        style = ttk.Style()
        style.theme_use('clam')
        
        # 核心组件
        self.tunnel_manager = TunnelManager(self.log_message)
        self.file_server = FileServer(self.log_message)
        self.config = self.load_config()
        
        # 创建界面
        self.create_menu()
        self.create_notebook()
        self.create_status_bar()
        
        # 加载配置
        self.load_settings()
        
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="保存配置", command=self.save_settings)
        file_menu.add_command(label="加载配置", command=self.load_settings)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        
        # 工具菜单
        tool_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tool_menu)
        tool_menu.add_command(label="获取本机IP", command=self.show_local_ip)
        tool_menu.add_command(label="获取公网IP", command=self.show_public_ip)
        tool_menu.add_command(label="端口扫描", command=self.open_port_scanner)
        tool_menu.add_command(label="测试延迟", command=self.test_latency)
        tool_menu.add_separator()
        tool_menu.add_command(label="二维码生成", command=self.open_qr_generator)
        tool_menu.add_command(label="流量监控", command=self.open_traffic_monitor)
        tool_menu.add_command(label="系统信息", command=self.open_system_info)

        # 添加对应的方法:

        def open_qr_generator(self):
            """打开二维码生成器"""
            from advanced_tools import QRCodeGenerator
            QRCodeGenerator(self.root)

        def open_traffic_monitor(self):
            """打开流量监控"""
            from advanced_tools import TrafficMonitor
            TrafficMonitor(self.root)

        def open_system_info(self):
            """打开系统信息"""
            from advanced_tools import SystemInfo
            SystemInfo(self.root)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用教程", command=self.show_tutorial)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def create_notebook(self):
        """创建选项卡"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 各个功能页面
        self.create_frp_page()
        self.create_simple_tunnel_page()
        self.create_file_share_page()
        self.create_game_page()
        self.create_remote_desktop_page()
        self.create_settings_page()
        self.create_log_page()
    
    def create_frp_page(self):
        """FRP穿透页面"""
        frp_frame = ttk.Frame(self.notebook)
        self.notebook.add(frp_frame, text="FRP穿透")
        
        # 服务器配置区
        server_group = ttk.LabelFrame(frp_frame, text="服务器配置", padding=10)
        server_group.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(server_group, text="服务器地址:").grid(row=0, column=0, sticky="w", pady=2)
        self.frp_server_addr = ttk.Entry(server_group, width=30)
        self.frp_server_addr.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(server_group, text="服务器端口:").grid(row=1, column=0, sticky="w", pady=2)
        self.frp_server_port = ttk.Entry(server_group, width=30)
        self.frp_server_port.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(server_group, text="Token:").grid(row=2, column=0, sticky="w", pady=2)
        self.frp_token = ttk.Entry(server_group, width=30, show="*")
        self.frp_token.grid(row=2, column=1, padx=5, pady=2)
        
        # 映射配置区
        mapping_group = ttk.LabelFrame(frp_frame, text="端口映射", padding=10)
        mapping_group.pack(fill="x", padx=10, pady=5)
        
        # 映射列表
        list_frame = ttk.Frame(mapping_group)
        list_frame.pack(fill="both", expand=True)
        
        self.mapping_tree = ttk.Treeview(list_frame, columns=("name", "type", "local", "remote"), 
                                         height=6, show="headings")
        self.mapping_tree.heading("name", text="名称")
        self.mapping_tree.heading("type", text="类型")
        self.mapping_tree.heading("local", text="本地端口")
        self.mapping_tree.heading("remote", text="远程端口")
        
        self.mapping_tree.column("name", width=100)
        self.mapping_tree.column("type", width=80)
        self.mapping_tree.column("local", width=100)
        self.mapping_tree.column("remote", width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.mapping_tree.yview)
        self.mapping_tree.configure(yscrollcommand=scrollbar.set)
        
        self.mapping_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 添加映射按钮
        btn_frame = ttk.Frame(mapping_group)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="添加映射", command=self.add_mapping).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="删除映射", command=self.delete_mapping).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="编辑映射", command=self.edit_mapping).pack(side="left", padx=2)
        
        # 控制按钮
        control_frame = ttk.Frame(frp_frame)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        self.frp_start_btn = ttk.Button(control_frame, text="启动FRP", 
                                        command=self.start_frp, width=15)
        self.frp_start_btn.pack(side="left", padx=5)
        
        self.frp_stop_btn = ttk.Button(control_frame, text="停止FRP", 
                                       command=self.stop_frp, width=15, state="disabled")
        self.frp_stop_btn.pack(side="left", padx=5)
        
        # 状态显示
        status_frame = ttk.LabelFrame(frp_frame, text="连接状态", padding=10)
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.frp_status_text = scrolledtext.ScrolledText(status_frame, height=8)
        self.frp_status_text.pack(fill="both", expand=True)
    
    def create_simple_tunnel_page(self):
        """简单穿透页面"""
        tunnel_frame = ttk.Frame(self.notebook)
        self.notebook.add(tunnel_frame, text="简单穿透")
        
        # 配置区
        config_group = ttk.LabelFrame(tunnel_frame, text="穿透配置", padding=10)
        config_group.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(config_group, text="监听端口:").grid(row=0, column=0, sticky="w", pady=2)
        self.tunnel_listen_port = ttk.Entry(config_group, width=20)
        self.tunnel_listen_port.insert(0, "8080")
        self.tunnel_listen_port.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(config_group, text="目标地址:").grid(row=1, column=0, sticky="w", pady=2)
        self.tunnel_target_host = ttk.Entry(config_group, width=20)
        self.tunnel_target_host.insert(0, "127.0.0.1")
        self.tunnel_target_host.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(config_group, text="目标端口:").grid(row=2, column=0, sticky="w", pady=2)
        self.tunnel_target_port = ttk.Entry(config_group, width=20)
        self.tunnel_target_port.insert(0, "80")
        self.tunnel_target_port.grid(row=2, column=1, padx=5, pady=2)
        
        # 协议选择
        ttk.Label(config_group, text="协议类型:").grid(row=3, column=0, sticky="w", pady=2)
        self.tunnel_protocol = ttk.Combobox(config_group, values=["TCP", "UDP"], width=18)
        self.tunnel_protocol.set("TCP")
        self.tunnel_protocol.grid(row=3, column=1, padx=5, pady=2)
        
        # 加密选项
        self.tunnel_encrypt = tk.BooleanVar()
        ttk.Checkbutton(config_group, text="启用加密传输", 
                       variable=self.tunnel_encrypt).grid(row=4, column=0, columnspan=2, pady=5)
        
        # 控制按钮
        control_frame = ttk.Frame(tunnel_frame)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        self.tunnel_start_btn = ttk.Button(control_frame, text="启动穿透", 
                                          command=self.start_simple_tunnel, width=15)
        self.tunnel_start_btn.pack(side="left", padx=5)
        
        self.tunnel_stop_btn = ttk.Button(control_frame, text="停止穿透", 
                                         command=self.stop_simple_tunnel, width=15, state="disabled")
        self.tunnel_stop_btn.pack(side="left", padx=5)
        
        # 连接统计
        stats_group = ttk.LabelFrame(tunnel_frame, text="连接统计", padding=10)
        stats_group.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tunnel_stats = tk.Text(stats_group, height=10)
        self.tunnel_stats.pack(fill="both", expand=True)
    
    def create_file_share_page(self):
        """文件分享页面"""
        file_frame = ttk.Frame(self.notebook)
        self.notebook.add(file_frame, text="文件分享")
        
        # 分享设置
        share_group = ttk.LabelFrame(file_frame, text="分享设置", padding=10)
        share_group.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(share_group, text="分享目录:").grid(row=0, column=0, sticky="w", pady=2)
        self.share_dir = ttk.Entry(share_group, width=40)
        self.share_dir.grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(share_group, text="浏览", 
                  command=self.browse_share_dir).grid(row=0, column=2, padx=5)
        
        ttk.Label(share_group, text="服务端口:").grid(row=1, column=0, sticky="w", pady=2)
        self.share_port = ttk.Entry(share_group, width=40)
        self.share_port.insert(0, "8000")
        self.share_port.grid(row=1, column=1, padx=5, pady=2)
        
        # 访问控制
        ttk.Label(share_group, text="访问密码:").grid(row=2, column=0, sticky="w", pady=2)
        self.share_password = ttk.Entry(share_group, width=40, show="*")
        self.share_password.grid(row=2, column=1, padx=5, pady=2)
        
        self.share_readonly = tk.BooleanVar(value=True)
        ttk.Checkbutton(share_group, text="只读模式", 
                       variable=self.share_readonly).grid(row=3, column=0, columnspan=2, pady=5)
        
        # 控制按钮
        control_frame = ttk.Frame(file_frame)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        self.file_start_btn = ttk.Button(control_frame, text="启动文件服务", 
                                        command=self.start_file_server, width=15)
        self.file_start_btn.pack(side="left", padx=5)
        
        self.file_stop_btn = ttk.Button(control_frame, text="停止文件服务", 
                                       command=self.stop_file_server, width=15, state="disabled")
        self.file_stop_btn.pack(side="left", padx=5)
        
        ttk.Button(control_frame, text="打开浏览器", 
                  command=self.open_file_browser, width=15).pack(side="left", padx=5)
        
        # 访问日志
        log_group = ttk.LabelFrame(file_frame, text="访问日志", padding=10)
        log_group.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.file_log = scrolledtext.ScrolledText(log_group, height=10)
        self.file_log.pack(fill="both", expand=True)
    
    def create_game_page(self):
        """游戏联机页面"""
        game_frame = ttk.Frame(self.notebook)
        self.notebook.add(game_frame, text="游戏联机")
        
        # 游戏预设
        preset_group = ttk.LabelFrame(game_frame, text="游戏预设", padding=10)
        preset_group.pack(fill="x", padx=10, pady=5)
        
        games = {
            "Minecraft Java版": 25565,
            "Minecraft 基岩版": 19132,
            "Terraria": 7777,
            "CS:GO": 27015,
            "ARK": 7777,
            "饥荒": 10999,
            "自定义": 0
        }
        
        ttk.Label(preset_group, text="选择游戏:").grid(row=0, column=0, sticky="w", pady=2)
        self.game_select = ttk.Combobox(preset_group, values=list(games.keys()), width=30)
        self.game_select.grid(row=0, column=1, padx=5, pady=2)
        self.game_select.bind("<<ComboboxSelected>>", lambda e: self.on_game_select(games))
        
        ttk.Label(preset_group, text="游戏端口:").grid(row=1, column=0, sticky="w", pady=2)
        self.game_port = ttk.Entry(preset_group, width=30)
        self.game_port.insert(0, "25565")
        self.game_port.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(preset_group, text="外网端口:").grid(row=2, column=0, sticky="w", pady=2)
        self.game_remote_port = ttk.Entry(preset_group, width=30)
        self.game_remote_port.insert(0, "25565")
        self.game_remote_port.grid(row=2, column=1, padx=5, pady=2)
        
        # 玩家列表
        player_group = ttk.LabelFrame(game_frame, text="在线玩家", padding=10)
        player_group.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.player_list = tk.Listbox(player_group, height=8)
        self.player_list.pack(fill="both", expand=True)
        
        # 控制按钮
        control_frame = ttk.Frame(game_frame)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        self.game_start_btn = ttk.Button(control_frame, text="启动联机", 
                                        command=self.start_game_tunnel, width=15)
        self.game_start_btn.pack(side="left", padx=5)
        
        self.game_stop_btn = ttk.Button(control_frame, text="停止联机", 
                                       command=self.stop_game_tunnel, width=15, state="disabled")
        self.game_stop_btn.pack(side="left", padx=5)
        
        ttk.Button(control_frame, text="复制连接地址", 
                  command=self.copy_game_address, width=15).pack(side="left", padx=5)
    
    def create_remote_desktop_page(self):
        """远程桌面页面"""
        rdp_frame = ttk.Frame(self.notebook)
        self.notebook.add(rdp_frame, text="远程桌面")
        
        # VNC设置
        vnc_group = ttk.LabelFrame(rdp_frame, text="VNC设置", padding=10)
        vnc_group.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(vnc_group, text="VNC端口:").grid(row=0, column=0, sticky="w", pady=2)
        self.vnc_port = ttk.Entry(vnc_group, width=30)
        self.vnc_port.insert(0, "5900")
        self.vnc_port.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(vnc_group, text="外网端口:").grid(row=1, column=0, sticky="w", pady=2)
        self.vnc_remote_port = ttk.Entry(vnc_group, width=30)
        self.vnc_remote_port.insert(0, "5900")
        self.vnc_remote_port.grid(row=1, column=1, padx=5, pady=2)
        
        # RDP设置
        rdp_group = ttk.LabelFrame(rdp_frame, text="RDP设置", padding=10)
        rdp_group.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(rdp_group, text="RDP端口:").grid(row=0, column=0, sticky="w", pady=2)
        self.rdp_port = ttk.Entry(rdp_group, width=30)
        self.rdp_port.insert(0, "3389")
        self.rdp_port.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(rdp_group, text="外网端口:").grid(row=1, column=0, sticky="w", pady=2)
        self.rdp_remote_port = ttk.Entry(rdp_group, width=30)
        self.rdp_remote_port.insert(0, "3389")
        self.rdp_remote_port.grid(row=1, column=1, padx=5, pady=2)
        
        # 控制按钮
        control_frame = ttk.Frame(rdp_frame)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(control_frame, text="启动VNC穿透", 
                  command=self.start_vnc_tunnel, width=15).pack(side="left", padx=5)
        ttk.Button(control_frame, text="启动RDP穿透", 
                  command=self.start_rdp_tunnel, width=15).pack(side="left", padx=5)
        
        # 连接信息
        info_group = ttk.LabelFrame(rdp_frame, text="连接信息", padding=10)
        info_group.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.rdp_info = scrolledtext.ScrolledText(info_group, height=10)
        self.rdp_info.pack(fill="both", expand=True)
    
    def create_settings_page(self):
        """设置页面"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="设置")
    
        # 通用设置
        general_group = ttk.LabelFrame(settings_frame, text="通用设置", padding=10)
        general_group.pack(fill="x", padx=10, pady=5)

        self.auto_start = tk.BooleanVar()
        ttk.Checkbutton(general_group, text="开机自启动", 
                       variable=self.auto_start).pack(anchor="w", pady=2)

        self.minimize_to_tray = tk.BooleanVar()
        ttk.Checkbutton(general_group, text="最小化到托盘", 
                       variable=self.minimize_to_tray).pack(anchor="w", pady=2)

        self.auto_reconnect = tk.BooleanVar(value=True)
        ttk.Checkbutton(general_group, text="断线自动重连", 
                       variable=self.auto_reconnect).pack(anchor="w", pady=2)

        # 网络设置
        network_group = ttk.LabelFrame(settings_frame, text="网络设置", padding=10)
        network_group.pack(fill="x", padx=10, pady=5)

        # 使用pack而不是grid
        timeout_frame = ttk.Frame(network_group)
        timeout_frame.pack(fill="x", pady=2)
        ttk.Label(timeout_frame, text="连接超时(秒):").pack(side="left")
        self.timeout = ttk.Entry(timeout_frame, width=20)
        self.timeout.insert(0, "30")
        self.timeout.pack(side="left", padx=5)

        buffer_frame = ttk.Frame(network_group)
        buffer_frame.pack(fill="x", pady=2)
        ttk.Label(buffer_frame, text="缓冲区大小(KB):").pack(side="left")
        self.buffer_size = ttk.Entry(buffer_frame, width=20)
        self.buffer_size.insert(0, "4096")
        self.buffer_size.pack(side="left", padx=5)

        # 日志设置
        log_group = ttk.LabelFrame(settings_frame, text="日志设置", padding=10)
        log_group.pack(fill="x", padx=10, pady=5)

        self.save_log = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_group, text="保存日志到文件", 
                       variable=self.save_log).pack(anchor="w", pady=2)

        # 使用pack而不是grid
        log_days_frame = ttk.Frame(log_group)
        log_days_frame.pack(fill="x", pady=2)
        ttk.Label(log_days_frame, text="日志保留天数:").pack(side="left")
        self.log_days = ttk.Entry(log_days_frame, width=20)
        self.log_days.insert(0, "7")
        self.log_days.pack(side="left", padx=5)

        # 按钮
        btn_frame = ttk.Frame(settings_frame)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="保存设置", 
                  command=self.save_settings, width=15).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="恢复默认", 
                  command=self.reset_settings, width=15).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="清空日志", 
                  command=self.clear_logs, width=15).pack(side="left", padx=5)
        
    
    def create_log_page(self):
        """日志页面"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="运行日志")
        
        # 工具栏
        toolbar = ttk.Frame(log_frame)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(toolbar, text="清空日志", 
                  command=self.clear_log_display, width=12).pack(side="left", padx=2)
        ttk.Button(toolbar, text="保存日志", 
                  command=self.save_log_file, width=12).pack(side="left", padx=2)
        ttk.Button(toolbar, text="刷新", 
                  command=self.refresh_log, width=12).pack(side="left", padx=2)
        
        # 日志级别过滤
        ttk.Label(toolbar, text="级别:").pack(side="left", padx=5)
        self.log_level = ttk.Combobox(toolbar, values=["全部", "信息", "警告", "错误"], width=10)
        self.log_level.set("全部")
        self.log_level.pack(side="left", padx=2)
        
        # 日志显示
        log_display = ttk.Frame(log_frame)
        log_display.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_display, wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True)
        
        # 配置日志颜色标签
        self.log_text.tag_config("INFO", foreground="blue")
        self.log_text.tag_config("WARNING", foreground="orange")
        self.log_text.tag_config("ERROR", foreground="red")
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_bar, text="就绪", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        self.ip_label = ttk.Label(self.status_bar, text="本机IP: 获取中...", anchor=tk.E)
        self.ip_label.pack(side=tk.RIGHT, padx=5)
        
        # 异步获取IP
        threading.Thread(target=self.update_ip_display, daemon=True).start()
    
    # ========== 功能实现方法 ==========
    
    def log_message(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry, level)
        self.log_text.see(tk.END)
        
        # 保存到文件
        if self.save_log.get():
            with open("tunnel.log", "a", encoding="utf-8") as f:
                f.write(log_entry)
    
    def start_frp(self):
        """启动FRP"""
        try:
            config = {
                'server_addr': self.frp_server_addr.get(),
                'server_port': int(self.frp_server_port.get()),
                'token': self.frp_token.get(),
                'mappings': []
            }
            
            # 获取所有映射
            for item in self.mapping_tree.get_children():
                values = self.mapping_tree.item(item)['values']
                config['mappings'].append({
                    'name': values[0],
                    'type': values[1].lower(),
                    'local_port': int(values[2]),
                    'remote_port': int(values[3])
                })
            
            # 启动隧道
            if self.tunnel_manager.start_frp(config):
                self.frp_start_btn.config(state="disabled")
                self.frp_stop_btn.config(state="normal")
                self.log_message("FRP穿透已启动")
                self.update_status("FRP运行中")
            else:
                messagebox.showerror("错误", "启动FRP失败")
                
        except Exception as e:
            self.log_message(f"启动FRP失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"启动失败: {str(e)}")
    
    def stop_frp(self):
        """停止FRP"""
        self.tunnel_manager.stop_frp()
        self.frp_start_btn.config(state="normal")
        self.frp_stop_btn.config(state="disabled")
        self.log_message("FRP穿透已停止")
        self.update_status("就绪")
    
    def add_mapping(self):
        """添加端口映射"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加端口映射")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        
        ttk.Label(dialog, text="映射名称:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        name_entry = ttk.Entry(dialog, width=25)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="协议类型:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        type_combo = ttk.Combobox(dialog, values=["TCP", "UDP"], width=23)
        type_combo.set("TCP")
        type_combo.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="本地端口:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        local_entry = ttk.Entry(dialog, width=25)
        local_entry.grid(row=2, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="远程端口:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        remote_entry = ttk.Entry(dialog, width=25)
        remote_entry.grid(row=3, column=1, padx=10, pady=10)
        
        def save_mapping():
            name = name_entry.get().strip()
            ptype = type_combo.get()
            local = local_entry.get().strip()
            remote = remote_entry.get().strip()
            
            if not all([name, local, remote]):
                messagebox.showwarning("警告", "请填写所有字段")
                return
            
            try:
                int(local)
                int(remote)
            except:
                messagebox.showerror("错误", "端口必须是数字")
                return
            
            self.mapping_tree.insert("", "end", values=(name, ptype, local, remote))
            self.log_message(f"添加映射: {name} ({ptype}) {local}->{remote}")
            dialog.destroy()
        
        ttk.Button(dialog, text="保存", command=save_mapping, width=12).grid(
            row=4, column=0, columnspan=2, pady=20)
    
    def delete_mapping(self):
        """删除映射"""
        selection = self.mapping_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的映射")
            return
        
        for item in selection:
            self.mapping_tree.delete(item)
        self.log_message("删除映射")
    
    def edit_mapping(self):
        """编辑映射"""
        selection = self.mapping_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要编辑的映射")
            return
        
        # 实现编辑对话框
        messagebox.showinfo("提示", "双击映射项进行编辑")
    
    def start_simple_tunnel(self):
        """启动简单穿透"""
        try:
            listen_port = int(self.tunnel_listen_port.get())
            target_host = self.tunnel_target_host.get()
            target_port = int(self.tunnel_target_port.get())
            protocol = self.tunnel_protocol.get()
            encrypt = self.tunnel_encrypt.get()
            
            if self.tunnel_manager.start_simple_tunnel(
                listen_port, target_host, target_port, protocol, encrypt):
                
                self.tunnel_start_btn.config(state="disabled")
                self.tunnel_stop_btn.config(state="normal")
                self.log_message(f"简单穿透已启动: {listen_port}->{target_host}:{target_port}")
                self.update_status("穿透运行中")
            else:
                messagebox.showerror("错误", "启动穿透失败")
                
        except Exception as e:
            self.log_message(f"启动穿透失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", str(e))
    
    def stop_simple_tunnel(self):
        """停止简单穿透"""
        self.tunnel_manager.stop_simple_tunnel()
        self.tunnel_start_btn.config(state="normal")
        self.tunnel_stop_btn.config(state="disabled")
        self.log_message("简单穿透已停止")
        self.update_status("就绪")
    
    def start_file_server(self):
        """启动文件服务器"""
        try:
            directory = self.share_dir.get()
            port = int(self.share_port.get())
            password = self.share_password.get()
            readonly = self.share_readonly.get()
            
            if not directory or not os.path.exists(directory):
                messagebox.showerror("错误", "请选择有效的分享目录")
                return
            
            if self.file_server.start(directory, port, password, readonly):
                self.file_start_btn.config(state="disabled")
                self.file_stop_btn.config(state="normal")
                
                local_ip = get_local_ip()
                url = f"http://{local_ip}:{port}"
                self.log_message(f"文件服务器已启动: {url}")
                self.file_log.insert(tk.END, f"访问地址: {url}\n")
                if password:
                    self.file_log.insert(tk.END, f"访问密码: {password}\n")
            else:
                messagebox.showerror("错误", "启动文件服务器失败")
                
        except Exception as e:
            self.log_message(f"启动文件服务器失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", str(e))
    
    def stop_file_server(self):
        """停止文件服务器"""
        self.file_server.stop()
        self.file_start_btn.config(state="normal")
        self.file_stop_btn.config(state="disabled")
        self.log_message("文件服务器已停止")
    
    def open_file_browser(self):
        """在浏览器中打开文件服务器"""
        port = self.share_port.get()
        url = f"http://127.0.0.1:{port}"
        webbrowser.open(url)
    
    def start_game_tunnel(self):
        """启动游戏隧道"""
        try:
            local_port = int(self.game_port.get())
            remote_port = int(self.game_remote_port.get())
            
            config = {
                'type': 'tcp',
                'local_port': local_port,
                'remote_port': remote_port
            }
            
            if self.tunnel_manager.start_game_tunnel(config):
                self.game_start_btn.config(state="disabled")
                self.game_stop_btn.config(state="normal")
                self.log_message(f"游戏隧道已启动: {local_port}->{remote_port}")
            else:
                messagebox.showerror("错误", "启动游戏隧道失败")
                
        except Exception as e:
            self.log_message(f"启动游戏隧道失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", str(e))
    
    def stop_game_tunnel(self):
        """停止游戏隧道"""
        self.tunnel_manager.stop_game_tunnel()
        self.game_start_btn.config(state="normal")
        self.game_stop_btn.config(state="disabled")
        self.log_message("游戏隧道已停止")
    
    def copy_game_address(self):
        """复制游戏连接地址"""
        public_ip = get_public_ip()
        port = self.game_remote_port.get()
        address = f"{public_ip}:{port}"
        
        self.root.clipboard_clear()
        self.root.clipboard_append(address)
        messagebox.showinfo("成功", f"已复制连接地址: {address}")
        self.log_message(f"复制连接地址: {address}")
    
    def on_game_select(self, games):
        """游戏选择事件"""
        game = self.game_select.get()
        port = games.get(game, 0)
        if port > 0:
            self.game_port.delete(0, tk.END)
            self.game_port.insert(0, str(port))
            self.game_remote_port.delete(0, tk.END)
            self.game_remote_port.insert(0, str(port))
    
    def start_vnc_tunnel(self):
        """启动VNC穿透"""
        try:
            local_port = int(self.vnc_port.get())
            remote_port = int(self.vnc_remote_port.get())
            
            config = {
                'type': 'tcp',
                'local_port': local_port,
                'remote_port': remote_port
            }
            
            if self.tunnel_manager.start_vnc_tunnel(config):
                self.log_message(f"VNC隧道已启动: {local_port}->{remote_port}")
                self.rdp_info.insert(tk.END, f"VNC连接: {get_public_ip()}:{remote_port}\n")
            else:
                messagebox.showerror("错误", "启动VNC隧道失败")
                
        except Exception as e:
            self.log_message(f"启动VNC隧道失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", str(e))
    
    def start_rdp_tunnel(self):
        """启动RDP穿透"""
        try:
            local_port = int(self.rdp_port.get())
            remote_port = int(self.rdp_remote_port.get())
            
            config = {
                'type': 'tcp',
                'local_port': local_port,
                'remote_port': remote_port
            }
            
            if self.tunnel_manager.start_rdp_tunnel(config):
                self.log_message(f"RDP隧道已启动: {local_port}->{remote_port}")
                self.rdp_info.insert(tk.END, f"RDP连接: {get_public_ip()}:{remote_port}\n")
            else:
                messagebox.showerror("错误", "启动RDP隧道失败")
                
        except Exception as e:
            self.log_message(f"启动RDP隧道失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", str(e))
    
    def browse_share_dir(self):
        """浏览分享目录"""
        directory = filedialog.askdirectory()
        if directory:
            self.share_dir.delete(0, tk.END)
            self.share_dir.insert(0, directory)
    
    def show_local_ip(self):
        """显示本机IP"""
        ip = get_local_ip()
        messagebox.showinfo("本机IP", f"本机IP地址: {ip}")
    
    def show_public_ip(self):
        """显示公网IP"""
        ip = get_public_ip()
        messagebox.showinfo("公网IP", f"公网IP地址: {ip}")
    
    def open_port_scanner(self):
        """打开端口扫描工具"""
        scanner = PortScannerDialog(self.root, self.log_message)
    
    def test_latency(self):
        """测试网络延迟"""
        LatencyTestDialog(self.root, self.log_message)
    
    def show_tutorial(self):
        """显示使用教程"""
        tutorial = """
        内网穿透工具使用教程
        
        1. FRP穿透：适合长期稳定使用
           - 需要有公网IP的服务器
           - 配置服务器地址和端口
           - 添加需要映射的端口
        
        2. 简单穿透：适合临时使用
           - 无需服务器
           - 配置本地和目标端口即可
        
        3. 文件分享：快速分享文件夹
           - 选择要分享的目录
           - 设置访问密码（可选）
           - 分享链接给朋友
        
        4. 游戏联机：快速开启游戏服务器
           - 选择游戏类型
           - 自动配置端口
           - 复制连接地址给朋友
        
        更多帮助请访问项目主页
        """
        messagebox.showinfo("使用教程", tutorial)
    
    def show_about(self):
        """关于对话框"""
        about_text = """
        多功能内网穿透工具 v2.0
        
        一款功能强大的内网穿透工具
        支持游戏联机、文件分享、远程桌面等
        
        开发语言: Python 3.x
        界面框架: Tkinter
        
        开源协议: MIT License
        作者: Your Name
        """
        messagebox.showinfo("关于", about_text)
    
    def update_status(self, status):
        """更新状态栏"""
        self.status_label.config(text=status)
    
    def update_ip_display(self):
        """更新IP显示"""
        local_ip = get_local_ip()
        self.ip_label.config(text=f"本机IP: {local_ip}")
    
    def clear_log_display(self):
        """清空日志显示"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("日志已清空")
    
    def save_log_file(self):
        """保存日志文件"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt")]
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.log_text.get(1.0, tk.END))
            messagebox.showinfo("成功", "日志已保存")
    
    def refresh_log(self):
        """刷新日志"""
        self.log_message("日志已刷新")
    
    def clear_logs(self):
        """清空所有日志"""
        if messagebox.askyesno("确认", "确定要清空所有日志吗？"):
            if os.path.exists("tunnel.log"):
                os.remove("tunnel.log")
            self.log_text.delete(1.0, tk.END)
            self.log_message("所有日志已清空")
    
    def save_settings(self):
        """保存设置"""
        config = {
            'frp_server': self.frp_server_addr.get(),
            'frp_port': self.frp_server_port.get(),
            'auto_start': self.auto_start.get(),
            'minimize_to_tray': self.minimize_to_tray.get(),
            'auto_reconnect': self.auto_reconnect.get(),
            'timeout': self.timeout.get(),
            'buffer_size': self.buffer_size.get(),
            'save_log': self.save_log.get(),
            'log_days': self.log_days.get()
        }
        
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        messagebox.showinfo("成功", "设置已保存")
        self.log_message("配置已保存")
    
    def load_settings(self):
        """加载设置"""
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                self.frp_server_addr.delete(0, tk.END)
                self.frp_server_addr.insert(0, config.get('frp_server', ''))
                
                self.frp_server_port.delete(0, tk.END)
                self.frp_server_port.insert(0, config.get('frp_port', '7000'))
                
                self.auto_start.set(config.get('auto_start', False))
                self.minimize_to_tray.set(config.get('minimize_to_tray', False))
                self.auto_reconnect.set(config.get('auto_reconnect', True))
                
                self.timeout.delete(0, tk.END)
                self.timeout.insert(0, config.get('timeout', '30'))
                
                self.buffer_size.delete(0, tk.END)
                self.buffer_size.insert(0, config.get('buffer_size', '4096'))
                
                self.save_log.set(config.get('save_log', True))
                
                self.log_days.delete(0, tk.END)
                self.log_days.insert(0, config.get('log_days', '7'))
                
                self.log_message("配置已加载")
            except Exception as e:
                self.log_message(f"加载配置失败: {str(e)}", "ERROR")
    
    def reset_settings(self):
        """恢复默认设置"""
        if messagebox.askyesno("确认", "确定要恢复默认设置吗？"):
            if os.path.exists("config.json"):
                os.remove("config.json")
            self.load_settings()
            messagebox.showinfo("成功", "已恢复默认设置")
    
    def load_config(self):
        """加载配置"""
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def open_qr_generator(self):
        """打开二维码生成器"""
        try:
            from advanced_tools import QRCodeGenerator
            QRCodeGenerator(self.root)
        except ImportError:
            messagebox.showwarning("提示", "此功能需要安装qrcode库\n运行: pip install qrcode pillow")
        except Exception as e:
            messagebox.showerror("错误", f"打开失败: {str(e)}")
    
    def open_traffic_monitor(self):
        """打开流量监控"""
        try:
            from advanced_tools import TrafficMonitor
            TrafficMonitor(self.root)
        except ImportError:
            messagebox.showwarning("提示", "此功能需要安装psutil库\n运行: pip install psutil")
        except Exception as e:
            messagebox.showerror("错误", f"打开失败: {str(e)}")
    
    def open_system_info(self):
        """打开系统信息"""
        try:
            from advanced_tools import SystemInfo
            SystemInfo(self.root)
        except Exception as e:
            messagebox.showerror("错误", f"打开失败: {str(e)}")

    def on_closing(self):
        """关闭程序"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            # 停止所有服务
            self.tunnel_manager.stop_all()
            self.file_server.stop()
            self.root.destroy()

def main():
    root = tk.Tk()
    app = NetworkTunnelApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()