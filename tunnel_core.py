import socket
import threading
import subprocess
import os
import time
from cryptography.fernet import Fernet
import struct

class TunnelManager:
    def __init__(self, log_callback):
        self.log = log_callback
        self.running = False
        self.threads = []
        self.sockets = []
        self.frp_process = None
        self.simple_tunnel = None
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
    def start_frp(self, config):
        """启动FRP客户端"""
        try:
            # 生成frpc配置文件
            frpc_config = self.generate_frpc_config(config)
            
            config_path = "frpc.ini"
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(frpc_config)
            
            # 检查frpc是否存在
            frpc_exe = "frpc.exe" if os.name == 'nt' else "frpc"
            if not os.path.exists(frpc_exe):
                self.log("错误: 找不到frpc程序，请下载frp客户端", "ERROR")
                return False
            
            # 启动frpc进程
            self.frp_process = subprocess.Popen(
                [frpc_exe, "-c", config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # 监控输出
            def monitor_output():
                for line in self.frp_process.stdout:
                    self.log(f"FRP: {line.strip()}")
            
            threading.Thread(target=monitor_output, daemon=True).start()
            
            self.log("FRP客户端已启动")
            return True
            
        except Exception as e:
            self.log(f"启动FRP失败: {str(e)}", "ERROR")
            return False
    
    def generate_frpc_config(self, config):
        """生成FRP配置文件"""
        cfg = f"""[common]
server_addr = {config['server_addr']}
server_port = {config['server_port']}
"""
        
        if config.get('token'):
            cfg += f"token = {config['token']}\n"
        
        cfg += "\n"
        
        # 添加各个映射
        for mapping in config['mappings']:
            cfg += f"""[{mapping['name']}]
type = {mapping['type']}
local_ip = 127.0.0.1
local_port = {mapping['local_port']}
remote_port = {mapping['remote_port']}

"""
        
        return cfg
    
    def stop_frp(self):
        """停止FRP"""
        if self.frp_process:
            self.frp_process.terminate()
            self.frp_process.wait(timeout=5)
            self.frp_process = None
            self.log("FRP客户端已停止")
    
    def start_simple_tunnel(self, listen_port, target_host, target_port, protocol="TCP", encrypt=False):
        """启动简单穿透"""
        try:
            self.running = True
            
            if protocol.upper() == "TCP":
                server = SimpleTCPTunnel(
                    listen_port, target_host, target_port, 
                    self.log, encrypt, self.cipher if encrypt else None
                )
            else:
                server = SimpleUDPTunnel(
                    listen_port, target_host, target_port, 
                    self.log
                )
            
            self.simple_tunnel = server
            
            # 在新线程中启动
            thread = threading.Thread(target=server.start, daemon=True)
            thread.start()
            self.threads.append(thread)
            
            self.log(f"简单穿透已启动 ({protocol}): {listen_port} -> {target_host}:{target_port}")
            return True
            
        except Exception as e:
            self.log(f"启动简单穿透失败: {str(e)}", "ERROR")
            return False
    
    def stop_simple_tunnel(self):
        """停止简单穿透"""
        if self.simple_tunnel:
            self.simple_tunnel.stop()
            self.simple_tunnel = None
            self.running = False
            self.log("简单穿透已停止")
    
    def start_game_tunnel(self, config):
        """启动游戏隧道"""
        return self.start_simple_tunnel(
            config['local_port'],
            "127.0.0.1",
            config['local_port'],
            config.get('type', 'tcp').upper()
        )
    
    def stop_game_tunnel(self):
        """停止游戏隧道"""
        self.stop_simple_tunnel()
    
    def start_vnc_tunnel(self, config):
        """启动VNC隧道"""
        return self.start_simple_tunnel(
            config['local_port'],
            "127.0.0.1",
            config['local_port'],
            "TCP"
        )
    
    def start_rdp_tunnel(self, config):
        """启动RDP隧道"""
        return self.start_simple_tunnel(
            config['local_port'],
            "127.0.0.1",
            config['local_port'],
            "TCP"
        )
    
    def stop_all(self):
        """停止所有服务"""
        self.stop_frp()
        self.stop_simple_tunnel()
        self.running = False


class SimpleTCPTunnel:
    """简单TCP穿透"""
    def __init__(self, listen_port, target_host, target_port, log_callback, encrypt=False, cipher=None):
        self.listen_port = listen_port
        self.target_host = target_host
        self.target_port = target_port
        self.log = log_callback
        self.running = False
        self.server_socket = None
        self.encrypt = encrypt
        self.cipher = cipher
        self.connections = []
        
    def start(self):
        """启动服务器"""
        try:
            self.running = True
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", self.listen_port))
            self.server_socket.listen(10)
            
            self.log(f"TCP隧道监听: {self.listen_port}")
            
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    client_socket, client_address = self.server_socket.accept()
                    self.log(f"新连接: {client_address}")
                    
                    # 为每个连接创建处理线程
                    thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket,),
                        daemon=True
                    )
                    thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.log(f"接受连接错误: {str(e)}", "ERROR")
                    break
                    
        except Exception as e:
            self.log(f"TCP隧道错误: {str(e)}", "ERROR")
        finally:
            self.stop()
    
    def handle_client(self, client_socket):
        """处理客户端连接"""
        target_socket = None
        try:
            # 连接到目标服务器
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((self.target_host, self.target_port))
            
            self.connections.append((client_socket, target_socket))
            
            # 双向转发数据
            def forward(source, destination, direction):
                try:
                    while self.running:
                        data = source.recv(8192)
                        if not data:
                            break
                        
                        # 加密处理
                        if self.encrypt and self.cipher:
                            if direction == "client_to_server":
                                data = self.cipher.encrypt(data)
                            else:
                                data = self.cipher.decrypt(data)
                        
                        destination.sendall(data)
                except Exception as e:
                    pass
                finally:
                    source.close()
                    destination.close()
            
            # 启动双向转发
            client_to_server = threading.Thread(
                target=forward,
                args=(client_socket, target_socket, "client_to_server"),
                daemon=True
            )
            server_to_client = threading.Thread(
                target=forward,
                args=(target_socket, client_socket, "server_to_client"),
                daemon=True
            )
            
            client_to_server.start()
            server_to_client.start()
            
            client_to_server.join()
            server_to_client.join()
            
        except Exception as e:
            self.log(f"转发错误: {str(e)}", "ERROR")
        finally:
            if client_socket:
                client_socket.close()
            if target_socket:
                target_socket.close()
    
    def stop(self):
        """停止服务器"""
        self.running = False
        
        # 关闭所有连接
        for client, target in self.connections:
            try:
                client.close()
                target.close()
            except:
                pass
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.log("TCP隧道已停止")


