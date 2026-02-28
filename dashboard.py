import http.server
import socketserver
import json
import os

# Configuration
PORT = 8000
STORAGE_DIR = "storage"
METADATA_FILE = "metadata.json"
CHUNK_SIZE = 4096

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def get_stats(self):
        if not os.path.exists(METADATA_FILE):
            return {"files": {}, "logical": 0, "actual": 0, "saved": 0, "efficiency": 0}
        
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
            
        total_logical_size = 0
        for hashes in metadata.values():
            total_logical_size += len(hashes) * CHUNK_SIZE
            
        actual_storage_size = 0
        if os.path.exists(STORAGE_DIR):
            for chunk_name in os.listdir(STORAGE_DIR):
                actual_storage_size += os.path.getsize(os.path.join(STORAGE_DIR, chunk_name))
                
        saved_space = total_logical_size - actual_storage_size
        efficiency = (saved_space / total_logical_size * 100) if total_logical_size > 0 else 0
        
        return {
            "files": metadata,
            "logical": total_logical_size,
            "actual": actual_storage_size,
            "saved": saved_space,
            "efficiency": efficiency
        }

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            stats = self.get_stats()
            
            html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Deduplication Dashboard</title>
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
                <style>
                    :root {{
                        --primary: #6366f1;
                        --bg: #0f172a;
                        --card: #1e293b;
                        --text: #f8fafc;
                        --text-dim: #94a3b8;
                        --accent: #38bdf8;
                    }}
                    body {{
                        font-family: 'Inter', sans-serif;
                        background-color: var(--bg);
                        color: var(--text);
                        margin: 0;
                        padding: 40px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    }}
                    .container {{
                        max-width: 1000px;
                        width: 100%;
                    }}
                    header {{
                        margin-bottom: 40px;
                        text-align: center;
                    }}
                    h1 {{
                        font-size: 2.5rem;
                        font-weight: 700;
                        background: linear-gradient(to right, #818cf8, #c084fc);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        margin-bottom: 10px;
                    }}
                    .stats-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                        margin-bottom: 40px;
                    }}
                    .card {{
                        background: var(--card);
                        border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 16px;
                        padding: 24px;
                        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                        transition: transform 0.2s;
                    }}
                    .card:hover {{
                        transform: translateY(-5px);
                        border-color: var(--primary);
                    }}
                    .card-label {{
                        font-size: 0.875rem;
                        color: var(--text-dim);
                        margin-bottom: 8px;
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                    }}
                    .card-value {{
                        font-size: 1.5rem;
                        font-weight: 600;
                    }}
                    .efficiency-bar-container {{
                        width: 100%;
                        height: 12px;
                        background: #334155;
                        border-radius: 6px;
                        margin-top: 20px;
                        overflow: hidden;
                    }}
                    .efficiency-bar {{
                        height: 100%;
                        background: linear-gradient(90deg, var(--primary), var(--accent));
                        width: {stats['efficiency']}%;
                        transition: width 1s ease-out;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        background: var(--card);
                        border-radius: 16px;
                        overflow: hidden;
                        border: 1px solid rgba(255,255,255,0.1);
                    }}
                    th, td {{
                        padding: 16px 24px;
                        text-align: left;
                    }}
                    th {{
                        background: rgba(255,255,255,0.05);
                        font-weight: 600;
                        color: var(--text-dim);
                        font-size: 0.75rem;
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                    }}
                    tr:not(:last-child) {{
                        border-bottom: 1px solid rgba(255,255,255,0.05);
                    }}
                    .status-active {{
                        color: #4ade80;
                        background: rgba(74, 222, 128, 0.1);
                        padding: 4px 12px;
                        border-radius: 12px;
                        font-size: 0.75rem;
                    }}
                    .refresh-btn {{
                        background: var(--primary);
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: 600;
                        margin-bottom: 20px;
                        transition: filter 0.2s;
                    }}
                    .refresh-btn:hover {{
                        filter: brightness(1.1);
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <header>
                        <h1>Intelligent Deduplication Dashboard</h1>
                        <p style="color: var(--text-dim)">Real-time storage optimization statistics</p>
                    </header>

                    <div class="stats-grid">
                        <div class="card">
                            <div class="card-label">Logical Size</div>
                            <div class="card-value">{stats['logical'] / 1024:.2f} KB</div>
                        </div>
                        <div class="card">
                            <div class="card-label">Actual Stored</div>
                            <div class="card-value">{stats['actual'] / 1024:.2f} KB</div>
                        </div>
                        <div class="card">
                            <div class="card-label">Space Saved</div>
                            <div class="card-value">{stats['saved'] / 1024:.2f} KB</div>
                        </div>
                        <div class="card">
                            <div class="card-label">Efficiency Ratio</div>
                            <div class="card-value">{stats['efficiency']:.1f}%</div>
                            <div class="efficiency-bar-container">
                                <div class="efficiency-bar"></div>
                            </div>
                        </div>
                    </div>

                    <button class="refresh-btn" onclick="window.location.reload()">Refresh Data</button>

                    <table>
                        <thead>
                            <tr>
                                <th>Filename</th>
                                <th>Total Chunks</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f"<tr><td>{f}</td><td>{len(h)}</td><td><span class='status-active'>Optimized</span></td></tr>" for f, h in stats['files'].items()])}
                        </tbody>
                    </table>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404)

def run_server():
    print(f"Starting dashboard at http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
