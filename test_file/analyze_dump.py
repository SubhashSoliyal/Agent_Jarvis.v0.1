
from bs4 import BeautifulSoup
import os

path = r"c:\AnithingLLM\Jarvis.v3.0\Jarvis.v3.0\backend\Data\Stories\debug_dump.html"

with open(path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
buttons = soup.find_all("button")

# Also check for elements with role="button"
role_buttons = soup.find_all(attrs={"role": "button"})

textareas = soup.find_all("textarea")
buttons = soup.find_all("button")
role_buttons = soup.find_all(attrs={"role": "button"})

with open("analysis_result.txt", "w", encoding="utf-8") as f:
    f.write("--- TEXTAREAS ---\n")
    for i, ta in enumerate(textareas):
        line = f"TEXTAREA {i}: Class='{ta.attrs.get('class')}' Placeholder='{ta.attrs.get('placeholder')}' Aria='{ta.attrs.get('aria-label')}' ValLength={len(ta.get_text(strip=True))}\n"
        f.write(line)
    
    f.write("\n--- BUTTONS (Relevant) ---\n")
    keywords = ["run", "download", "export", "stop", "generate", "audio", "speech", "close", "cancel"]
    for btn in buttons + role_buttons:
        text = btn.get_text(strip=True)
        attrs = btn.attrs
        s_text = text.lower()
        s_attrs = str(attrs).lower()
        if any(k in s_text or k in s_attrs for k in keywords):
            line = f"MATCH: <{btn.name}> Text='{text}' Class='{attrs.get('class')}' Aria='{attrs.get('aria-label')}'\n"
            f.write(line)

    f.write("\n--- POTENTIAL ERRORS ---\n")
    for tag in soup.find_all(string=lambda t: "error" in t.lower() or "wrong" in t.lower()):
        parent = tag.parent
        line = f"ERROR MATCH: <{parent.name}> Text='{tag.strip()}'\n"
        f.write(line)



