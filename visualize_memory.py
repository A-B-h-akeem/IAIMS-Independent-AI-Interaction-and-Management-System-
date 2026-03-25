import json
import os
import plotly.graph_objects as go
import networkx as nx
import numpy as np  # <-- ADD THIS IMPORT
from datetime import datetime
import random

# Load your Membrain memories
def load_memories():
    """Load memories from your local storage"""
    try:
        if os.path.exists("local_memories.json"):
            with open("local_memories.json", 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

# Create sample memories (replace with your actual data)
def get_sample_memories():
    """Use this if you don't have memories yet"""
    return [
        {"content": "WhatsApp message to Kaustav: Do your project", "tags": ["whatsapp", "communication"], "timestamp": "2024-01-15T10:30:00"},
        {"content": "Called Kaustav on WhatsApp", "tags": ["whatsapp", "call"], "timestamp": "2024-01-15T11:00:00"},
        {"content": "Added contact John with phone +1234567890", "tags": ["contact", "personal"], "timestamp": "2024-01-14T15:20:00"},
        {"content": "Meeting tomorrow at 3pm", "tags": ["meeting", "schedule"], "timestamp": "2024-01-14T09:15:00"},
        {"content": "John is my business partner", "tags": ["contact", "business"], "timestamp": "2024-01-13T14:45:00"},
        {"content": "Facebook post: Hello from ClawMind!", "tags": ["facebook", "social"], "timestamp": "2024-01-13T16:30:00"},
        {"content": "User phone number: +917411358375", "tags": ["personal", "contact"], "timestamp": "2024-01-12T12:00:00"},
        {"content": "Hackathon project deadline Friday", "tags": ["project", "deadline"], "timestamp": "2024-01-11T09:00:00"},
        {"content": "WhatsApp video call with team", "tags": ["whatsapp", "call", "video"], "timestamp": "2024-01-10T14:30:00"},
        {"content": "Remember to buy groceries", "tags": ["personal", "task"], "timestamp": "2024-01-09T18:00:00"},
        {"content": "ClawMind agent initialized", "tags": ["system", "setup"], "timestamp": "2024-01-08T10:00:00"}
    ]

def create_animated_graph():
    """Create an animated interactive graph visualization"""
    
    print("📊 Creating animated memory graph...")
    
    # Install numpy if not present
    try:
        import numpy as np
    except ImportError:
        print("⚠️ numpy not found. Installing...")
        import subprocess
        subprocess.run(["pip", "install", "numpy"])
        import numpy as np
    
    # Load your memories
    memories = load_memories()
    if not memories:
        print("No memories found, using sample data...")
        memories = get_sample_memories()
    
    print(f"Found {len(memories)} memories")
    
    # Create a graph
    G = nx.Graph()
    
    # Color mapping for different tag types
    tag_colors = {
        "whatsapp": "#25D366",  # WhatsApp green
        "call": "#FF9800",       # Orange
        "video": "#FF5252",      # Red
        "contact": "#2196F3",    # Blue
        "personal": "#9C27B0",   # Purple
        "business": "#FF5722",   # Deep Orange
        "facebook": "#1877F2",   # Facebook blue
        "social": "#E4405F",     # Pink
        "meeting": "#4CAF50",    # Green
        "schedule": "#FFC107",   # Amber
        "communication": "#00BCD4", # Cyan
        "project": "#3F51B5",    # Indigo
        "deadline": "#F44336",   # Red
        "task": "#FF9800",       # Orange
        "system": "#607D8B",     # Blue Grey
        "setup": "#009688",      # Teal
        "default": "#9E9E9E"     # Gray
    }
    
    # Add nodes (memories)
    for i, memory in enumerate(memories):
        # Get the main tag for color
        main_tag = memory.get('tags', ['default'])[0] if memory.get('tags') else 'default'
        color = tag_colors.get(main_tag, tag_colors['default'])
        
        # Truncate content for display
        display_content = memory['content'][:60] + "..." if len(memory['content']) > 60 else memory['content']
        
        G.add_node(
            i,
            label=display_content,
            full_content=memory['content'],
            tags=', '.join(memory.get('tags', [])),
            color=color,
            size=20 + (len(memory.get('tags', [])) * 5),
            timestamp=memory.get('timestamp', '')
        )
    
    # Add edges (connections based on shared tags)
    for i in range(len(memories)):
        for j in range(i + 1, len(memories)):
            tags_i = set(memories[i].get('tags', []))
            tags_j = set(memories[j].get('tags', []))
            shared = tags_i & tags_j
            
            if shared:
                # Connection strength based on how many shared tags
                strength = len(shared)
                G.add_edge(i, j, weight=strength, tags=list(shared))
    
    print(f"Created graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Create layout for node positions
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Prepare edge traces (lines between nodes)
    edge_traces = []
    
    # Create animated edges with varying opacity
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        
        # Edge weight affects thickness
        weight = edge[2].get('weight', 1)
        
        edge_trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(
                width=1 + weight,
                color='rgba(100, 150, 255, 0.5)',
                shape='spline'
            ),
            hoverinfo='none',
            showlegend=False
        )
        edge_traces.append(edge_trace)
    
    # Create node trace
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    
    for node in G.nodes(data=True):
        x, y = pos[node[0]]
        node_x.append(x)
        node_y.append(y)
        
        # Create hover text with memory details
        hover_text = f"<b>📝 {node[1]['label']}</b><br>"
        hover_text += f"🏷️ Tags: {node[1]['tags']}<br>"
        if node[1].get('timestamp'):
            hover_text += f"🕐 {node[1]['timestamp']}<br>"
        hover_text += f"🔗 Connections: {G.degree(node[0])}"
        
        node_text.append(hover_text)
        node_color.append(node[1]['color'])
        node_size.append(node[1]['size'])
    
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=[node[1]['label'][:20] + '...' for node in G.nodes(data=True)],
        textposition='top center',
        textfont=dict(size=10, color='white'),
        hovertext=node_text,
        hoverinfo='text',
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(color='white', width=2),
            symbol='circle',
            opacity=0.9
        ),
        showlegend=False
    )
    
    # Create the figure
    fig = go.Figure(data=edge_traces + [node_trace])
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"🧠 Membrain Memory Graph - {len(memories)} Memories, {G.number_of_edges()} Connections",
            font=dict(size=24, color='white'),
            x=0.5
        ),
        showlegend=False,
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(10, 20, 40, 1)',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        font=dict(color='white'),
        height=800,
        width=1400,
        annotations=[
            dict(
                text="🎮 Hover over nodes for details | Drag to pan | Scroll to zoom",
                x=0.5,
                y=-0.05,
                xref='paper',
                yref='paper',
                showarrow=False,
                font=dict(size=12, color='rgba(255,255,255,0.7)')
            )
        ]
    )
    
    # Save as HTML
    output_file = "memory_graph_animated.html"
    fig.write_html(
        output_file,
        include_plotlyjs='cdn',
        config={
            'displayModeBar': True,
            'scrollZoom': True,
            'responsive': True,
            'displaylogo': False
        }
    )
    
    print(f"\n✅ Graph created successfully!")
    print(f"📁 Saved to: {output_file}")
    print(f"📊 Stats: {len(memories)} memories, {G.number_of_edges()} connections")
    print("\n🌐 Opening in browser...")
    
    # Automatically open in browser
    import webbrowser
    webbrowser.open(f"file://{os.path.abspath(output_file)}")
    
    return output_file

# Run the visualization
if __name__ == "__main__":
    create_animated_graph()