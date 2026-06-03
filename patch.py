# patch.py - 一键修复脚本
import os
import shutil

def create_missing_files():
    """创建缺失的文件"""
    
    # 1. 创建 utils.py
    if not os.path.exists('utils.py'):
        print("创建 utils.py...")
        with open('utils.py', 'w', encoding='utf-8') as f:
            f.write('''
import socket
import requests
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

def get_local_ip():
    """获取本机IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_public_ip():
    """获取公网IP"""
    try:
        response = requests.get("https://api.ipify.org", timeout=5)
        return response.text.strip()
    except:
        return "无法获取"

def validate_ip(ip):
    """验证IP地址"""
    import re
    pattern = re.compile(r'^(\\d{1,3}\\.){3}\\d{1,3}$')
    if pattern.match(ip):
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    return False

def validate_port(port):
    """验证端口"""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except:
        return False

def check_port(host, port, timeout=3):
    """检查端口"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def get_service_name(port):
    """获取端口服务名"""
    services = {
        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
        80: "HTTP", 443: "HTTPS", 3306: "MySQL", 3389: "RDP",
        5900: "VNC", 8080: "HTTP-Proxy", 25565: "Minecraft"
    }
    return services.get(port, "Unknown")

def get_all_interfaces():
    """获取网络接口"""
    return []

class PortScannerDialog:
    """端口扫描器"""
    def __init__(self, parent, log_callback):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("端口扫描")
        self.dialog.geometry("500x400")
        self.log = log_callback
        
        ttk.Label(self.dialog, text="功能开发中...").pack(pady=20)
        ttk.Button(self.dialog, text="关闭", command=self.dialog.destroy).pack()

class LatencyTestDialog:
    """延迟测试"""
    def __init__(self, parent, log_callback):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("延迟测试")
        self.dialog.geometry("500x400")
        self.log = log_callback
        
        ttk.Label(self.dialog, text="功能开发中...").pack(pady=20)
        ttk.Button(self.dialog, text="关闭", command=self.dialog.destroy).pack()
''')
    
    # 2. 创建 tunnel_core.py
    if not os.path.exists('tunnel_core.py'):
        print("创建 tunnel_core.py...")
        with open('tunnel_core.py', 'w', encoding='utf-8') as f:
            f.write('''
import socket
import threading
import subprocess
import os

class TunnelManager:
    """穿透管理器"""
    def __init__(self, log_callback):
        self.log = log_callback
        self.running = False
        self.frp_process = None
        self.simple_tunnel = None
    
    def start_frp(self, config):
        """启动FRP"""
        self.log("FRP功能需要frpc.exe支持", "WARNING")
        return False
    
    def stop_frp(self):
        """停止FRP"""
        self.log("FRP已停止")
    
    def start_simple_tunnel(self, listen_port, target_host, target_port, protocol="TCP", encrypt=False):
        """启动简单穿透"""
        self.log(f"简单穿透: {listen_port} -> {target_host}:{target_port}")
        
        try:
            server = SimpleTCPTunnel(listen_port, target_host, target_port, self.log)
            self.simple_tunnel = server
            
            thread = threading.Thread(target=server.start, daemon=True)
            thread.start()
            return True
        except Exception as e:
            self.log(f"启动失败: {e}", "ERROR")
            return False
    
    def stop_simple_tunnel(self):
        """停止简单穿透"""
        if self.simple_tunnel:
            self.simple_tunnel.stop()
            self.simple_tunnel = None
    
    def start_game_tunnel(self, config):
        """启动游戏隧道"""
        return self.start_simple_tunnel(
            config['local_port'], "127.0.0.1", 
            config['local_port'], "TCP"
        )
    
    def stop_game_tunnel(self):
        """停止游戏隧道"""
        self.stop_simple_tunnel()
    
    def start_vnc_tunnel(self, config):
        """启动VNC"""
        return self.start_simple_tunnel(
            config['local_port'], "127.0.0.1",
            config['local_port'], "TCP"
        )
    
    def start_rdp_tunnel(self, config):
        """启动RDP"""
        return self.start_simple_tunnel(
            config['local_port'], "127.0.0.1",
            config['local_port'], "TCP"
        )
    
    def stop_all(self):
        """停止所有"""
        self.stop_frp()
        self.stop_simple_tunnel()

class SimpleTCPTunnel:
    """简单TCP穿透"""
    def __init__(self, listen_port, target_host, target_port, log_callback):
        self.listen_port = listen_port
        self.target_host = target_host
        self.target_port = target_port
        self.log = log_callback
        self.running = False
        self.server_socket = None
    
    def start(self):
        """启动"""
        try:
            self.running = True
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", self.listen_port))
            self.server_socket.listen(5)
            
            self.log(f"TCP隧道监听: {self.listen_port}")
            
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    client_socket, addr = self.server_socket.accept()
                    self.log(f"新连接: {addr}")
                    
                    threading.Thread(
                        target=self.handle_client,
                        args=(client_socket,),
                        daemon=True
                    ).start()
                except socket.timeout:
                    continue
                except:
                    break
        except Exception as e:
            self.log(f"隧道错误: {e}", "ERROR")
        finally:
            self.stop()
    
    def handle_client(self, client_socket):
        """处理客户端"""
        target_socket = None
        try:
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((self.target_host, self.target_port))
            
            def forward(src, dst):
                try:
                    while self.running:
                        data = src.recv(4096)
                        if not data:
                            break
                        dst.sendall(data)
                except:
                    pass
                finally:
                    src.close()
                    dst.close()
            
            t1 = threading.Thread(target=forward, args=(client_socket, target_socket), daemon=True)
            t2 = threading.Thread(target=forward, args=(target_socket, client_socket), daemon=True)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
        except Exception as e:
            self.log(f"转发错误: {e}", "ERROR")
        finally:
            if client_socket:
                client_socket.close()
            if target_socket:
                target_socket.close()
    
    def stop(self):
        """停止"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        self.log("TCP隧道已停止")
''')
    
    # 3. 创建 file_server.py
    if not os.path.exists('file_server.py'):
        print("创建 file_server.py...")
        with open('file_server.py', 'w', encoding='utf-8') as f:
            f.write('''
import os
import threading
import http.server
import socketserver

class FileServer:
    """文件服务器"""
    def __init__(self, log_callback):
        self.log = log_callback
        self.server = None
        self.running = False
    
    def start(self, directory, port, password=None, readonly=True):
        """启动文件服务器"""
        try:
            os.chdir(directory)
            
            Handler = http.server.SimpleHTTPRequestHandler
            self.server = socketserver.TCPServer(("", port), Handler)
            self.server.allow_reuse_address = True
            self.running = True
            
            def serve():
                self.server.serve_forever()
            
            threading.Thread(target=serve, daemon=True).start()
            
            self.log(f"文件服务器已启动: 端口 {port}")
            return True
        except Exception as e:
            self.log(f"启动失败: {e}", "ERROR")
            return False
    
    def stop(self):
        """停止"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            self.log("文件服务器已停止")
''')
    
    # 4. 创建 advanced_tools.py
    if not os.path.exists('advanced_tools.py'):
        print("创建 advanced_tools.py...")
        with open('advanced_tools.py', 'w', encoding='utf-8') as f:
            f.write('''
import tkinter as tk
from tkinter import ttk, messagebox

class QRCodeGenerator:
    """二维码生成器"""
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("二维码生成器")
        self.window.geometry("400x300")
        
        ttk.Label(
            self.window, 
            text="此功能需要安装qrcode库\\npip install qrcode pillow",
            font=('Arial', 12)
        ).pack(expand=True)
        
        ttk.Button(self.window, text="关闭", command=self.window.destroy).pack(pady=10)

class TrafficMonitor:
    """流量监控"""
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("流量监控")
        self.window.geometry("400x300")
        
        ttk.Label(
            self.window,
            text="此功能需要安装psutil库\\npip install psutil",
            font=('Arial', 12)
        ).pack(expand=True)
        
        ttk.Button(self.window, text="关闭", command=self.window.destroy).pack(pady=10)

class SystemInfo:
    """系统信息"""
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("系统信息")
        self.window.geometry("400x300")
        
        import platform
        
        info = f"""
系统: {platform.system()} {platform.release()}
架构: {platform.machine()}
Python: {platform.python_version()}
计算机名: {platform.node()}
        """
        
        text = tk.Text(self.window)
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", info)
        text.config(state="disabled")
        
        ttk.Button(self.window, text="关闭", command=self.window.destroy).pack(pady=5)
''')
    
    print("\n✅ 所有文件创建完成！")
    print("\n现在可以运行: python main.py")

if __name__ == "__main__":
    print("=" * 50)
    print("  内网穿透工具 - 自动修复脚本")
    print("=" * 50)
    print()
    
    create_missing_files()
    
    print("\n按回车键退出...")
    input()