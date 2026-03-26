import os
import feedparser
import google.generativeai as genai
from datetime import datetime

# 1. Setup Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Define News Sources
# We use Google News RSS to target specific categories accurately
FEEDS = {
    "AI": "https://news.google.com/rss/search?q=Artificial+Intelligence+when:24h",
    "Deep Tech": "https://news.google.com/rss/search?q=Deep+Tech+OR+Quantum+Computing+when:24h",
    "South East Asia": "https://news.google.com/rss/search?q=South+East+Asia+Tech+Startup+when:24h"
}

def get_ai_summary(title, description):
    prompt = f"Summarize this news in 2 concise sentences for a professional tech innovator. Focus on the 'why it matters'.\nTitle: {title}\nContext: {description}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "Summary currently unavailable."

# 3. HTML Template (Your Minimalist Design)
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UnicrisAI News</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background-color: white; color: black; }}
        img {{ filter: grayscale(100%); }}
        .news-card {{ border-bottom: 1px solid #f3f4f6; padding: 2rem 0; }}
    </style>
</head>
<body class="font-sans antialiased">
    <header class="max-w-4xl mx-auto pt-12 px-6 flex justify-between items-baseline border-b border-gray-100 pb-6">
        <div>
            <h1 class="text-3xl font-black tracking-tighter uppercase">UnicrisAI</h1>
            <p class="text-xs tracking-[0.2em] text-gray-400 mt-1">DEEP TECH • AI • SEA</p>
        </div>
        <div class="text-right">
            <p class="text-xs font-mono text-gray-400">{datetime.now().strftime('%Y-%m-%d')}</p>
        </div>
    </header>

    <main class="max-w-4xl mx-auto px-6 py-12">
"""

# 4. Fetch and Process News
for category, url in FEEDS.items():
    html_content += f"<h2 class='text-sm font-bold uppercase tracking-widest text-gray-400 mt-12 mb-6 border-l-4 border-black pl-3' id='{category}'>{category}</h2>"
    feed = feedparser.parse(url)
    
    # Take the top 3 articles per category to keep it clean
    for entry in feed.entries[:3]:
        summary = get_ai_summary(entry.title, entry.get('summary', ''))
        html_content += f"""
        <div class="news-card">
            <h3 class="text-xl font-medium leading-tight mb-3">
                <a href="{entry.link}" target="_blank" class="hover:text-gray-500 transition-colors">{entry.title}</a>
            </h3>
            <p class="text-gray-600 leading-relaxed text-sm mb-4">{summary}</p>
            <a href="{entry.link}" target="_blank" class="text-[10px] uppercase tracking-widest font-bold border-b border-black pb-1">Read Article →</a>
        </div>
        """

html_content += """
    </main>
    <footer class="max-w-4xl mx-auto px-6 py-20 text-center text-[10px] text-gray-300 uppercase tracking-[0.3em]">
        &copy; 2026 UNICRISAI • AUTOMATED INTELLIGENCE
    </footer>
</body>
</html>
"""

# 5. Save the generated HTML
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
