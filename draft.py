import os
import json
import time
import requests
from dotenv import load_dotenv   # Optional but recommended
import subprocess
import time
import pygetwindow as gw
import pyautogui
import webbrowser
from datetime import datetime
import pyperclip  # Add this to your imports at the top
import urllib.parse
FACEBOOK_LOG_FILE = "facebook_log.json"

def load_facebook_log():
    """Load Facebook activity log"""
    try:
        if os.path.exists(FACEBOOK_LOG_FILE):
            with open(FACEBOOK_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"posts": [], "comments": [], "photos": []}

def save_facebook_log(log_data):
    """Save Facebook activity log"""
    try:
        with open(FACEBOOK_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        return True
    except:
        return False

def log_facebook_post(content, post_type="text"):
    """Log a Facebook post"""
    log = load_facebook_log()
    log["posts"].append({
        "content": content[:200],
        "type": post_type,
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S")
    })
    save_facebook_log(log)
    save_memory(f"Posted on Facebook: {content[:100]}...", ["facebook", "post"])

def post_facebook_status(message):
    """Post a regular status update (not a story)"""
    print(f"\n💬 [Posting status to Facebook: {message[:50]}...]")
    
    try:
        webbrowser.open("https://www.facebook.com")
        time.sleep(6)
        
        # Find browser window
        browser_windows = (
            gw.getWindowsWithTitle('Chrome') or
            gw.getWindowsWithTitle('Edge') or
            gw.getWindowsWithTitle('Facebook')
        )
        
        if not browser_windows:
            return "❌ Could not find browser window"
        
        window = browser_windows[0]
        window.activate()
        time.sleep(1.5)

        # Force-navigate via address bar to avoid stale tabs
        print("🌐 Navigating to facebook.com...")
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.5)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.typewrite('https://www.facebook.com', interval=0.05)
        pyautogui.press('enter')
        time.sleep(6)

        screen_width, screen_height = pyautogui.size()

        # Click "What's on your mind?" box — centered feed, just below navbar
        post_x = int(screen_width * 0.50)
        post_y = int(screen_height * 0.26)

        print(f"📝 Clicking 'What's on your mind?' at ({post_x}, {post_y})...")
        pyautogui.click(post_x, post_y)
        time.sleep(3)   # Wait for composer dialog to fully open

        # Paste message via clipboard
        print(f"📋 Pasting message...")
        pyperclip.copy(message)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1.5)

        # Click the blue "Post" button directly
        # From screenshot: dialog is centered, Post button is at ~50% X, ~75% Y
        post_btn_x = int(screen_width * 0.50)
        post_btn_y = int(screen_height * 0.75)

        print(f"📤 Clicking Post button at ({post_btn_x}, {post_btn_y})...")
        pyautogui.click(post_btn_x, post_btn_y)
        time.sleep(3)

        log_facebook_post(message, "status")
        return f"✅ Facebook status posted!\n   📝 {message}"
        
    except Exception as e:
        return f"❌ Error: {str(e)}"




