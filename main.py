import os
import json
import feedparser
import google.generativeai as genai
from datetime import datetime

# 1. Setup Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

FEEDS = {
    "AI": "https://news.google.com/rss/search?q=Artificial+Intelligence+when:24h",
    "Deep Tech": "https://news.google.com/rss/search?q=Deep+Tech+OR+Quantum+Computing+when:24h",
    "South East Asia": "https://news.google.com/rss/search?q=South+East+Asia+Tech+Startup+when:24h"
}

def get_ai_summary(title):
    prompt = f"Summarize this news in 2 short sentences for a tech innovator. Headline: {title}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "Insightful summary coming shortly."

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
            
            # Match banners
            img = "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&q=80" # AI
            if category == "Deep Tech": img = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80"
            if category == "South East Asia": img = "https://images.unsplash.com/photo-1528154291023-a6525fabe5b4?w=800&q=80"

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
