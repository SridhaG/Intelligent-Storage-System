import http.server
import socketserver
import json
import os
import hashlib
import io
import re

# Configuration
PORT = 8000
STORAGE_DIR = "storage"
METADATA_FILE = "metadata.json"
CHUNK_SIZE = 4096

def ensure_directories():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

def get_file_hash(data):
    return hashlib.sha256(data).hexdigest()

def load_metadata():
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_metadata(metadata):
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=4)

def dedup_file(filename, file_data):
    metadata = load_metadata()
    if filename in metadata:
        return False, "File already exists"

    ensure_directories()
    chunk_hashes = []
    
    stream = io.BytesIO(file_data)
    while True:
        chunk = stream.read(CHUNK_SIZE)
        if not chunk:
            break
        
        chunk_hash = get_file_hash(chunk)
        chunk_hashes.append(chunk_hash)
        
        chunk_path = os.path.join(STORAGE_DIR, chunk_hash)
        if not os.path.exists(chunk_path):
            with open(chunk_path, 'wb') as f:
                f.write(chunk)
                
    metadata[filename] = chunk_hashes
    save_metadata(metadata)
    return True, "Success"

def reconstruct_file_data(filename):
    metadata = load_metadata()
    if filename not in metadata:
        return None
    
    hashes = metadata[filename]
    output = io.BytesIO()
    for h in hashes:
        path = os.path.join(STORAGE_DIR, h)
        if not os.path.exists(path):
            return None
        with open(path, 'rb') as f:
            output.write(f.read())
            
    return output.getvalue()

class FullStackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            if os.path.exists('index.html'):
                with open('index.html', 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b"index.html not found.")
        
        elif self.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            metadata = load_metadata()
            total_logical = sum(len(h) * CHUNK_SIZE for h in metadata.values())
            
            actual = 0
            if os.path.exists(STORAGE_DIR):
                for f in os.listdir(STORAGE_DIR):
                    actual += os.path.getsize(os.path.join(STORAGE_DIR, f))
            
            stats = {
                "logical": total_logical,
                "actual": actual,
                "saved": total_logical - actual,
                "efficiency": (1 - actual/total_logical)*100 if total_logical > 0 else 0,
                "files": [{"name": k, "chunks": len(v)} for k, v in metadata.items()]
            }
            self.wfile.write(json.dumps(stats).encode())

        elif self.path.startswith('/api/download/'):
            filename = self.path[len('/api/download/'):]
            data = reconstruct_file_data(filename)
            if data:
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error(404, "File not found")

    def do_POST(self):
        if self.path == '/api/upload':
            content_type = self.headers.get('Content-Type')
            if not content_type or 'multipart/form-data' not in content_type:
                self.send_error(400, "Bad Request: Expected multipart/form-data")
                return

            try:
                content_length = int(self.headers.get('Content-Length'))
            except (TypeError, ValueError):
                self.send_error(400, "Bad Request: Invalid Content-Length")
                return

            body = self.rfile.read(content_length)
            
            # Simple boundary parsing
            boundary = content_type.split("boundary=")[-1].encode()
            parts = body.split(b'--' + boundary)
            
            filename = None
            file_data = None
            
            for part in parts:
                if b'Content-Disposition' in part and b'name="file"' in part:
                    # Find filename
                    fn_match = re.search(b'filename="([^"]+)"', part)
                    if fn_match:
                        filename = fn_match.group(1).decode()
                    
                    # Extract file content (after headers, separated by double CRLF)
                    header_end = part.find(b'\r\n\r\n')
                    if header_end != -1:
                        file_data = part[header_end+4:].rstrip(b'\r\n--')
            
            if filename and file_data:
                success, msg = dedup_file(filename, file_data)
                self.send_response(200 if success else 400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": success, "message": msg}).encode())
            else:
                self.send_error(400, "Bad Request: File not found in upload")

def run_server():
    print(f"Starting Full Stack System at http://localhost:{PORT}")
    server = socketserver.TCPServer(("", PORT), FullStackHandler)
    server.allow_reuse_address = True # Faster restarts
    server.serve_forever()

if __name__ == "__main__":
    ensure_directories()
    run_server()
