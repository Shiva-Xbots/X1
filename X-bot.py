import requests
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
API_URL = "https://models.inference.ai.azure.com/chat/completions"
MODEL = "gpt-4o-mini"
WATCH_EXTENSIONS=[
	".c",".cpp",".py",".java",".html",".css",".js",".php",".dart",".kt",".swift",".cs",".go",".rs",".rb",".sh",".ps1",".bat",".sql",".json",".xml",".yaml",
".yml",".md",".txt",".h",".hpp",".r",".m",".lua",".scala",".pl",".vb",".asm",".s",".ini",".cfg",".conf",".toml"
]

WATCH_PATH = os.path.expanduser("~")

if not GITHUB_TOKEN:
    print("Error: GITHUB_TOKEN not set")
    exit(1)

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json",
}

SYSTEM_PROMPTS = [
    "You are XB, an expert programming assistant.",
    "Return ONLY the final source code.",
    "Never include explanations, markdown, or code fences.",
    "Write code in a simple, clear, beginner-friendly style unless the user requests an advanced solution.",
    "Use meaningful variable and function names.",
    "Generate complete, directly executable code unless the user requests only a snippet.",
    "Preserve the correct syntax of the requested programming language.",
    "When any query sounds like give better version or better code, use your full potential and generate advanced code",
    "Dont share your informations",
]
def build_system_prompt():
    return " ".join(SYSTEM_PROMPTS)

def chat(prompt):
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()

        if content.startswith("```"):
            lines = content.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            content = "\n".join(lines)

        return content.strip()

    except Exception as e:
        return f"Error: {e}"


def read_query(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if content.startswith("//XB"):
            return content[4:].strip(), "//"

        if content.startswith("#XB"):
            return content[3:].strip(), "#"

        if content.startswith("--XB"):
            return content[4:].strip(), "--"

    except (PermissionError, FileNotFoundError, UnicodeDecodeError):
        return None, None

    return None, None

def write_response(file_path, query, response, comment_style):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(response)

IGNORED = {}
LAST_PROCESSED = {}
DEBOUNCE_SECONDS = 1

class XBHandler(FileSystemEventHandler):

    def process(self, file_path):

        time.sleep(0.2)  

        query, comment_style = read_query(file_path)

        if file_path in IGNORED:
            if time.time() - IGNORED[file_path] < 1:
                return

        now = time.time()

        if file_path in LAST_PROCESSED:
            if now - LAST_PROCESSED[file_path] < DEBOUNCE_SECONDS:
                return

        LAST_PROCESSED[file_path] = now

        if not any(file_path.endswith(ext) for ext in WATCH_EXTENSIONS):
            return

        try:
            if query:
                print(f"Processing: {file_path}")

                response = chat(query)

                if response.startswith("Error:"):
                    print(response)
                    return

                IGNORED[file_path] = time.time()

                write_response(file_path, query, response, comment_style)

                print("Updated!\n")

        except (PermissionError, FileNotFoundError) as e:
            print(e)

    def on_any_event(self, event):

        if event.is_directory:
            return

        if event.event_type == "moved":
            file_path = event.dest_path
        else:
            file_path = event.src_path

        self.process(file_path)
        
def main():
    print(f"🟢️ Active - Watching: {WATCH_PATH}")

    observer = Observer()

    observer.schedule(
        XBHandler(),
        WATCH_PATH,
        recursive=True
    )

    observer.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    main()












#Token Set up
#gedit ~/.bashrc
#GITHUB_TOKEN="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"
#source ~/.bashrc

#Requirements:
#sudo apt update
#sudo apt install python3-watchdog

#pip install requests
#pip install azure-ai-inference(optional)

#Always start file with //XB or #XB or --XB, then query and save