def post_facebook_photo(image_path, caption=""):
    """Post a photo to Facebook using direct upload URL"""
    print(f"\n📸 [Posting photo to Facebook: {image_path}]")
    
    try:
        # Check if image exists
        if not os.path.exists(image_path):
            pictures_dir = os.path.expanduser("~/Pictures")
            test_path = os.path.join(pictures_dir, image_path)
            if os.path.exists(test_path):
                image_path = test_path
            else:
                return f"❌ Image not found: {image_path}"
        
        # Open Facebook's direct photo upload page
        print("📂 Opening Facebook photo upload...")
        webbrowser.open("https://www.facebook.com/photos/upload")
        time.sleep(4)
        
        # Find browser window
        browser_windows = gw.getWindowsWithTitle('Facebook')
        if not browser_windows:
            browser_windows = gw.getWindowsWithTitle('Chrome')
        
        if browser_windows:
            window = browser_windows[0]
            window.activate()
            time.sleep(2)
            
            # The file dialog should appear automatically
            # If not, try to trigger it with Ctrl+V
            print("📁 Selecting image file...")
            
            # Copy image path to clipboard
            pyperclip.copy(image_path)
            time.sleep(0.5)
            
            # Try to paste and open file dialog
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(3)  # Wait for upload
            
            # Add caption if provided
            if caption:
                print("📝 Adding caption...")
                pyautogui.press('tab')
                time.sleep(0.5)
                pyautogui.write(caption, interval=0.05)
                time.sleep(1)
            
            # Post it
            print("📤 Posting...")
            pyautogui.press('tab')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(2)
            
            # Log the post
            log_facebook_post(f"Photo: {os.path.basename(image_path)} - {caption}", "photo")
            
            return f"✅ Photo posted to Facebook!\n   📸 {os.path.basename(image_path)}\n   📝 {caption}"
        else:
            return "❌ Could not find browser window."
        
    except Exception as e:
        return f"❌ Error posting photo: {str(e)}"

def open_facebook():
    """Open Facebook in browser"""
    webbrowser.open("https://www.facebook.com")
    time.sleep(3)
    return "✅ Facebook opened in browser!"

def check_facebook_posts(limit=5):
    """Get recent Facebook posts (from log)"""
    log = load_facebook_log()
    posts = log["posts"][-limit:][::-1]
    
    if not posts:
        return "No Facebook posts recorded yet."
    
    result = f"📱 Recent Facebook posts:\n"
    for post in posts:
        result += f"  • {post['time']} - {post['type'].upper()}: {post['content'][:80]}...\n"
    return result

