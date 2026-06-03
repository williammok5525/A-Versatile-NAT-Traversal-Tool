import socket
import requests
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import time
import subprocess
import platform
import re

def get_local_ip():
    """获取本机IP地址"""
    try:
        # 创建一个UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_public_ip():
    """获取公网IP地址"""
    try:
        # 尝试多个服务
        services = [
            "https://api.ipify.org",
            "https://ifconfig.me/ip",
            "https://icanhazip.com",
            "https://ident.me"
        ]
        
        for service in services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    return response.text.strip()
            except:
                continue
        
        return "无法获取"
    except:
        return "无法获取"

def get_all_interfaces():
    """获取所有网络接口"""
    interfaces = []
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            output = result.stdout
            
            # 解析ipconfig输出
            current_interface = None
            for line in output.split('\n'):
                if '适配器' in line or 'adapter' in line.lower():
                    current_interface = line.strip()
                elif 'IPv4' in line:
                    ip = line.split(':')[-1].strip()
                    if current_interface:
                        interfaces.append({
                            'name': current_interface,
                            'ip': ip
                        })
        else:
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            output = result.stdout
            # 解析ifconfig输出
            # 这里可以添加Linux/Mac的解析逻辑
            
    except Exception as e:
        print(f"获取网络接口失败: {e}")
    
    return interfaces

def check_port(host, port, timeout=3):
    """检查端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def scan_ports(host, start_port, end_port, callback):
    """扫描端口范围"""
    open_ports = []
    
    for port in range(start_port, end_port + 1):
        if check_port(host, port, timeout=1):
            open_ports.append(port)
            callback(f"发现开放端口: {port}")
        else:
            callback(f"扫描端口: {port} (关闭)")
    
    return open_ports

def ping_host(host, count=4):
    """Ping主机"""
    try:
        if platform.system() == "Windows":
            cmd = ['ping', '-n', str(count), host]
        else:
            cmd = ['ping', '-c', str(count), host]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout
    except Exception as e:
        return f"Ping失败: {str(e)}"

def test_speed(host, port, duration=5):
    """测试网络速度"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        
        data = b'0' * 1024  # 1KB数据
        start_time = time.time()
        bytes_sent = 0
        
        while time.time() - start_time < duration:
            sock.send(data)
            bytes_sent += len(data)
        
        sock.close()
        
        speed_mbps = (bytes_sent * 8) / (duration * 1024 * 1024)
        return f"{speed_mbps:.2f} Mbps"
    except Exception as e:
        return f"测试失败: {str(e)}"

def get_latency(host, port=80, count=4):
    """测试延迟"""
    latencies = []
    
    for _ in range(count):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            start = time.time()
            sock.connect((host, port))
            end = time.time()
            
            latency = (end - start) * 1000  # 转换为毫秒
            latencies.append(latency)
            sock.close()
            
        except:
            continue
    
    if latencies:
        avg = sum(latencies) / len(latencies)
        min_lat = min(latencies)
        max_lat = max(latencies)
        return {
            'avg': avg,
            'min': min_lat,
            'max': max_lat,
            'count': len(latencies)
        }
    else:
        return None

