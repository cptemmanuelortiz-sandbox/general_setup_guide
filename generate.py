import json
import os
import shutil
import sys
import re

CONFIG_FILE = "config.json"
STATIC_SRC = "static"
OUTPUT_DIR = "output"

def log_error_and_exit(msg):
    print(f"❌ {msg}")
    sys.exit(1)

# ---------- Helper to convert video links to embed URLs ----------
def get_embed_url(url):
    # Google Drive
    drive_match = re.search(r'/file/d/([^/]+)', url)
    if drive_match:
        return f'https://drive.google.com/file/d/{drive_match.group(1)}/preview'
    
    # YouTube
    yt_match = re.search(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([^&?]+)', url)
    if yt_match:
        return f'https://www.youtube.com/embed/{yt_match.group(1)}'
        
    return url  # Fallback

# ---------- Helper to get localized text ----------
def get_localized_text(data, lang='en'):
    """Extract text from a field that might be a string or a language object"""
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        return data.get(lang, data.get('en', str(data)))
    return str(data)

# ---------- Load config ----------
if not os.path.exists(CONFIG_FILE):
    log_error_and_exit(f"{CONFIG_FILE} not found!")

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
except json.JSONDecodeError as e:
    log_error_and_exit(f"Invalid JSON in {CONFIG_FILE}: {e}")

# ---------- Prepare output directory ----------
shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------- Copy static files securely ----------
if os.path.exists(STATIC_SRC):
    dest_static = os.path.join(OUTPUT_DIR, "static")
    os.makedirs(dest_static, exist_ok=True)
    for root, dirs, files in os.walk(STATIC_SRC):
        rel_path = os.path.relpath(root, STATIC_SRC)
        dest_dir = os.path.join(dest_static, rel_path) if rel_path != "." else dest_static
        os.makedirs(dest_dir, exist_ok=True)
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_dir, file)
            shutil.copy2(src_file, dest_file)
    print("✅ Static files copied successfully.")
else:
    print("⚠️  Warning: 'static/' folder not found – no media will be copied.")