def list_available_photos():
    """List available photos in Pictures folder"""
    photo_dir = os.path.expanduser("~/Pictures")
    try:
        photos = [f for f in os.listdir(photo_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
        if photos:
            return f"📸 Available photos in {photo_dir}:\n" + "\n".join(f"  • {p}" for p in photos[:15])
        else:
            return f"No photos found in {photo_dir}"
    except:
        return f"Could not access {photo_dir}"

def facebook_tool(action_type, image_path=None, caption=None, message=None):
    """Main Facebook automation tool"""
    print(f"\n📘 [Facebook Action: {action_type.upper()}]")
    
    try:
        if action_type == "open":
            return open_facebook()
        
        elif action_type == "post_status":
            if not message:
                return "❌ Please provide a status message."
            return post_facebook_status(message)
        
        elif action_type == "post_photo":
            if not image_path:
                return "❌ Please provide an image path."
            return post_facebook_photo(image_path, caption or "")
        
        elif action_type == "check_posts":
            return check_facebook_posts()
        
        elif action_type == "list_photos":
            return list_available_photos()
        
        return f"Unknown Facebook action: {action_type}"
        
    except Exception as e:
        return f"❌ Facebook error: {str(e)}"

# Add this to track WhatsApp communications
WHATSAPP_LOG_FILE = "whatsapp_log.json"

def load_whatsapp_log():
    """Load WhatsApp communication log"""
    try:
        if os.path.exists(WHATSAPP_LOG_FILE):
            with open(WHATSAPP_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"calls": [], "messages": []}

def save_whatsapp_log(log_data):
    """Save WhatsApp communication log"""
    try:
        with open(WHATSAPP_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        return True
    except:
        return False

def log_whatsapp_call(contact, call_type="audio", status="initiated"):
    """Log a WhatsApp call"""
    log = load_whatsapp_log()
    log["calls"].append({
        "contact": contact,
        "call_type": call_type,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S")
    })
    save_whatsapp_log(log)
    
    # Also save to Membrain memory
    save_memory(f"Made WhatsApp {call_type} call to {contact} at {datetime.now().strftime('%H:%M')}", 
                ["whatsapp", "call", contact])

def log_whatsapp_message(contact, message, direction="sent"):
    """Log a WhatsApp message"""
    log = load_whatsapp_log()
    log["messages"].append({
        "contact": contact,
        "message": message[:100],  # Truncate long messages
        "direction": direction,
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S")
    })
    save_whatsapp_log(log)
    
    # Also save to Membrain memory
    save_memory(f"{direction.title()} WhatsApp message to {contact}: {message[:50]}...", 
                ["whatsapp", "message", contact])

def get_whatsapp_calls_today(contact=None):
    """Get WhatsApp calls for today, optionally filtered by contact"""
    log = load_whatsapp_log()
    today = datetime.now().strftime("%Y-%m-%d")
    
    today_calls = [call for call in log["calls"] if call["date"] == today]
    
    if contact:
        today_calls = [call for call in today_calls if contact.lower() in call["contact"].lower()]
    
    return today_calls

def get_whatsapp_messages(contact=None, limit=10):
    """Get recent WhatsApp messages, optionally filtered by contact"""
    log = load_whatsapp_log()
    messages = log["messages"][-limit:]  # Get last N messages
    
    if contact:
        messages = [msg for msg in messages if contact.lower() in msg["contact"].lower()]
    
    return messages[::-1]  # Reverse to show newest first

def get_last_message(contact):
    """Get the last message from a specific contact"""
    messages = get_whatsapp_messages(contact, limit=1)
    if messages:
        return messages[0]
    return None

def whatsapp_call(contact, call_type="audio"):
    """
    Make a WhatsApp audio or video call by clicking the Call button directly.
    call_type: "audio" or "video"
    """
    print(f"\n📞 [WhatsApp {call_type.title()} Call → {contact}]")

    try:
        # Open WhatsApp Desktop
        subprocess.Popen(["start", "whatsapp:"], shell=True)
        time.sleep(4)

        # Find WhatsApp window
        whatsapp_windows = gw.getWindowsWithTitle('WhatsApp')
        if not whatsapp_windows:
            whatsapp_windows = gw.getWindowsWithTitle('WhatsApp Desktop')
        if not whatsapp_windows:
            return "❌ WhatsApp window not found. Is WhatsApp Desktop installed?"

        window = whatsapp_windows[0]
        window.activate()
        time.sleep(1.5)

        win_x = window.left
        win_y = window.top
        win_w = window.width
        win_h = window.height
        print(f"📐 WhatsApp window: x={win_x}, y={win_y}, w={win_w}, h={win_h}")

        # ── Step 1: Search for contact ─────────────────────────────────
        print("🔍 Searching for contact...")
        pyautogui.hotkey('ctrl', 'n')
        time.sleep(1.5)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('delete')
        time.sleep(0.3)
        pyperclip.copy(contact)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(2)

        # ── Step 2: Open the chat ──────────────────────────────────────
        pyautogui.press('enter')
        time.sleep(2)

        # ── Step 3: Click the "Call ▾" dropdown button ────────────────
        call_btn_x = win_x + int(win_w * 0.880)
        call_btn_y = win_y + int(win_h * 0.085)
        print(f"📞 Clicking Call dropdown at ({call_btn_x}, {call_btn_y})...")
        pyautogui.click(call_btn_x, call_btn_y)
        time.sleep(1.5)  # Wait for dropdown to appear

        # ── Step 4: Click Voice or Video from the dropdown ────────────
        # From your screenshot, the dropdown shows two big green buttons:
        #   "Voice" — left button at ~75% X, ~24% Y of window
        #   "Video" — right button at ~87% X, ~24% Y of window

        if call_type == "video":
            btn_x = win_x + int(win_w * 0.870)
            btn_y = win_y + int(win_h * 0.240)
            print(f"📹 Clicking Video button at ({btn_x}, {btn_y})...")
        else:
            btn_x = win_x + int(win_w * 0.748)
            btn_y = win_y + int(win_h * 0.240)
            print(f"🔊 Clicking Voice button at ({btn_x}, {btn_y})...")

        pyautogui.click(btn_x, btn_y)
        time.sleep(2)

        # Log the call
        log_whatsapp_call(contact, call_type, "initiated")
        return f"📞 {call_type.title()} call started with {contact} on WhatsApp!"

    except Exception as e:
        return f"❌ Call error: {str(e)}"




def whatsapp_tool(action_type, contact=None, message=None, call_type="audio"):
    """Open and control WhatsApp on Windows with logging"""
    print(f"\n💬 [WhatsApp Action: {action_type.upper()} → {contact or 'App'}]")

    try:
        if action_type == "open":
            subprocess.Popen(["start", "whatsapp:"], shell=True)
            time.sleep(2)
            return "✅ WhatsApp opened successfully!"

        elif action_type == "send" and contact and message:
            subprocess.Popen(["start", "whatsapp:"], shell=True)
            time.sleep(4)

            whatsapp_windows = gw.getWindowsWithTitle('WhatsApp')
            if not whatsapp_windows:
                whatsapp_windows = gw.getWindowsWithTitle('WhatsApp Desktop')

            if whatsapp_windows:
                window = whatsapp_windows[0]
                window.activate()
                time.sleep(2)

                print("📝 Searching for contact...")
                pyautogui.hotkey('ctrl', 'n')
                time.sleep(1.5)
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('delete')
                time.sleep(0.5)

                for char in contact:
                    pyautogui.write(char)
                    time.sleep(0.05)
                time.sleep(2)

                pyautogui.press('enter')
                time.sleep(1.5)

                print("📝 Typing message...")
                pyperclip.copy(message)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.5)

                pyautogui.press('enter')
                time.sleep(0.5)

                log_whatsapp_message(contact, message, "sent")
                return f"✅ WhatsApp message sent to {contact}!"
            else:
                return "❌ WhatsApp window not found."

        elif action_type == "call" and contact:
            # Use the new robust call function
            return whatsapp_call(contact, call_type)

        elif action_type == "check_calls":
            today_calls = get_whatsapp_calls_today(contact)
            if not today_calls:
                return f"No WhatsApp calls to {contact} found today." if contact else "No WhatsApp calls found today."
            result = f"📞 Found {len(today_calls)} WhatsApp call(s) today:\n"
            for call in today_calls:
                result += f"  • {call['time']} - {call['call_type'].title()} call to {call['contact']} ({call['status']})\n"
            return result

        elif action_type == "last_message":
            if not contact:
                return "Please specify a contact name."
            last_msg = get_last_message(contact)
            if last_msg:
                return f"📨 Last message from {contact} at {last_msg['time']}:\n   {last_msg['message']}"
            return f"No recorded messages from {contact}."

        elif action_type == "recent_messages":
            messages = get_whatsapp_messages(contact, limit=5)
            if not messages:
                return "No messages found."
            result = "📨 Recent WhatsApp messages:\n"
            for msg in messages:
                icon = "📤" if msg['direction'] == "sent" else "📥"
                result += f"  {icon} {msg['time']} - {msg['contact']}: {msg['message'][:50]}...\n"
            return result

        return f"Unknown action: {action_type}"

    except Exception as e:
        return f"❌ Error: {str(e)}"

# ===================== CONFIG =====================
load_dotenv()  # If you want to use .env file later

# OpenRouter Configuration (replace Groq)
OPENROUTER_API_KEY = "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"  # Get from https://openrouter.ai/keys
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Choose your model (free options available)
# Free models:
# - "meta-llama/llama-3.3-70b-instruct" (Llama 3.3 70B)
# - "meta-llama/llama-3.2-3b-instruct" (Llama 3.2 3B, faster)
# - "microsoft/phi-3-mini-128k-instruct" (Phi-3 Mini)
# - "google/gemini-flash-1.5" (Gemini Flash)
MODEL = "meta-llama/llama-3.3-70b-instruct"

# Membrain Configuration (unchanged)
MEMBRAIN_API_KEY = "mb_live_znz--Wuae4XfPR2mh1p1DYSt-lbHSBOk6K2Up4-Thc8"
MEMBRAIN_BASE_URL = "https://mem-brain-api-cutover-v4-production.up.railway.app/api/v1"

# Headers for OpenRouter
openrouter_headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:3000",  # Optional, for OpenRouter rankings
    "X-Title": "ClawMind Agent"  # Identifies your app
}

# Membrain headers (unchanged)
membrain_headers = {
    "X-API-Key": MEMBRAIN_API_KEY,
    "Content-Type": "application/json"
}

# ===================== MEMORY TOOLS =====================
def search_membrain(query: str, k: int = 15):
    print(f"\n🔍 [Searching Memory: '{query}']...")

    # Smart default for recall questions
    if any(word in query.lower() for word in ["recall", "remember", "everything", "past", "previous"]):
        search_term = "hackathon meeting exam birthday schedule project clawmind ishan"
    else:
        search_term = query

    payload = {"query": search_term, "k": k}

    try:
        res = requests.post(f"{MEMBRAIN_BASE_URL}/memories/search", headers=membrain_headers, json=payload, timeout=10)
        
        if res.status_code != 200:
            print(f"❌ API Error {res.status_code}: {res.text}")
            return "Memory database is currently unreachable."

        data = res.json()
        # print(f"🔎 RAW RESPONSE: {json.dumps(data, indent=2)}")   # Uncomment for debugging

        memories = []

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    content = item.get('content') or item.get('text') or item.get('memory')
                    if content:
                        memories.append(str(content).strip())
                elif isinstance(item, str):
                    memories.append(item.strip())

        elif isinstance(data, dict):
            # Try common keys
            items = data.get('results') or data.get('memories') or data.get('data') or data.get('items') or []
            if not isinstance(items, list):
                items = [items]
            for item in items:
                if isinstance(item, dict):
                    content = item.get('content') or item.get('text') or item.get('memory')
                    if content:
                        memories.append(str(content).strip())
                elif isinstance(item, str):
                    memories.append(item.strip())

        if not memories:
            return "No prior context found in the graph database."

        return "CRITICAL LONG-TERM MEMORY FOUND:\n" + "\n\n".join(memories)

    except Exception as e:
        print(f"Search exception: {e}")
        return f"Database connection error: {e}"


def save_memory(fact: str, tags: list = None):
    if tags is None:
        tags = []
    print(f"\n💾 [Saving: '{fact[:100]}...']")

    payload = {
        "content": fact,
        "tags": tags + ["clawmind", "hackathon", "ishan"]
    }

    try:
        response = requests.post(f"{MEMBRAIN_BASE_URL}/memories", headers=membrain_headers, json=payload, timeout=10)
        response.raise_for_status()
        job_id = response.json().get("job_id")

        for _ in range(25):   # Max ~25 seconds polling
            time.sleep(1)
            poll_res = requests.get(f"{MEMBRAIN_BASE_URL}/memories/jobs/{job_id}", headers=membrain_headers, timeout=10)
            poll_res.raise_for_status()
            status_data = poll_res.json()

            if status_data.get("status") == "completed":
                print("✅ Memory saved & linked successfully!")
                return "SUCCESS: Memory permanently saved in graph."
            elif status_data.get("status") == "failed":
                return f"FAILED: {status_data.get('error', 'Unknown error')}"

        return "Save request timed out."
    except Exception as e:
        print(f"Save error: {e}")
        return f"Save tool failed: {e}"


# ===================== FILE SYSTEM TOOL =====================
def manage_local_file(method: str, file_path: str, content: str = None):
    print(f"\n📂 [File System: {method.upper()} → {file_path}]")

    try:
        if method == "list":
            files = os.listdir(file_path or ".")
            return f"Files in directory: {', '.join(files)}"

        elif method == "read":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        elif method == "write":
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content or "")
            return f"SUCCESS: File written → {file_path}"

        else:
            return f"Unknown file action: {method}"
    except Exception as e:
        return f"File system error: {str(e)}"


