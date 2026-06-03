import os
import threading
import http.server
import socketserver
from urllib.parse import unquote, quote
import mimetypes
import base64
import json

class AuthHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """带认证的HTTP请求处理器"""
    
    def __init__(self, *args, password=None, readonly=True, log_callback=None, **kwargs):
        self.password = password
        self.readonly = readonly
        self.log_callback = log_callback
        super().__init__(*args, **kwargs)
    
    def do_AUTHHEAD(self):
        """发送认证头"""
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="File Server"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    
    def check_auth(self):
        """检查认证"""
        if not self.password:
            return True
            
        auth_header = self.headers.get('Authorization')
        if auth_header is None:
            return False
            
        auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
        username, password = auth_decoded.split(':', 1)
        
        return password == self.password
    
    def do_GET(self):
        """处理GET请求"""
        if not self.check_auth():
            self.do_AUTHHEAD()
            self.wfile.write(b'Authentication required')
            return
        
        if self.log_callback:
            self.log_callback(f"GET请求: {self.path} 来自 {self.client_address[0]}")
        
        # 如果是根目录，显示文件列表
        if self.path == '/':
            self.list_directory_enhanced(self.translate_path(self.path))
        else:
            super().do_GET()
    
    def do_POST(self):
        """处理POST请求 (上传文件)"""
        if self.readonly:
            self.send_error(403, "只读模式")
            return
            
        if not self.check_auth():
            self.do_AUTHHEAD()
            self.wfile.write(b'Authentication required')
            return
        
        try:
            content_length = int(self.headers['Content-Length'])
            content_type = self.headers['Content-Type']
            
            if 'multipart/form-data' in content_type:
                # 处理文件上传
                boundary = content_type.split('boundary=')[1].encode()
                data = self.rfile.read(content_length)
                
                # 解析上传的文件
                self.parse_multipart(data, boundary)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'File uploaded successfully')
                
                if self.log_callback:
                    self.log_callback(f"文件上传成功 来自 {self.client_address[0]}")
            
        except Exception as e:
            self.send_error(500, f"Upload failed: {str(e)}")
            if self.log_callback:
                self.log_callback(f"上传失败: {str(e)}", "ERROR")
    
    def parse_multipart(self, data, boundary):
        """解析multipart数据"""
        parts = data.split(b'--' + boundary)
        for part in parts:
            if b'Content-Disposition' in part:
                # 提取文件名
                lines = part.split(b'\r\n')
                for i, line in enumerate(lines):
                    if b'filename=' in line:
                        filename = line.split(b'filename=')[1].strip(b'"').decode('utf-8')
                        # 文件内容从空行后开始
                        file_content = b'\r\n'.join(lines[i+2:]).rstrip(b'\r\n')
                        
                        # 保存文件
                        save_path = os.path.join(self.translate_path('/'), filename)
                        with open(save_path, 'wb') as f:
                            f.write(file_content)
                        break
    
    def list_directory_enhanced(self, path):
        """增强的目录列表"""
        try:
            file_list = os.listdir(path)
        except OSError:
            self.send_error(404, "Cannot list directory")
            return
        
        file_list.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
        
        # 生成HTML
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>文件分享</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                .container {
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    padding: 30px;
                }
                h1 {
                    color: #333;
                    margin-bottom: 20px;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 10px;
                }
                .upload-area {
                    border: 2px dashed #667eea;
                    border-radius: 8px;
                    padding: 30px;
                    text-align: center;
                    margin-bottom: 30px;
                    background: #f8f9ff;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                .upload-area:hover {
                    background: #e8ebff;
                    border-color: #764ba2;
                }
                .file-list {
                    list-style: none;
                }
                .file-item {
                    padding: 15px;
                    border-bottom: 1px solid #eee;
                    display: flex;
                    align-items: center;
                    transition: background 0.2s;
                }
                .file-item:hover {
                    background: #f5f5f5;
                }
                .file-icon {
                    width: 40px;
                    height: 40px;
                    margin-right: 15px;
                    font-size: 24px;
                }
                .file-info {
                    flex: 1;
                }
                .file-name {
                    font-weight: 500;
                    color: #333;
                    text-decoration: none;
                    display: block;
                    margin-bottom: 5px;
                }
                .file-name:hover {
                    color: #667eea;
                }
                .file-size {
                    color: #888;
                    font-size: 0.9em;
                }
                .stats {
                    background: #f8f9ff;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    display: flex;
                    justify-content: space-around;
                }
                .stat-item {
                    text-align: center;
                }
                .stat-value {
                    font-size: 1.5em;
                    font-weight: bold;
                    color: #667eea;
                }
                .stat-label {
                    color: #666;
                    font-size: 0.9em;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📁 文件分享服务器</h1>
                
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-value" id="fileCount">0</div>
                        <div class="stat-label">文件数</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="folderCount">0</div>
                        <div class="stat-label">文件夹数</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="totalSize">0 MB</div>
                        <div class="stat-label">总大小</div>
                    </div>
                </div>
        '''
        
        if not self.readonly:
            html += '''
                <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                    <h3>📤 点击上传文件</h3>
                    <p>或拖拽文件到此处</p>
                    <form id="uploadForm" enctype="multipart/form-data" method="post" style="display:none">
                        <input type="file" id="fileInput" name="file" multiple onchange="uploadFile()">
                    </form>
                </div>
            '''
        
        html += '<ul class="file-list">'
        
        file_count = 0
        folder_count = 0
        total_size = 0
        
        for name in file_list:
            fullname = os.path.join(path, name)
            displayname = name
            
            # 获取文件信息
            if os.path.isdir(fullname):
                icon = "📁"
                size = "-"
                folder_count += 1
            else:
                icon = self.get_file_icon(name)
                size_bytes = os.path.getsize(fullname)
                size = self.format_size(size_bytes)
                total_size += size_bytes
                file_count += 1
            
            html += f'''
                <li class="file-item">
                    <div class="file-icon">{icon}</div>
                    <div class="file-info">
                        <a href="{quote(name)}" class="file-name">{displayname}</a>
                        <div class="file-size">{size}</div>
                    </div>
                </li>
            '''
        
        html += f'''
                </ul>
            </div>
            <script>
                document.getElementById('fileCount').textContent = {file_count};
                document.getElementById('folderCount').textContent = {folder_count};
                document.getElementById('totalSize').textContent = '{self.format_size(total_size)}';
                
                function uploadFile() {{
                    const form = document.getElementById('uploadForm');
                    const formData = new FormData(form);
                    
                    fetch('/', {{
                        method: 'POST',
                        body: formData
                    }})
                    .then(response => response.text())
                    .then(data => {{
                        alert('上传成功!');
                        location.reload();
                    }})
                    .catch(error => {{
                        alert('上传失败: ' + error);
                    }});
                }}
                
                // 拖拽上传
                const uploadArea = document.querySelector('.upload-area');
                if (uploadArea) {{
                    uploadArea.addEventListener('dragover', (e) => {{
                        e.preventDefault();
                        uploadArea.style.background = '#e8ebff';
                    }});
                    
                    uploadArea.addEventListener('dragleave', () => {{
                        uploadArea.style.background = '#f8f9ff';
                    }});
                    
                    uploadArea.addEventListener('drop', (e) => {{
                        e.preventDefault();
                        uploadArea.style.background = '#f8f9ff';
                        
                        const files = e.dataTransfer.files;
                        const formData = new FormData();
                        for (let file of files) {{
                            formData.append('file', file);
                        }}
                        
                        fetch('/', {{
                            method: 'POST',
                            body: formData
                        }})
                        .then(response => response.text())
                        .then(data => {{
                            alert('上传成功!');
                            location.reload();
                        }})
                        .catch(error => {{
                            alert('上传失败: ' + error);
                        }});
                    }});
                }}
            </script>
        </body>
        </html>
        '''
        
        encoded = html.encode('utf-8')
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
    
    def get_file_icon(self, filename):
        """根据文件类型返回图标"""
        ext = os.path.splitext(filename)[1].lower()
        icons = {
            '.txt': '📄', '.pdf': '📕', '.doc': '📘', '.docx': '📘',
            '.xls': '📗', '.xlsx': '📗', '.ppt': '📙', '.pptx': '📙',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
            '.mp3': '🎵', '.wav': '🎵', '.mp4': '🎬', '.avi': '🎬',
            '.zip': '📦', '.rar': '📦', '.7z': '📦',
            '.py': '🐍', '.java': '☕', '.js': '📜', '.html': '🌐',
            '.exe': '⚙️', '.apk': '📱'
        }
        return icons.get(ext, '📄')
    
    def format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class FileServer:
    """文件服务器"""
    def __init__(self, log_callback):
        self.log = log_callback
        self.server = None
        self.thread = None
        self.running = False
        
    def start(self, directory, port, password=None, readonly=True):
        """启动文件服务器"""
        try:
            os.chdir(directory)
            
            # 创建处理器工厂
            def handler_factory(*args, **kwargs):
                return AuthHTTPRequestHandler(
                    *args,
                    password=password,
                    readonly=readonly,
                    log_callback=self.log,
                    **kwargs
                )
            
            self.server = socketserver.TCPServer(("", port), handler_factory)
            self.server.allow_reuse_address = True
            self.running = True
            
            # 在新线程中启动
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            
            self.log(f"文件服务器已启动: 端口 {port}")
            return True
            
        except Exception as e:
            self.log(f"启动文件服务器失败: {str(e)}", "ERROR")
            return False
    
    def stop(self):
        """停止文件服务器"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            self.log("文件服务器已停止")