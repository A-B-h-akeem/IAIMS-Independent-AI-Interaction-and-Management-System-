"""
visualize_3d.py  -  Real-time 3D Memory Graph for ClawMind / Membrain
Polls the Membrain API directly. No local file needed.

Requirements:
    pip install flask flask-sock requests networkx numpy

Usage:
    python visualize_3d.py
    python visualize_3d.py --port 8080
    python visualize_3d.py --interval 5
"""

import argparse
import json
import threading
import time
import webbrowser
from datetime import datetime

import networkx as nx
import numpy as np
import requests
from flask import Flask, render_template_string
from flask_sock import Sock

# Membrain config (copied from agent.py)
MEMBRAIN_API_KEY  = "mb_live_24j8Zn-9hTCSqMVgUhDeTtyVVfBVc1v1WBKla8WHhU8"
MEMBRAIN_BASE_URL = "https://mem-brain-api-cutover-v4-production.up.railway.app/api/v1"
MEMBRAIN_HEADERS  = {
    "X-API-Key":    MEMBRAIN_API_KEY,
    "Content-Type": "application/json",
}

# Several broad queries to pull as many memories as possible
FETCH_QUERIES = [
    "clawmind ishan hackathon project memory",
    "whatsapp facebook message call reminder",
    "user query ai response action result",
]

DEFAULT_PORT     = 5050
DEFAULT_INTERVAL = 4

COLOR_MAP = {
    "whatsapp":   "#25D366",
    "message":    "#4CAF50",
    "call":       "#FF9800",
    "user":       "#2196F3",
    "query":      "#00BCD4",
    "ai":         "#9C27B0",
    "response":   "#FF69B4",
    "permission": "#FFC107",
    "action":     "#FF5722",
    "success":    "#8BC34A",
    "memory":     "#3F51B5",
    "result":     "#009688",
    "reminder":   "#FF4081",
    "default":    "#9E9E9E",
}


def fetch_all_memories():
    seen, combined = set(), []
    for query in FETCH_QUERIES:
        try:
            res = requests.post(
                f"{MEMBRAIN_BASE_URL}/memories/search",
                headers=MEMBRAIN_HEADERS,
                json={"query": query, "k": 50},
                timeout=10,
            )
            if res.status_code != 200:
                continue
            data  = res.json()
            items = data if isinstance(data, list) else (
                data.get("results") or data.get("memories") or
                data.get("data")    or data.get("items") or []
            )
            for item in items:
                if isinstance(item, dict):
                    content = item.get("content") or item.get("text") or item.get("memory") or ""
                    tags    = item.get("tags", [])
                    ts      = item.get("timestamp") or item.get("created_at") or ""
                elif isinstance(item, str):
                    content, tags, ts = item, [], ""
                else:
                    continue
                content = content.strip()
                if content and content not in seen:
                    seen.add(content)
                    if not tags:
                        lower = content.lower()
                        tags  = [k for k in COLOR_MAP if k != "default" and k in lower]
                    combined.append({"content": content, "tags": tags, "timestamp": ts})
        except Exception as e:
            print(f"[poll] error ({query[:20]}...): {e}")
    return combined


def build_graph_data(memories):
    if not memories:
        return {"nodes": [], "edges": [], "stats": {"memories": 0, "connections": 0}, "updated_at": "-"}

    G = nx.Graph()
    for i, mem in enumerate(memories):
        tags  = mem.get("tags", [])
        color = next((COLOR_MAP[t] for t in tags if t in COLOR_MAP), COLOR_MAP["default"])
        G.add_node(i, label=mem["content"][:50], full=mem["content"],
                   tags=", ".join(tags) or "-", color=color,
                   timestamp=mem.get("timestamp", ""))

    for i in range(len(memories)):
        for j in range(i + 1, len(memories)):
            shared = set(memories[i].get("tags", [])) & set(memories[j].get("tags", []))
            if shared:
                G.add_edge(i, j, weight=len(shared))

    pos = nx.spring_layout(G, dim=3, seed=42, k=3, iterations=80)
    nodes = [{"id": n, "x": float(pos[n][0]), "y": float(pos[n][1]), "z": float(pos[n][2]),
               "label": d["label"], "full": d["full"], "tags": d["tags"],
               "color": d["color"], "timestamp": d["timestamp"],
               "degree": G.degree(n), "size": 12 + len(d["tags"].split(",")) * 2}
             for n, d in G.nodes(data=True)]
    edges = [{"x": [float(pos[u][0]), float(pos[v][0])],
               "y": [float(pos[u][1]), float(pos[v][1])],
               "z": [float(pos[u][2]), float(pos[v][2])]}
             for u, v in G.edges()]
    return {"nodes": nodes, "edges": edges,
            "stats": {"memories": len(memories), "connections": G.number_of_edges()},
            "updated_at": datetime.now().strftime("%H:%M:%S")}