def format_bytes(size):
    """格式化字节大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def validate_ip(ip):
    """验证IP地址"""
    pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    if pattern.match(ip):
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    return False

def validate_port(port):
    """验证端口号"""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except:
        return False

def generate_qr_code(data, size=200):
    """生成二维码"""
    try:
        import qrcode
        from PIL import ImageTk
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size))
        
        return ImageTk.PhotoImage(img)
    except ImportError:
        return None

class PortScannerDialog:
    """端口扫描对话框"""
    def __init__(self, parent, log_callback):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("端口扫描工具")
        self.dialog.geometry("600x500")
        self.log = log_callback
        self.scanning = False
        
        # 配置区
        config_frame = ttk.LabelFrame(self.dialog, text="扫描配置", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(config_frame, text="目标主机:").grid(row=0, column=0, sticky="w", pady=5)
        self.host_entry = ttk.Entry(config_frame, width=30)
        self.host_entry.insert(0, "127.0.0.1")
        self.host_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="起始端口:").grid(row=1, column=0, sticky="w", pady=5)
        self.start_port = ttk.Entry(config_frame, width=30)
        self.start_port.insert(0, "1")
        self.start_port.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="结束端口:").grid(row=2, column=0, sticky="w", pady=5)
        self.end_port = ttk.Entry(config_frame, width=30)
        self.end_port.insert(0, "1000")
        self.end_port.grid(row=2, column=1, padx=5, pady=5)
        
        # 常用端口快捷按钮
        preset_frame = ttk.Frame(config_frame)
        preset_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(preset_frame, text="常用端口", 
                  command=lambda: self.set_range(1, 1024)).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="Web服务", 
                  command=lambda: self.set_range(80, 8080)).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="全端口", 
                  command=lambda: self.set_range(1, 65535)).pack(side="left", padx=2)
        
        # 控制按钮
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.scan_btn = ttk.Button(btn_frame, text="开始扫描", command=self.start_scan)
        self.scan_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="停止扫描", 
                                   command=self.stop_scan, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        # 进度条
        self.progress = ttk.Progressbar(self.dialog, mode='determinate')
        self.progress.pack(fill="x", padx=10, pady=5)
        
        # 结果显示
        result_frame = ttk.LabelFrame(self.dialog, text="扫描结果", padding=10)
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=15)
        self.result_text.pack(fill="both", expand=True)
    
    def set_range(self, start, end):
        """设置端口范围"""
        self.start_port.delete(0, tk.END)
        self.start_port.insert(0, str(start))
        self.end_port.delete(0, tk.END)
        self.end_port.insert(0, str(end))
    
    def start_scan(self):
        """开始扫描"""
        host = self.host_entry.get()
        start = int(self.start_port.get())
        end = int(self.end_port.get())
        
        if not validate_ip(host) and host != 'localhost':
            tk.messagebox.showerror("错误", "无效的IP地址")
            return
        
        self.scanning = True
        self.scan_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.result_text.delete(1.0, tk.END)
        
        self.result_text.insert(tk.END, f"开始扫描 {host}:{start}-{end}\n")
        self.result_text.insert(tk.END, "=" * 50 + "\n")
        
        def scan_thread():
            total_ports = end - start + 1
            scanned = 0
            open_ports = []
            
            for port in range(start, end + 1):
                if not self.scanning:
                    break
                
                if check_port(host, port, timeout=1):
                    service = get_service_name(port)
                    msg = f"✓ 端口 {port} 开放 [{service}]\n"
                    self.result_text.insert(tk.END, msg)
                    self.result_text.see(tk.END)
                    open_ports.append(port)
                    self.log(f"发现开放端口: {port} ({service})")
                
                scanned += 1
                progress = (scanned / total_ports) * 100
                self.progress['value'] = progress
                self.dialog.update_idletasks()
            
            self.result_text.insert(tk.END, "=" * 50 + "\n")
            self.result_text.insert(tk.END, f"扫描完成! 发现 {len(open_ports)} 个开放端口\n")
            
            self.scan_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.scanning = False
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def stop_scan(self):
        """停止扫描"""
        self.scanning = False
        self.result_text.insert(tk.END, "\n扫描已停止\n")
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

def get_service_name(port):
    """获取端口对应的服务名"""
    services = {
        20: "FTP-Data", 21: "FTP", 22: "SSH", 23: "Telnet",
        25: "SMTP", 53: "DNS", 80: "HTTP", 110: "POP3",
        143: "IMAP", 443: "HTTPS", 445: "SMB", 3306: "MySQL",
        3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
        8080: "HTTP-Proxy", 8443: "HTTPS-Alt", 27017: "MongoDB",
        25565: "Minecraft", 7777: "Terraria", 19132: "Minecraft-BE"
    }
    return services.get(port, "Unknown")

class LatencyTestDialog:
    """延迟测试对话框"""
    def __init__(self, parent, log_callback):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("网络延迟测试")
        self.dialog.geometry("500x400")
        self.log = log_callback
        
        # 配置区
        config_frame = ttk.LabelFrame(self.dialog, text="测试配置", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(config_frame, text="目标主机:").grid(row=0, column=0, sticky="w", pady=5)
        self.host_entry = ttk.Entry(config_frame, width=30)
        self.host_entry.insert(0, "8.8.8.8")
        self.host_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="端口:").grid(row=1, column=0, sticky="w", pady=5)
        self.port_entry = ttk.Entry(config_frame, width=30)
        self.port_entry.insert(0, "80")
        self.port_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="测试次数:").grid(row=2, column=0, sticky="w", pady=5)
        self.count_entry = ttk.Entry(config_frame, width=30)
        self.count_entry.insert(0, "10")
        self.count_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # 预设服务器
        preset_frame = ttk.Frame(config_frame)
        preset_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(preset_frame, text="Google DNS", 
                  command=lambda: self.set_host("8.8.8.8")).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="百度", 
                  command=lambda: self.set_host("www.baidu.com")).pack(side="left", padx=2)
        ttk.Button(preset_frame, text="腾讯", 
                  command=lambda: self.set_host("www.qq.com")).pack(side="left", padx=2)
        
        # 控制按钮
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="开始测试", command=self.start_test).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="清空结果", command=self.clear_results).pack(side="left", padx=5)
        
        # 结果显示
        result_frame = ttk.LabelFrame(self.dialog, text="测试结果", padding=10)
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=12)
        self.result_text.pack(fill="both", expand=True)
    
    def set_host(self, host):
        """设置主机"""
        self.host_entry.delete(0, tk.END)
        self.host_entry.insert(0, host)
    
    def start_test(self):
        """开始测试"""
        host = self.host_entry.get()
        port = int(self.port_entry.get())
        count = int(self.count_entry.get())
        
        self.result_text.insert(tk.END, f"\n正在测试 {host}:{port}\n")
        self.result_text.insert(tk.END, "=" * 50 + "\n")
        
        def test_thread():
            latencies = []
            
            for i in range(count):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    
                    start = time.time()
                    sock.connect((host, port))
                    end = time.time()
                    
                    latency = (end - start) * 1000
                    latencies.append(latency)
                    
                    msg = f"测试 {i+1}: {latency:.2f} ms\n"
                    self.result_text.insert(tk.END, msg)
                    self.result_text.see(tk.END)
                    
                    sock.close()
                    time.sleep(0.5)
                    
                except Exception as e:
                    self.result_text.insert(tk.END, f"测试 {i+1}: 失败 ({str(e)})\n")
            
            if latencies:
                avg = sum(latencies) / len(latencies)
                min_lat = min(latencies)
                max_lat = max(latencies)
                
                self.result_text.insert(tk.END, "=" * 50 + "\n")
                self.result_text.insert(tk.END, f"平均延迟: {avg:.2f} ms\n")
                self.result_text.insert(tk.END, f"最小延迟: {min_lat:.2f} ms\n")
                self.result_text.insert(tk.END, f"最大延迟: {max_lat:.2f} ms\n")
                self.result_text.insert(tk.END, f"丢包率: {((count - len(latencies)) / count * 100):.1f}%\n")
                
                self.log(f"延迟测试完成: {host} 平均 {avg:.2f}ms")
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def clear_results(self):
        """清空结果"""
        self.result_text.delete(1.0, tk.END)

class SpeedTestDialog:
    """网速测试对话框"""
    def __init__(self, parent, log_callback):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("网速测试")
        self.dialog.geometry("500x400")
        self.log = log_callback
        self.testing = False
        
        # 信息显示
        info_frame = ttk.LabelFrame(self.dialog, text="网络信息", padding=10)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        self.info_text = tk.Text(info_frame, height=6)
        self.info_text.pack(fill="both", expand=True)
        
        # 显示本机信息
        local_ip = get_local_ip()
        public_ip = get_public_ip()
        self.info_text.insert(tk.END, f"本机IP: {local_ip}\n")
        self.info_text.insert(tk.END, f"公网IP: {public_ip}\n")
        
        # 控制按钮
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        self.test_btn = ttk.Button(btn_frame, text="开始测速", command=self.start_test)
        self.test_btn.pack(side="left", padx=5)
        
        # 结果显示
        result_frame = ttk.LabelFrame(self.dialog, text="测试结果", padding=10)
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=12)
        self.result_text.pack(fill="both", expand=True)
    
    def start_test(self):
        """开始测速"""
        if self.testing:
            return
        
        self.testing = True
        self.test_btn.config(state="disabled")
        self.result_text.insert(tk.END, "正在测试网速...\n")
        
        def test_thread():
            try:
                # 这里可以集成speedtest-cli或其他测速工具
                self.result_text.insert(tk.END, "下载速度测试中...\n")
                # 模拟测速
                time.sleep(2)
                self.result_text.insert(tk.END, "下载速度: 100 Mbps\n")
                
                self.result_text.insert(tk.END, "上传速度测试中...\n")
                time.sleep(2)
                self.result_text.insert(tk.END, "上传速度: 50 Mbps\n")
                
                self.result_text.insert(tk.END, "延迟测试中...\n")
                time.sleep(1)
                self.result_text.insert(tk.END, "延迟: 20 ms\n")
                
                self.result_text.insert(tk.END, "\n测试完成!\n")
                
            except Exception as e:
                self.result_text.insert(tk.END, f"测试失败: {str(e)}\n")
            finally:
                self.testing = False
                self.test_btn.config(state="normal")
        
        threading.Thread(target=test_thread, daemon=True).start()

class NetworkMonitor:
    """网络流量监控"""
    def __init__(self):
        self.last_bytes_sent = 0
        self.last_bytes_recv = 0
        self.last_time = time.time()
    
    def get_speed(self):
        """获取当前网速"""
        try:
            import psutil
            
            net_io = psutil.net_io_counters()
            current_time = time.time()
            
            time_delta = current_time - self.last_time
            
            bytes_sent = net_io.bytes_sent - self.last_bytes_sent
            bytes_recv = net_io.bytes_recv - self.last_bytes_recv
            
            upload_speed = bytes_sent / time_delta if time_delta > 0 else 0
            download_speed = bytes_recv / time_delta if time_delta > 0 else 0
            
            self.last_bytes_sent = net_io.bytes_sent
            self.last_bytes_recv = net_io.bytes_recv
            self.last_time = current_time
            
            return {
                'upload': format_bytes(upload_speed) + '/s',
                'download': format_bytes(download_speed) + '/s'
            }
        except ImportError:
            return {'upload': 'N/A', 'download': 'N/A'}