class SimpleUDPTunnel:
    """简单UDP穿透"""
    def __init__(self, listen_port, target_host, target_port, log_callback):
        self.listen_port = listen_port
        self.target_host = target_host
        self.target_port = target_port
        self.log = log_callback
        self.running = False
        self.server_socket = None
        self.client_map = {}  # 客户端地址映射
        
    def start(self):
        """启动UDP转发"""
        try:
            self.running = True
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.bind(("0.0.0.0", self.listen_port))
            
            self.log(f"UDP隧道监听: {self.listen_port}")
            
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    data, client_addr = self.server_socket.recvfrom(8192)
                    
                    # 转发到目标服务器
                    if client_addr not in self.client_map:
                        target_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        self.client_map[client_addr] = target_socket
                        
                        # 启动接收线程
                        thread = threading.Thread(
                            target=self.receive_from_target,
                            args=(target_socket, client_addr),
                            daemon=True
                        )
                        thread.start()
                    
                    target_socket = self.client_map[client_addr]
                    target_socket.sendto(data, (self.target_host, self.target_port))
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.log(f"UDP转发错误: {str(e)}", "ERROR")
                    
        except Exception as e:
            self.log(f"UDP隧道错误: {str(e)}", "ERROR")
        finally:
            self.stop()
    
    def receive_from_target(self, target_socket, client_addr):
        """从目标服务器接收数据"""
        try:
            while self.running:
                target_socket.settimeout(1.0)
                data, _ = target_socket.recvfrom(8192)
                self.server_socket.sendto(data, client_addr)
        except socket.timeout:
            pass
        except Exception as e:
            pass
    
    def stop(self):
        """停止服务器"""
        self.running = False
        
        # 关闭所有目标socket
        for target_socket in self.client_map.values():
            try:
                target_socket.close()
            except:
                pass
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.log("UDP隧道已停止")


class P2PTunnel:
    """P2P穿透 (NAT穿透)"""
    def __init__(self, log_callback):
        self.log = log_callback
        self.running = False
        
    def start_p2p(self, peer_ip, peer_port, local_port):
        """启动P2P连接"""
        try:
            self.running = True
            
            # 创建UDP socket进行打洞
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(("0.0.0.0", local_port))
            
            # 发送打洞包
            for _ in range(10):
                sock.sendto(b"PUNCH", (peer_ip, peer_port))
                time.sleep(0.1)
            
            self.log(f"P2P打洞完成: {peer_ip}:{peer_port}")
            
            # 开始接收数据
            while self.running:
                try:
                    sock.settimeout(1.0)
                    data, addr = sock.recvfrom(8192)
                    self.log(f"收到P2P数据: {addr}")
                except socket.timeout:
                    continue
                    
        except Exception as e:
            self.log(f"P2P连接错误: {str(e)}", "ERROR")
        finally:
            sock.close()
    
    def stop(self):
        """停止P2P"""
        self.running = False