class State:
    def __init__(self, interval):
        self.interval, self.lock = interval, threading.Lock()
        self.graph_data, self.clients, self._last_count = {}, [], -1

    def poll_loop(self):
        while True:
            try:
                mems = fetch_all_memories()
                if len(mems) != self._last_count:
                    self._last_count = len(mems)
                    data = build_graph_data(mems)
                    with self.lock:
                        self.graph_data = data
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {len(mems)} memories — pushing update...")
                    self.broadcast()
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] No change ({len(mems)} memories)")
            except Exception as e:
                print(f"[poll] loop error: {e}")
            time.sleep(self.interval)

    def broadcast(self):
        with self.lock:
            payload = json.dumps(self.graph_data)
        dead = []
        for ws in list(self.clients):
            try: ws.send(payload)
            except: dead.append(ws)
        for ws in dead:
            try: self.clients.remove(ws)
            except: pass


PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Membrain Live Graph</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#fff;font-family:'Segoe UI',sans-serif;overflow:hidden}
#graph{width:100vw;height:100vh}
#hud{position:fixed;top:12px;left:50%;transform:translateX(-50%);display:flex;gap:14px;align-items:center;z-index:10;background:rgba(0,0,0,.65);border:1px solid rgba(255,255,255,.2);border-radius:24px;padding:6px 20px;font-size:13px}
.pill{background:rgba(255,255,255,.08);border-radius:20px;padding:3px 12px}
#dot{width:9px;height:9px;border-radius:50%;background:#25D366;box-shadow:0 0 6px #25D366;animation:pulse 1.4s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
#toast{position:fixed;bottom:28px;left:50%;transform:translateX(-50%);background:rgba(37,211,102,.18);border:1px solid #25D366;color:#25D366;padding:8px 20px;border-radius:20px;font-size:13px;opacity:0;transition:opacity .4s;z-index:20;pointer-events:none}
</style>
</head>
<body>
<div id="hud">
  <span id="dot"></span>
  <span class="pill"><b>MEMBRAIN LIVE</b></span>
  <span class="pill">Memories: <b id="mem-count">-</b></span>
  <span class="pill">Connections: <b id="conn-count">-</b></span>
  <span class="pill">Updated: <b id="update-time">-</b></span>
</div>
<div id="toast"></div>
<div id="graph"></div>
<script>
const RNG=(a,b)=>Math.random()*(b-a)+a;
const N=(n,a,b)=>Array.from({length:n},()=>RNG(a,b));
const bg=[
  {type:'scatter3d',mode:'markers',x:N(1500,-20,20),y:N(1500,-15,15),z:N(1500,-25,25),marker:{size:N(1500,1,3),color:'white',opacity:.5,symbol:'circle'},hoverinfo:'none',showlegend:false},
  {type:'scatter3d',mode:'markers',x:N(800,-18,18),y:N(800,-13,13),z:N(800,-22,22),marker:{size:1.5,color:Array.from({length:800},()=>['#FF6B6B','#4ECDC4','#45B7D1','#96CEB4','#FFE5B4'][Math.floor(Math.random()*5)]),opacity:.4,symbol:'circle'},hoverinfo:'none',showlegend:false},
  {type:'scatter3d',mode:'markers',x:N(1000,-15,15),y:N(1000,-12,12),z:N(1000,-18,18),marker:{size:1,color:'rgba(255,255,255,.3)',symbol:'circle'},hoverinfo:'none',showlegend:false}
];
const eEdge={type:'scatter3d',mode:'lines',x:[],y:[],z:[],line:{color:'rgba(100,200,255,.6)',width:3},hoverinfo:'none',showlegend:false};
const eNode={type:'scatter3d',mode:'markers+text',x:[],y:[],z:[],text:[],textposition:'top center',textfont:{size:9,color:'white'},hovertext:[],hoverinfo:'text',marker:{size:[],color:[],opacity:.9,line:{color:'white',width:2},symbol:'circle'},showlegend:false};
const layout={paper_bgcolor:'black',plot_bgcolor:'black',font:{color:'white'},margin:{l:0,r:0,t:0,b:0},showlegend:false,scene:{bgcolor:'black',xaxis:{showbackground:false,showgrid:false,showticklabels:false,zeroline:false},yaxis:{showbackground:false,showgrid:false,showticklabels:false,zeroline:false},zaxis:{showbackground:false,showgrid:false,showticklabels:false,zeroline:false},camera:{eye:{x:10,y:10,z:8},up:{x:0,y:0,z:1}}}};
Plotly.newPlot('graph',[...bg,eEdge,eNode],layout,{displayModeBar:true,displaylogo:false,modeBarButtonsToRemove:['lasso2d','select2d']});

