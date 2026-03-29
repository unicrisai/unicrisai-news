import os
import json
import random
import feedparser
import google.generativeai as genai
from datetime import datetime
import time

# 1. SETUP GEMINI
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

safety_settings = [
    { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE" },
    { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE" },
    { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE" },
    { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE" },
]

model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safety_settings)

# 2. NEWS SOURCES
FEEDS = {
    "AI": "https://news.google.com/rss/search?q=Artificial+Intelligence+when:24h",
    "Deep Tech": "https://news.google.com/rss/search?q=Deep+Tech+OR+Quantum+Computing+when:24h",
    "South East Asia": "https://news.google.com/rss/search?q=South+East+Asia+Tech+Startup+when:24h"
}

def get_ai_summary(title):
    # DEBUG: Print what we are sending
    print(f"--- Requesting Summary for: {title[:50]}... ---")
    prompt = f"Write a 2-sentence executive summary for this tech news headline. Focus on the innovation. Headline: {title}"
    try:
        response = model.generate_content(prompt)
        if response.candidates and response.candidates[0].content.parts:
            text = response.text.strip()
            print(f"SUCCESS: {text[:50]}...")
            return text
        print("BLOCKED: Gemini returned an empty candidate (Safety filter?)")
        return "Insightful tech update. View full article for details."
    except Exception as e:
        print(f"ERROR: {e}")
        return "Summary being refined. Full details available at source."

# 3. DATA PERSISTENCE
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        full_database = json.load(f)
else:
    full_database = []

for category, url in FEEDS.items():
    feed = feedparser.parse(url)
    for entry in feed.entries[:3]:
        if not any(item['link'] == entry.link for item in full_database):
            summary = get_ai_summary(entry.title)
            
            r = random.randint(1, 1000)
            img_map = {
                "AI": f"https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&q=80&sig={r}",
                "Deep Tech": f"https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80&sig={r}",
                "South East Asia": f"https://images.unsplash.com/photo-1528154291023-a6525fabe5b4?w=800&q=80&sig={r}"
            }

            full_database.insert(0, {
                "title": entry.title,
                "link": entry.link,
                "summary": summary,
                "category": category,
                "image": img_map.get(category),
                "date": datetime.now().strftime('%Y-%m-%d')
            })
            time.sleep(2) # Increased sleep to be safe

with open("data.json", "w") as f:
    json.dump(full_database, f)

# 4. UI GENERATION
def generate_html(news_items, filename, page_title):
    categories = ["All", "AI", "Deep Tech", "South East Asia"]
    
    # We use a very explicit style for the buttons to make sure they show up
    button_html = ""
    for cat in categories:
        active_class = "bg-black text-white" if cat == "All" else "bg-gray-100 text-black"
        button_html += f'<button class="tab-btn px-4 py-2 text-[10px] uppercase font-bold mr-2 mb-2 {active_class}" onclick="filterCategory(\'{cat}\')">{cat}</button>'

    html_start = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{page_title} | UnicrisAI</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: white; color: black; }}
            .active-page {{ border-bottom: 2px solid black; padding-bottom: 4px; }}
            .active-tab {{ background: black !important; color: white !important; }}
        </style>
    </head>
    <body class="font-sans antialiased">
        <header class="max-w-2xl mx-auto pt-16 px-6">
            <h1 class="text-4xl font-black tracking-tighter uppercase">UnicrisAI</h1>
            
            <nav class="mt-8 flex gap-6">
                <a href="index.html" class="text-[10px] uppercase font-bold tracking-widest {'active-page' if filename=='index.html' else ''}">Latest Updates</a>
                <a href="archive.html" class="text-[10px] uppercase font-bold tracking-widest {'active-page' if filename=='archive.html' else ''}">Full Archive</a>
            </nav>

            <div class="mt-12 border-b border-gray-100 pb-2">
                <input type="text" id="searchInput" placeholder="SEARCH..." class="w-full text-xs tracking-widest uppercase bg-transparent outline-none">
            </div>

            <div id="tabContainer" class="mt-8 flex flex-wrap">
                {button_html}
            </div>
        </header>

        <main id="newsContainer" class="max-w-2xl mx-auto px-6 py-8">
    """
    
    cards_html = ""
    for item in news_items:
        cards_html += f"""
        <div class="news-card border-b border-gray-100 py-12" data-title="{item['title'].lower()}" data-category="{item['category']}">
            <img src="{item['image']}" class="w-full h-40 object-cover mb-6 grayscale hover:grayscale-0 transition-all">
            <div class="text-[9px] font-bold tracking-widest text-gray-400 uppercase mb-2">{item['category']} | {item['date']}</div>
            <h3 class="text-2xl font-bold leading-tight mb-4">
                <a href="{item['link']}" target="_blank" class="hover:underline">{item['title']}</a>
            </h3>
            <p class="text-gray-600 leading-relaxed mb-6">{item['summary']}</p>
        </div>
        """

    html_end = """
        </main>
        <script>
            function filterCategory(cat) {
                document.querySelectorAll('.tab-btn').forEach(btn => {
                    btn.classList.toggle('active-tab', btn.innerText === cat);
                });
                const cards = document.querySelectorAll('.news-card');
                const term = document.getElementById('searchInput').value.toLowerCase();
                cards.forEach(card => {
                    const matchesCat = (cat === 'All' || card.dataset.category === cat);
                    const matchesSearch = card.dataset.title.includes(term);
                    card.style.display = (matchesCat && matchesSearch) ? 'block' : 'none';
                });
            }
            document.getElementById('searchInput').addEventListener('input', () => filterCategory(document.querySelector('.active-tab').innerText));
        </script>
    </body>
    </html>
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_start + cards_html + html_end)

generate_html(full_database[:10], "index.html", "Latest Updates")
generate_html(full_database, "archive.html", "Full Archive")
