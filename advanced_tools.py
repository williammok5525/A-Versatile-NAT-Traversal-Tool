import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
import qrcode
from PIL import Image, ImageTk
import io
import subprocess
import platform

class QRCodeGenerator:
    """二维码生成器"""
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("二维码生成器")
        self.window.geometry("500x600")
        
        # 输入区
        input_frame = ttk.LabelFrame(self.window, text="输入信息", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(input_frame, text="文本内容:").pack(anchor="w")
        self.text_input = tk.Text(input_frame, height=4)
        self.text_input.pack(fill="x", pady=5)
        
        # 快捷按钮
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="当前IP", 
                  command=self.insert_ip).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="WiFi信息", 
                  command=self.insert_wifi).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="生成二维码", 
                  command=self.generate_qr).pack(side="left", padx=2)
        
        # 二维码显示
        qr_frame = ttk.LabelFrame(self.window, text="二维码预览", padding=10)
        qr_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.qr_label = ttk.Label(qr_frame)
        self.qr_label.pack(expand=True)
        
        # 保存按钮
        ttk.Button(self.window, text="保存图片", 
                  command=self.save_qr).pack(pady=10)
    
    def insert_ip(self):
        """插入IP地址"""
        from utils import get_local_ip, get_public_ip
        local_ip = get_local_ip()
        public_ip = get_public_ip()
        text = f"本机IP: {local_ip}\n公网IP: {public_ip}"
        self.text_input.delete(1.0, tk.END)
        self.text_input.insert(1.0, text)
    
    def insert_wifi(self):
        """插入WiFi信息"""
        # 这里可以添加WiFi信息获取逻辑
        text = "WIFI:T:WPA;S:YourSSID;P:YourPassword;;"
        self.text_input.delete(1.0, tk.END)
        self.text_input.insert(1.0, text)
    
    def generate_qr(self):
        """生成二维码"""
        text = self.text_input.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("警告", "请输入内容")
            return
        
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(text)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img = img.resize((300, 300))
            
            # 转换为PhotoImage
            self.qr_image = img
            photo = ImageTk.PhotoImage(img)
            self.qr_label.config(image=photo)
            self.qr_label.image = photo
            
        except Exception as e:
            messagebox.showerror("错误", f"生成失败: {str(e)}")
    
    def save_qr(self):
        """保存二维码"""
        from tkinter import filedialog
        if not hasattr(self, 'qr_image'):
            messagebox.showwarning("警告", "请先生成二维码")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG图片", "*.png"), ("所有文件", "*.*")]
        )
        
        if filename:
            self.qr_image.save(filename)
            messagebox.showinfo("成功", "二维码已保存")

class TrafficMonitor:
    """流量监控器"""
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("流量监控")
        self.window.geometry("600x400")
        self.monitoring = False
        
        # 控制区
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="开始监控", 
                                    command=self.start_monitor)
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="停止监控", 
                                   command=self.stop_monitor, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        # 统计信息
        stats_frame = ttk.LabelFrame(self.window, text="实时统计", padding=10)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        # 上传
        ttk.Label(stats_frame, text="上传速度:").grid(row=0, column=0, sticky="w")
        self.upload_label = ttk.Label(stats_frame, text="0 KB/s", 
                                      font=('Arial', 14, 'bold'))
        self.upload_label.grid(row=0, column=1, padx=10)
        
        # 下载
        ttk.Label(stats_frame, text="下载速度:").grid(row=1, column=0, sticky="w")
        self.download_label = ttk.Label(stats_frame, text="0 KB/s", 
                                        font=('Arial', 14, 'bold'))
        self.download_label.grid(row=1, column=1, padx=10)
        
        # 总计
        ttk.Label(stats_frame, text="总上传:").grid(row=2, column=0, sticky="w")
        self.total_upload = ttk.Label(stats_frame, text="0 MB")
        self.total_upload.grid(row=2, column=1, padx=10)
        
        ttk.Label(stats_frame, text="总下载:").grid(row=3, column=0, sticky="w")
        self.total_download = ttk.Label(stats_frame, text="0 MB")
        self.total_download.grid(row=3, column=1, padx=10)
        
        # 详细信息
        detail_frame = ttk.LabelFrame(self.window, text="详细信息", padding=10)
        detail_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.detail_text = scrolledtext.ScrolledText(detail_frame, height=10)
        self.detail_text.pack(fill="both", expand=True)
    
    def start_monitor(self):
        """开始监控"""
        self.monitoring = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        def monitor_thread():
            try:
                import psutil
                
                last_sent = psutil.net_io_counters().bytes_sent
                last_recv = psutil.net_io_counters().bytes_recv
                
                while self.monitoring:
                    import time
                    time.sleep(1)
                    
                    current = psutil.net_io_counters()
                    
                    upload_speed = (current.bytes_sent - last_sent) / 1024
                    download_speed = (current.bytes_recv - last_recv) / 1024
                    
                    self.upload_label.config(
                        text=f"{upload_speed:.2f} KB/s"
                    )
                    self.download_label.config(
                        text=f"{download_speed:.2f} KB/s"
                    )
                    
                    total_up = current.bytes_sent / (1024 * 1024)
                    total_down = current.bytes_recv / (1024 * 1024)
                    
                    self.total_upload.config(text=f"{total_up:.2f} MB")
                    self.total_download.config(text=f"{total_down:.2f} MB")
                    
                    last_sent = current.bytes_sent
                    last_recv = current.bytes_recv
                    
                    # 记录到详细信息
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    log = f"[{timestamp}] ↑{upload_speed:.1f}KB/s ↓{download_speed:.1f}KB/s\n"
                    self.detail_text.insert(tk.END, log)
                    self.detail_text.see(tk.END)
                    
            except ImportError:
                messagebox.showerror("错误", "需要安装psutil库: pip install psutil")
                self.stop_monitor()
        
        threading.Thread(target=monitor_thread, daemon=True).start()
    
    def stop_monitor(self):
        """停止监控"""
        self.monitoring = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