function toast(msg){const t=document.getElementById('toast');t.textContent=msg;t.style.opacity=1;setTimeout(()=>t.style.opacity=0,2400)}

function updateGraph(d){
  if(!d.nodes)return;
  const ex=[],ey=[],ez=[];
  (d.edges||[]).forEach(e=>{ex.push(e.x[0],e.x[1],null);ey.push(e.y[0],e.y[1],null);ez.push(e.z[0],e.z[1],null)});
  const nx=[],ny=[],nz=[],lbl=[],hvr=[],col=[],sz=[];
  (d.nodes||[]).forEach(n=>{
    nx.push(n.x);ny.push(n.y);nz.push(n.z);
    lbl.push((n.label||'').slice(0,15)+'...');
    hvr.push('<b>'+n.label+'</b><br>Tags: '+n.tags+'<br>'+n.timestamp+'<br>Connections: '+n.degree);
    col.push(n.color);sz.push(n.size);
  });
  Plotly.update('graph',{x:[ex],y:[ey],z:[ez]},{},[ 3]);
  Plotly.update('graph',{x:[nx],y:[ny],z:[nz],text:[lbl],hovertext:[hvr],'marker.color':[col],'marker.size':[sz]},{},[ 4]);
  document.getElementById('mem-count').textContent =d.stats?d.stats.memories:'-';
  document.getElementById('conn-count').textContent=d.stats?d.stats.connections:'-';
  document.getElementById('update-time').textContent=d.updated_at||'-';
}

function connect(){
  const ws=new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws');
  ws.onopen=()=>console.log('WS connected');
  ws.onclose=()=>{console.warn('WS closed, retrying...');setTimeout(connect,3000)};
  ws.onmessage=e=>{try{const d=JSON.parse(e.data);updateGraph(d);toast('Updated: '+(d.stats?d.stats.memories:'?')+' memories')}catch(x){console.error(x)}};
}
connect();
</script>
</body>
</html>"""


app  = Flask(__name__)
sock = Sock(app)
state = None


@app.route("/")
def index():
    return render_template_string(PAGE_HTML)


@sock.route("/ws")
def websocket(ws):
    with state.lock:
        payload = json.dumps(state.graph_data)
    ws.send(payload)
    state.clients.append(ws)
    try:
        while True:
            ws.receive(timeout=30)
    except Exception:
        pass
    finally:
        try: state.clients.remove(ws)
        except ValueError: pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port",       type=int, default=DEFAULT_PORT)
    parser.add_argument("--interval",   type=int, default=DEFAULT_INTERVAL)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    global state
    state = State(args.interval)

    print("Fetching memories from Membrain API...")
    mems = fetch_all_memories()
    state.graph_data  = build_graph_data(mems)
    state._last_count = len(mems)
    print(f"Loaded {len(mems)} memories")

    threading.Thread(target=state.poll_loop, daemon=True).start()

    if not args.no_browser:
        threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{args.port}")).start()

    print(f"\nLive graph at http://localhost:{args.port}")
    print(f"Polling Membrain every {args.interval}s  |  Ctrl+C to stop\n")
    app.run(host="0.0.0.0", port=args.port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()