import os
import json
import random
import feedparser
import google.generativeai as genai
from datetime import datetime
import time

# 1. SETUP
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Safety settings remain as you had them
safety_settings = [
    { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE" },
    { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE" },
    { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE" },
    { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE" },
]

model = genai.GenerativeModel('gemini-1.5-flash', safety_settings=safety_settings)

FEEDS = {
    "AI": "https://news.google.com/rss/search?q=Artificial+Intelligence+when:24h",
    "Deep Tech": "https://news.google.com/rss/search?q=Deep+Tech+OR+Quantum+Computing+when:24h",
    "South East Asia": "https://news.google.com/rss/search?q=South+East+Asia+Tech+Startup+when:24h"
}

def get_ai_summary(title):
    prompt = f"Write a 2-sentence executive summary for this tech news headline. Focus on the innovation. Headline: {title}"
    try:
        response = model.generate_content(prompt)
        # Added a check for candidates to prevent 'response.text' errors
        if response.candidates and response.candidates[0].content.parts:
            return response.text.strip()
        return "Insightful tech update. View full article for details."
    except Exception as e:
        print(f"Gemini Error for '{title}': {e}")
        return "Summary being refined. Full details available at source."

# 3. PERMANENT ARCHIVE LOGIC
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        full_database = json.load(f)
else:
    full_database = []

new_entries_count = 0
for category, url in FEEDS.items():
    feed = feedparser.parse(url)
    for entry in feed.entries[:3]:
        # Check if already in database
        if not any(item['link'] == entry.link for item in full_database):
            print(f"Summarizing: {entry.title}")
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
            new_entries_count += 1
            time.sleep(1) # Short pause to prevent API rate limiting

# SAVE EVERYTHING (No more [:50] limit)
with open("data.json", "w") as f:
    json.dump(full_database, f)

# 4. HTML GENERATION FUNCTION
def generate_html(news_items, filename, page_title):
    # We define the categories for the tabs
    categories = ["All", "AI", "Deep Tech", "South East Asia"]
    
    html_start = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{page_title} | UnicrisAI</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: white; color: black; }}
            .banner-img {{ filter: grayscale(100%); height: 140px; width: 100%; object-fit: cover; border-radius: 2px; transition: 0.4s; }}
            .banner-img:hover {{ filter: grayscale(0%); }}
            .news-card {{ border-bottom: 1px solid #f3f4f6; padding: 3rem 0; }}
            .nav-link {{ font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase; font-weight: bold; margin-right: 20px; }}
            .active-page {{ border-bottom: 2px solid black; padding-bottom: 4px; }}
            .tab-btn {{ font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; padding: 6px 12px; border: 1px solid #eee; transition: 0.2s; }}
            .tab-btn:hover {{ background: #f9f9f9; }}
            .active-tab {{ background: black !important; color: white; border-color: black; }}
        </style>
    </head>
    <body class="font-sans antialiased">
        <header class="max-w-2xl mx-auto pt-16 px-6">
            <h1 class="text-4xl font-black tracking-tighter uppercase">UnicrisAI</h1>
            
            <nav class="mt-6 flex">
                <a href="index.html" class="nav-link {'active-page' if filename=='index.html' else ''}">Latest</a>
                <a href="archive.html" class="nav-link {'active-page' if filename=='archive.html' else ''}">Archive</a>
            </nav>

            <div class="flex justify-between items-center mt-8 text-[10px] tracking-[0.4em] text-gray-400 uppercase">
                <div>{page_title}</div>
                <div>{datetime.now().strftime('%Y-%m-%d')}</div>
            </div>

            <div class="mt-12 border-b border-gray-100 pb-2">
                <input type="text" id="searchInput" placeholder="SEARCH..." class="w-full text-xs tracking-widest uppercase bg-transparent outline-none">
            </div>

            <div id="tabContainer" class="mt-6 flex flex-wrap gap-2">
                {" ".join([f"<button class='tab-btn {'active-tab' if cat=='All' else ''}' onclick='filterCategory(\"{cat}\")'>{cat}</button>" for cat in categories])}
            </div>
        </header>

        <main id="newsContainer" class="max-w-2xl mx-auto px-6 py-8">
    """
    
    cards_html = ""
    for item in news_items:
        # We include the category in a data-attribute for the JS filter
        cards_html += f"""
        <div class="news-card" data-title="{item['title'].lower()}" data-category="{item['category']}">
            <img src="{item['image']}" class="banner-img mb-6">
            <div class="text-[9px] font-bold tracking-[0.2em] text-gray-400 uppercase mb-2">{item['category']} | {item['date']}</div>
            <h3 class="text-2xl font-bold leading-tight mb-4">
                <a href="{item['link']}" target="_blank" class="hover:text-gray-400 transition-colors">{item['title']}</a>
            </h3>
            <p class="text-gray-600 leading-relaxed mb-6">{item['summary']}</p>
            <a href="{item['link']}" target="_blank" class="text-[10px] font-black border-b-2 border-black pb-1 tracking-widest uppercase">Read More →</a>
        </div>
        """

    html_end = """
        </main>
        <footer class="max-w-2xl mx-auto px-6 py-24 text-center text-[9px] text-gray-300 uppercase tracking-[0.5em]">
            &copy; 2026 UNICRISAI • AUTOMATED NEWS ENGINE
        </footer>

        <script>
            let currentCategory = 'All';
            let currentSearch = '';

            function updateDisplay() {
                const cards = document.querySelectorAll('.news-card');
                cards.forEach(card => {
                    const title = card.getAttribute('data-title');
                    const category = card.getAttribute('data-category');
                    
                    const matchesSearch = title.includes(currentSearch);
                    const matchesCategory = currentCategory === 'All' || category === currentCategory;
                    
                    card.style.display = (matchesSearch && matchesCategory) ? 'block' : 'none';
                });
            }

            function filterCategory(cat) {
                currentCategory = cat;
                // Update button UI
                document.querySelectorAll('.tab-btn').forEach(btn => {
                    btn.classList.toggle('active-tab', btn.innerText.toUpperCase() === cat.toUpperCase());
                });
                updateDisplay();
            }

            document.getElementById('searchInput').addEventListener('input', (e) => {
                currentSearch = e.target.value.toLowerCase();
                updateDisplay();
            });
        </script>
    </body>
    </html>
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_start + cards_html + html_end)

# 5. GENERATE THE TWO PAGES
# Latest page: top 10 items
generate_html(full_database[:10], "index.html", "Latest Updates")
# Archive page: everything
generate_html(full_database, "archive.html", "Full Archive")
