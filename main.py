import os
import json
import feedparser
import google.generativeai as genai
from datetime import datetime

# 1. Setup Gemini with safety bypass
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# We tell Gemini to be less restrictive for our news summaries
safety_settings = [
    { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE" },
    { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE" },
    { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE" },
    { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE" },
]

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    safety_settings=safety_settings
)

# ... (Keep the rest of your FEEDS and Archive logic)

def get_ai_summary(title):
    # We give Gemini a very specific "persona" to help it focus
    prompt = f"""
    You are a high-level tech curator. 
    Summarize this headline into 2 professional sentences for an innovation newsletter.
    Headline: {title}
    """
    try:
        response = model.generate_content(prompt)
        # Check if the response actually has text
        if response.text:
            return response.text.strip()
        else:
            return "Breaking news in development. Full details at the source link."
    except Exception as e:
        # This will help us see if there's a specific error in the logs
        print(f"API Error for '{title}': {e}")
        return "Summary being refined. View full article for immediate details."

# --- ARCHIVE LOGIC ---
# Load existing news or start fresh
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        archive = json.load(f)
else:
    archive = []

# Fetch new stories
new_stories = []
for category, url in FEEDS.items():
    feed = feedparser.parse(url)
    for entry in feed.entries[:3]:
        # Check if we already have this story (by link)
        if not any(item['link'] == entry.link for item in archive):
            summary = get_ai_summary(entry.title)
            
            # This creates more variety by adding a random number to the search
        import random
        r = random.randint(1, 100)
        
        if category == "AI": 
            image_url = f"https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&q=80&sig={r}"
        elif category == "Deep Tech": 
            image_url = f"https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80&sig={r}"
        else: # South East Asia
            image_url = f"https://images.unsplash.com/photo-1528154291023-a6525fabe5b4?w=800&q=80&sig={r}"

            archive.insert(0, {
                "title": entry.title,
                "link": entry.link,
                "summary": summary,
                "category": category,
                "image": img,
                "date": datetime.now().strftime('%Y-%m-%d')
            })

# Keep only the last 50 stories to keep it fast
archive = archive[:50]

# Save updated archive
with open("data.json", "w") as f:
    json.dump(archive, f)

# --- HTML GENERATION ---
html_start = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UnicrisAI News</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: white; color: black; }}
        .banner-img {{ filter: grayscale(100%); height: 120px; width: 100%; object-fit: cover; border-radius: 2px; }}
        .news-card {{ border-bottom: 1px solid #f3f4f6; padding: 2.5rem 0; }}
        input:focus {{ outline: none; border-bottom: 2px solid black; }}
    </style>
</head>
<body class="font-sans antialiased">
    <header class="max-w-2xl mx-auto pt-16 px-6">
        <h1 class="text-4xl font-black tracking-tighter uppercase">UnicrisAI</h1>
        <div class="flex justify-between items-center mt-4 text-[10px] tracking-[0.3em] text-gray-400 uppercase">
            <div>DEEP TECH • AI • SEA</div>
            <div>{datetime.now().strftime('%Y-%m-%d')}</div>
        </div>
        <div class="mt-12 border-b border-gray-100 pb-2">
            <input type="text" id="searchInput" placeholder="SEARCH ARCHIVE..." class="w-full text-xs tracking-widest uppercase bg-transparent">
        </div>
    </header>

    <main id="newsContainer" class="max-w-2xl mx-auto px-6 py-8">
"""

# Generate cards from archive
cards_html = ""
for item in archive:
    cards_html += f"""
    <div class="news-card" data-title="{item['title'].lower()}">
        <img src="{item['image']}" class="banner-img mb-4">
        <div class="text-[9px] font-bold tracking-widest text-gray-400 uppercase mb-2">{item['category']}</div>
        <h3 class="text-xl font-bold leading-tight mb-3">
            <a href="{item['link']}" target="_blank" class="hover:text-gray-400 transition-colors">{item['title']}</a>
        </h3>
        <p class="text-gray-500 text-sm leading-relaxed mb-4">{item['summary']}</p>
        <a href="{item['link']}" target="_blank" class="text-[9px] font-black border-b border-black pb-0.5 tracking-widest uppercase">Read More →</a>
    </div>
    """

html_end = """
    </main>
    <script>
        document.getElementById('searchInput').addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            document.querySelectorAll('.news-card').forEach(card => {
                const title = card.getAttribute('data-title');
                card.style.display = title.includes(term) ? 'block' : 'none';
            });
        });
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_start + cards_html + html_end)