class SystemInfo:
    """系统信息查看器"""
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("系统信息")
        self.window.geometry("600x500")
        
        # 创建Notebook
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 系统信息页
        self.create_system_tab(notebook)
        
        # 网络信息页
        self.create_network_tab(notebook)
        
        # 刷新按钮
        ttk.Button(self.window, text="刷新", 
                  command=self.refresh_all).pack(pady=5)
    
    def create_system_tab(self, notebook):
        """创建系统信息页"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="系统信息")
        
        self.sys_text = scrolledtext.ScrolledText(frame)
        self.sys_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.update_system_info()
    
    def create_network_tab(self, notebook):
        """创建网络信息页"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="网络信息")
        
        self.net_text = scrolledtext.ScrolledText(frame)
        self.net_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.update_network_info()
    
    def update_system_info(self):
        """更新系统信息"""
        self.sys_text.delete(1.0, tk.END)
        
        info = f"""
系统信息
{'='*50}

操作系统: {platform.system()} {platform.release()}
架构: {platform.machine()}
处理器: {platform.processor()}
Python版本: {platform.python_version()}
计算机名: {platform.node()}
"""
        
        try:
            import psutil
            
            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            info += f"\nCPU使用率: {cpu_percent}%"
            info += f"\nCPU核心数: {cpu_count}"
            
            # 内存信息
            mem = psutil.virtual_memory()
            info += f"\n\n内存总量: {mem.total / (1024**3):.2f} GB"
            info += f"\n已用内存: {mem.used / (1024**3):.2f} GB"
            info += f"\n内存使用率: {mem.percent}%"
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            info += f"\n\n磁盘总量: {disk.total / (1024**3):.2f} GB"
            info += f"\n已用磁盘: {disk.used / (1024**3):.2f} GB"
            info += f"\n磁盘使用率: {disk.percent}%"
            
        except ImportError:
            info += "\n\n(安装psutil库获取更多信息: pip install psutil)"
        
        self.sys_text.insert(1.0, info)
    
    def update_network_info(self):
        """更新网络信息"""
        self.net_text.delete(1.0, tk.END)
        
        from utils import get_local_ip, get_public_ip, get_all_interfaces
        
        info = f"""
网络信息
{'='*50}

本机IP: {get_local_ip()}
公网IP: {get_public_ip()}

网络接口:
"""
        
        interfaces = get_all_interfaces()
        for iface in interfaces:
            info += f"\n  {iface['name']}: {iface['ip']}"
        
        try:
            import psutil
            
            net_io = psutil.net_io_counters()
            info += f"\n\n网络统计:"
            info += f"\n  发送: {net_io.bytes_sent / (1024**2):.2f} MB"
            info += f"\n  接收: {net_io.bytes_recv / (1024**2):.2f} MB"
            info += f"\n  发送包: {net_io.packets_sent}"
            info += f"\n  接收包: {net_io.packets_recv}"
            
        except ImportError:
            pass
        
        self.net_text.insert(1.0, info)
    
    def refresh_all(self):
        """刷新所有信息"""
        self.update_system_info()
        self.update_network_info()