# ---------- HTML Templates ----------
# Smart Cookies: Clears ONLY on the index/choice page (first access)
CHOICE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <script>
        document.cookie.split(";").forEach(function(c) {{ 
            document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
        }});
        localStorage.removeItem('preferredLanguage');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{site_title_en} - Choose Path</title>
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }}
        .choice-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 2rem 0; }}
        .choice-card {{ display: block; padding: 2rem 1rem; background: #f8f9fa; border: 2px solid #dee2e6; border-radius: 12px; text-decoration: none; color: #333; text-align: center; transition: all 0.3s ease; }}
        .choice-card:hover {{ background: #007bff; color: white; border-color: #007bff; transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }}
        .choice-title {{ font-size: 1.3rem; font-weight: bold; margin-bottom: 0.5rem; }}
        .choice-desc {{ font-size: 0.9rem; opacity: 0.8; }}
        .lang-toggle {{ position: fixed; bottom: 20px; right: 20px; background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; z-index: 1000; }}
        .lang-toggle:hover {{ background: #218838; }}
        .lang-en, .lang-es {{ display: none; }}
        .lang-en.active, .lang-es.active {{ display: block; }}
        h1, .subtitle {{ text-align: center; }}
        .subtitle {{ color: #666; margin-bottom: 2rem; }}
    </style>
</head>
<body>
    <button class="lang-toggle" onclick="toggleLanguage()">Español</button>
    <h1>
        <span class="lang-en active">{site_title_en}</span>
        <span class="lang-es">{site_title_es}</span>
    </h1>
    <p class="subtitle">
        <span class="lang-en active">Choose how you want to proceed:</span>
        <span class="lang-es">Elija cómo desea proceder:</span>
    </p>
    <div class="choice-grid">
        {choices_html}
    </div>
    <script>
        let currentLang = 'en';
        function toggleLanguage() {{
            const toggleBtn = document.querySelector('.lang-toggle');
            currentLang = currentLang === 'en' ? 'es' : 'en';
            toggleBtn.textContent = currentLang === 'en' ? 'Español' : 'English';
            updateLanguage(currentLang);
        }}
        function updateLanguage(lang) {{
            document.querySelectorAll('.lang-en, .lang-es').forEach(el => {{
                el.classList.remove('active');
                if (el.classList.contains(`lang-${{lang}}`)) el.classList.add('active');
            }});
            localStorage.setItem('preferredLanguage', lang);
        }}
        document.addEventListener('DOMContentLoaded', function() {{
            const savedLang = localStorage.getItem('preferredLanguage') || 'en';
            currentLang = savedLang;
            if (savedLang === 'es') document.querySelector('.lang-toggle').textContent = 'English';
            updateLanguage(savedLang);
        }});
    </script>
</body>
</html>
"""

# Smart Cookies: REMOVED. Language is preserved here.
STEP_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Step {step_num} of {total_steps} – {process_title_en}</title>
    <style>
        body {{ font-family: sans-serif; max-width: 600px; margin: 2rem auto; padding: 0 1rem; }}
        .button {{ display: inline-block; padding: 1rem 2rem; margin: 1rem 0; background: #007bff; color: white; text-decoration: none; border-radius: 8px; }}
        img, video, iframe {{ max-width: 100%; height: auto; margin: 1rem 0; border-radius: 8px; }}
        iframe {{ width: 100%; height: 340px; border: none; }}
        .nav {{ margin-top: 2rem; display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }}
        .lang-toggle {{ position: fixed; bottom: 20px; right: 20px; background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; z-index: 1000; }}
        .lang-toggle:hover {{ background: #218838; }}
        .lang-en, .lang-es, .instruction-en, .instruction-es, .step-counter-en, .step-counter-es {{ display: none; }}
        .lang-en.active, .lang-es.active, .instruction-en.active, .instruction-es.active, .step-counter-en.active, .step-counter-es.active {{ display: block; }}
        .step-counter-en.active, .step-counter-es.active {{ display: inline; }}
    </style>
</head>
<body>
    <button class="lang-toggle" onclick="toggleLanguage()">Español</button>
    <h1>
        <span class="lang-en active">{process_title_en}</span>
        <span class="lang-es">{process_title_es}</span>
    </h1>
    <p><strong>
        <span class="lang-en active step-counter-en">Step {step_num} of {total_steps}</span>
        <span class="lang-es step-counter-es">Paso {step_num} de {total_steps}</span>
    </strong></p>
    <div class="instruction-en active">{instruction_en}</div>
    <div class="instruction-es">{instruction_es}</div>
    {media}
    <div class="nav">
        {prev_link}
        {next_link}
        <a href="index.html" class="button">🏠 Home</a>
    </div>
    <script>
        let currentLang = 'en';
        function toggleLanguage() {{
            const toggleBtn = document.querySelector('.lang-toggle');
            currentLang = currentLang === 'en' ? 'es' : 'en';
            toggleBtn.textContent = currentLang === 'en' ? 'Español' : 'English';
            updateLanguage(currentLang);
        }}
        function updateLanguage(lang) {{
            document.querySelectorAll('.lang-en, .lang-es, .instruction-en, .instruction-es, .step-counter-en, .step-counter-es').forEach(el => {{
                el.classList.remove('active');
                if (el.classList.contains(`lang-${{lang}}`) || el.classList.contains(`instruction-${{lang}}`) || el.classList.contains(`step-counter-${{lang}}`)) el.classList.add('active');
            }});
            localStorage.setItem('preferredLanguage', lang);
        }}
        document.addEventListener('DOMContentLoaded', function() {{
            const savedLang = localStorage.getItem('preferredLanguage') || 'en';
            currentLang = savedLang;
            if (savedLang === 'es') document.querySelector('.lang-toggle').textContent = 'English';
            updateLanguage(savedLang);
        }});
    </script>
</body>
</html>
"""

# ---------- Generator Logic ----------
def get_media_html(step, lang='en'):
    if "video_url" in step:
        embed_url = get_embed_url(step["video_url"])
        alt_text = get_localized_text(step.get("alt"), lang)
        return f'<iframe src="{embed_url}" allow="autoplay; encrypted-media" allowfullscreen title="{alt_text}"></iframe>'
    
    if "video" in step:
        alt_text = get_localized_text(step.get("alt"), lang)
        return f'<video controls alt="{alt_text}"><source src="static/videos/{step["video"]}" type="video/mp4">Your browser does not support the video tag.</video>'
    
    if "images" in step:
        images_html = '<div class="image-grid">'
        for img in step["images"]:
            alt_text = get_localized_text(img.get("alt"), lang)
            images_html += f'<img src="static/images/{img["src"]}" alt="{alt_text}">'
        images_html += '</div>'
        return images_html
    
    if "image" in step:
        alt_text = get_localized_text(step.get("alt"), lang)
        return f'<img src="static/images/{step["image"]}" alt="{alt_text}">'
    
    return ""

def build_site():
    site_title_en = get_localized_text(config.get("site_title", "Process Guide"), 'en')
    site_title_es = get_localized_text(config.get("site_title", "Guía de Proceso"), 'es')
    
    # Support both "processes" (new universal) and "options" (old room format) for backwards compatibility
    processes = config.get("processes", config.get("options", []))
    
    if not processes:
        log_error_and_exit("No processes/options found in config.json!")

    # 1. Build Index / Choice Page
    if len(processes) == 1:
        # If there's only one process, we still create an index page but link directly to step 1
        proc = processes[0]
        title_en = get_localized_text(proc["title"], 'en')
        title_es = get_localized_text(proc["title"], 'es')
        
        choices_html = f'''
        <a href="{proc['id']}_step1.html" class="choice-card">
            <div class="choice-title">
                <span class="lang-en active">{title_en}</span>
                <span class="lang-es">{title_es}</span>
            </div>
        </a>
        '''
        with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
            f.write(CHOICE_TEMPLATE.format(site_title_en=site_title_en, site_title_es=site_title_es, choices_html=choices_html))
            
    else:
        # Build the multi-choice page
        choices_html = ""
        for proc in processes:
            title_en = get_localized_text(proc["title"], 'en')
            title_es = get_localized_text(proc["title"], 'es')
            desc_en = get_localized_text(proc.get("description", ""), 'en')
            desc_es = get_localized_text(proc.get("description", ""), 'es')
            link = f"{proc['id']}_step1.html"
            
            choices_html += f'''
            <a href="{link}" class="choice-card">
                <div class="choice-title">
                    <span class="lang-en active">{title_en}</span>
                    <span class="lang-es">{title_es}</span>
                </div>
                <div class="choice-desc">
                    <span class="lang-en active">{desc_en}</span>
                    <span class="lang-es">{desc_es}</span>
                </div>
            </a>
            '''
            
        with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
            f.write(CHOICE_TEMPLATE.format(site_title_en=site_title_en, site_title_es=site_title_es, choices_html=choices_html))

    # 2. Build Step Pages for all processes
    for proc in processes:
        proc_id = proc["id"]
        steps = proc.get("steps", [])
        
        # Handle both the multi-path dictionary structure and single-path list structure
        if isinstance(steps, dict):
            # Multi-path (e.g., main_computer, laptop_hdmi)
            for path_id, path_steps in steps.items():
                path_title = {"en": path_id.replace('_', ' ').title(), "es": path_id.replace('_', ' ').title()}
                for p in proc.get("choices", []):
                    if p["id"] == path_id:
                        path_title = p["title"]
                        break
                generate_steps(proc_id, path_id, path_title, path_steps)
        else:
            # Single path (linear process)
            generate_steps(proc_id, "", proc["title"], steps)

def generate_steps(proc_id, path_id, title_obj, steps):
    total = len(steps)
    if total == 0:
        return
        
    title_en = get_localized_text(title_obj, 'en')
    title_es = get_localized_text(title_obj, 'es')
    
    # Create the prefix for filenames (e.g., "start_main_computer" or just "start")
    prefix = f"{proc_id}_{path_id}" if path_id else proc_id

    for i, step in enumerate(steps, start=1):
        instr_en = get_localized_text(step.get("instruction"), 'en')
        instr_es = get_localized_text(step.get("instruction"), 'es')
        media = get_media_html(step, 'en')
        
        prev_link = f'<a href="{prefix}_step{i-1}.html" class="button"><span class="lang-en active">⬅ Previous</span><span class="lang-es">⬅ Anterior</span></a>' if i > 1 else '<span></span>'
        next_link = f'<a href="{prefix}_step{i+1}.html" class="button"><span class="lang-en active">Next ➔</span><span class="lang-es">Siguiente ➔</span></a>' if i < total else f'<a href="index.html" class="button"><span class="lang-en active">Finish 🎉</span><span class="lang-es">Finalizar 🎉</span></a>'

        page = STEP_TEMPLATE.format(
            process_title_en=title_en, process_title_es=title_es,
            step_num=i, total_steps=total,
            instruction_en=instr_en, instruction_es=instr_es,
            media=media, prev_link=prev_link, next_link=next_link
        )
        
        with open(os.path.join(OUTPUT_DIR, f"{prefix}_step{i}.html"), "w") as f:
            f.write(page)

if __name__ == "__main__":
    print("🚀 Generating site...")
    build_site()
    print("✅ Site generated successfully!")
