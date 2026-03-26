import os
import json
import random
import feedparser
import google.generativeai as genai
from datetime import datetime

# 1. SETUP GEMINI WITH SAFETY BYPASS
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# We disable blocks to ensure tech news summaries aren't censored
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

# 2. NEWS SOURCES
FEEDS = {
    "AI": "https://news.google.com/rss/search?q=Artificial+Intelligence+when:24h",
    "Deep Tech": "https://news.google.com/rss/search?q=Deep+Tech+OR+Quantum+Computing+when:24h",
    "South East Asia": "https://news.google.com/rss/search?q=South+East+Asia+Tech+Startup+when:24h"
}

def get_ai_summary(title):
    prompt = f"Write a 2-sentence executive summary for this tech news headline. Focus on the innovation. Headline: {title}"
    try:
        response = model.generate_content(prompt)
        if response.text:
            return response.text.strip()
        return "Insightful tech update. View full article for details."
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Summary being refined. Full details available at source."

# 3. ARCHIVE LOGIC (JSON DATABASE)
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        archive = json.load(f)
else:
    archive = []

# Fetch and Add New Stories
for category, url in FEEDS.items():
    feed = feedparser.parse(url)
    for entry in feed.entries[:3]:
        if not any(item['link'] == entry.link for item in archive):
            summary = get_ai_summary(entry.title)
            
            # Variety for Banners using different high-quality tech photos
            # We add a random 'sig' number to the URL to force Unsplash to give a different photo
            r = random.randint(1, 1000)
            img_map = {
                "AI": f"https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&q=80&sig={r}",
                "Deep Tech": f"https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80&sig={r}",
                "South East Asia": f"https://images.unsplash.com/photo-1528154291023-a6525fabe5b4?w=800&q=80&sig={r}"
            }

            archive.insert(0, {
                "title": entry.title,
                "link": entry.link,
                "summary": summary,
                "category": category,
                "image": img_map.get(category),
                "date": datetime.now().strftime('%Y-%m-%d')
            })

# Keep last 50 entries
archive = archive[:50]

with open("data.json", "w") as f:
    json.dump(archive, f)

# 4. HTML GENERATION (The UI)
html_start = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UnicrisAI News</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background: white; color: black; }}
        .banner-img {{ filter: grayscale(100%); height: 140px; width: 100%; object-fit: cover; border-radius: 2px; transition: 0.4s; }}
        .banner-img:hover {{ filter: grayscale(0%); }}
        .news-card {{ border-bottom: 1px solid #f3f4f6; padding: 3rem 0; }}
        input:focus {{ outline: none; border-bottom: 2px solid black; }}
    </style>
</head>
<body class="font-sans antialiased">
    <header class="max-w-2xl mx-auto pt-16 px-6">
        <h1 class="text-4xl font-black tracking-tighter uppercase">UnicrisAI</h1>
        <div class="flex justify-between items-center mt-4 text-[10px] tracking-[0.4em] text-gray-400 uppercase">
            <div>DEEP TECH • AI • SEA</div>
            <div>{datetime.now().strftime('%Y-%m-%d')}</div>
        </div>
        <div class="mt-12 border-b border-gray-100 pb-2">
            <input type="text" id="searchInput" placeholder="SEARCH ARCHIVE..." class="w-full text-xs tracking-widest uppercase bg-transparent">
        </div>
    </header>

    <main id="newsContainer" class="max-w-2xl mx-auto px-6 py-8">
"""

cards_html = ""
for item in archive:
    cards_html += f"""
    <div class="news-card" data-title="{item['title'].lower()}">
        <img src="{item['image']}" class="banner-img mb-6">
        <div class="text-[9px] font-bold tracking-[0.2em] text-gray-400 uppercase mb-2">{item['category']}</div>
        <h3 class="text-2xl font-bold leading-tight mb-4">
            <a href="{item['link']}" target="_blank" class="hover:text-gray-400 transition-colors">{item['title']}</a>
        </h3>
        <p class="text-gray-600 leading-relaxed mb-6">{item['summary']}</p>
        <a href="{item['link']}" target="_blank" class="text-[10px] font-black border-b-2 border-black pb-1 tracking-widest uppercase hover:text-gray-400 hover:border-gray-400 transition-all">Read Full Article →</a>
    </div>
    """

html_end = """
    </main>
    <footer class="max-w-2xl mx-auto px-6 py-24 text-center text-[9px] text-gray-300 uppercase tracking-[0.5em]">
        &copy; 2026 UNICRISAI • AUTOMATED NEWS ENGINE
    </footer>
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