# ===================== OPENROUTER CHAT FUNCTION =====================
def call_openrouter(messages):
    """Make API call to OpenRouter"""
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "response_format": {"type": "json_object"}  # Ensure JSON response
    }
    
    try:
        response = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=openrouter_headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ OpenRouter API Error {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
        return response.json()
    
    except Exception as e:
        print(f"OpenRouter call error: {e}")
        return None


# ===================== SYSTEM PROMPT =====================
SYSTEM_PROMPT = """
You are ClawMind — an autonomous AI with long-term memory, WhatsApp, and Facebook control.

Rules:
- Always search memory first for context
- When user shares info, use "remember" action
- For WhatsApp actions, ask permission first
- For Facebook actions, ask permission first

WhatsApp Actions:
- Send: {"action": "whatsapp", "action_type": "send", "contact": "Name", "message": "Text"}
- Call: {"action": "whatsapp", "action_type": "call", "contact": "Name", "call_type": "audio"}
- Check calls: {"action": "whatsapp", "action_type": "check_calls", "contact": "Name"}
- Last message: {"action": "whatsapp", "action_type": "last_message", "contact": "Name"}
- Recent messages: {"action": "whatsapp", "action_type": "recent_messages"}
- Open: {"action": "whatsapp", "action_type": "open"}

Facebook Actions:
- Open: {"action": "facebook", "action_type": "open"}
- Post status: {"action": "facebook", "action_type": "post_status", "message": "Hello world!"}
- Post photo: {"action": "facebook", "action_type": "post_photo", "image_path": "C:/path/photo.jpg", "caption": "My photo"}
- Check posts: {"action": "facebook", "action_type": "check_posts"}
- Get photos: {"action": "facebook", "action_type": "get_photos"}

Output ONLY valid JSON:
{"action": "search", "query": "..."}
{"action": "remember", "fact": "...", "tags": ["tag1"]}
{"action": "whatsapp", "action_type": "send", "contact": "John", "message": "Hello"}
{"action": "facebook", "action_type": "post_status", "message": "Hello!"}
{"action": "facebook", "action_type": "post_photo", "image_path": "photo.jpg", "caption": "Caption here"}
{"action": "reply", "message": "your response"}
"""



# ===================== MAIN AGENT =====================
def run_agent():
    print("\n🧠 ClawMind Agent Started — Using OpenRouter API")
    print(f"📡 Model: {MODEL}")
    print("💾 Long-term Memory + File Access Active\n")

    # Initial context
    current_files = manage_local_file("list", ".")
    db_context = search_membrain("user profile, hackathon, clawmind, ishan, preferences")

    chat_history = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"LOCAL FILES: {current_files}"},
        {"role": "system", "content": f"LONG-TERM MEMORY: {db_context}"}
    ]

    print("✅ Ready! Type 'bye' to exit.\n")
    # Add these variables at the beginning of run_agent() function
    pending_whatsapp_action = None
    pending_facebook_action = None
    permission_granted = False

    while True:
        user_input = input("👤 You: ").strip()
        if pending_whatsapp_action and user_input.lower() in ["yes", "proceed", "ok", "sure", "go ahead"]:
            print(f"\n✅ Permission granted. Executing WhatsApp action...")
            # Execute the pending action
            result = whatsapp_tool(
                pending_whatsapp_action.get("action_type"),
                pending_whatsapp_action.get("contact"),
                pending_whatsapp_action.get("message")
            )
            chat_history.append({"role": "system", "content": f"WHATSAPP RESULT: {result}"})
            print(f"\n🤖 ClawMind: {result}")
            pending_whatsapp_action = None
            continue
        elif pending_facebook_action and user_input.lower() in ["yes", "proceed", "ok", "sure", "go ahead"]:
            print(f"\n✅ Permission granted. Executing Facebook action...")
            result = facebook_tool(
                pending_facebook_action.get("action_type"),
                image_path=pending_facebook_action.get("image_path"),
                caption=pending_facebook_action.get("caption"),
                message=pending_facebook_action.get("message")
            )
            chat_history.append({"role": "system", "content": f"FACEBOOK RESULT: {result}"})
            print(f"\n🤖 ClawMind: {result}")
            pending_facebook_action = None
            continue
        elif (pending_whatsapp_action or pending_facebook_action) and user_input.lower() in ["no", "cancel", "stop"]:
            print("\n❌ Action cancelled.")
            pending_whatsapp_action = None
            pending_facebook_action = None
            continue
        # 👆👆👆 END OF PERMISSION CHECK SECTION 👆👆👆
        
        if user_input.lower() in ["bye", "exit", "quit"]:
            print("👋 Goodbye! All memories saved in Membrain.")
            break
        chat_history.append({"role": "user", "content": user_input})

        for _ in range(10):   # Safety limit on ReAct steps
            try:
                # Call OpenRouter instead of Groq
                response = call_openrouter(chat_history)
                
                if not response:
                    print("❌ Failed to get response from OpenRouter")
                    break
                
                ai_msg = response["choices"][0]["message"]["content"]
                chat_history.append({"role": "assistant", "content": ai_msg})

                data = json.loads(ai_msg)
                decision = data[0] if isinstance(data, list) else data
                action = decision.get("action")

                if action == "reply":
                    print(f"\n🤖 ClawMind: {decision.get('message')}")
                    break

                elif action == "search":
                    result = search_membrain(decision.get("query", user_input))
                    chat_history.append({"role": "system", "content": f"MEMORY RESULT:\n{result}"})

                elif action == "remember":
                    result = save_memory(decision.get("fact"), decision.get("tags", []))
                    chat_history.append({"role": "system", "content": f"SAVE STATUS: {result}"})

                elif action == "file_system":
                    result = manage_local_file(
                        decision.get("action_type"),
                        decision.get("path"),
                        decision.get("content")
                    )
                    chat_history.append({"role": "system", "content": f"FILE RESULT: {result}"})
                    
                # 👇👇👇 REPLACE YOUR WHATSAPP SECTION WITH THIS 👇👇👇
                elif action == "whatsapp":
                    # Ask for permission
                    action_type = decision.get("action_type")
                    contact = decision.get("contact")
                    
                    if action_type in ["send", "call"]:
                        pending_whatsapp_action = decision
                        print(f"\n🤖 ClawMind: I need permission to {action_type} WhatsApp message to {contact}. Proceed?")
                        break
                    else:
                        result = whatsapp_tool(action_type, contact, decision.get("message"))
                        chat_history.append({"role": "system", "content": f"WHATSAPP RESULT: {result}"})
                        print(f"\n🤖 ClawMind: {result}")
                
                # 👇👇👇 REPLACE YOUR FACEBOOK SECTION WITH THIS 👇👇👇
                elif action == "facebook":
                    # Ask for permission
                    action_type = decision.get("action_type")
                    
                    if action_type in ["post_status", "post_photo"]:
                        pending_facebook_action = decision
                        print(f"\n🤖 ClawMind: I need permission to {action_type} on Facebook. Proceed?")
                        break
                    else:
                        result = facebook_tool(
                            action_type,
                            image_path=decision.get("image_path"),
                            caption=decision.get("caption"),
                            message=decision.get("message")
                        )
                        chat_history.append({"role": "system", "content": f"FACEBOOK RESULT: {result}"})
                        print(f"\n🤖 ClawMind: {result}")
                # 👆👆👆 END OF REPLACED SECTIONS 👆👆👆

                else:
                    print(f"Unknown action: {action}")
                    break

            except json.JSONDecodeError:
                print("AI returned invalid JSON → forcing reply")
                print(f"\n🤖 ClawMind: {ai_msg}")
                break
            except Exception as e:
                print(f"Agent loop error: {e}")
                break

if __name__ == "__main__":
    run_agent()