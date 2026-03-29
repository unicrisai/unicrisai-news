import os
import json
import feedparser
from datetime import datetime
from google import genai

# --- 1. SETUP & CONFIG ---
try:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
except Exception as e:
    print(f"Error: GEMINI_API_KEY not found or invalid. {e}")
    exit(1)

RSS_FEED_URL = "https://news.google.com/rss?q=artificial+intelligence+deep+tech&hl=en-US&gl=US&ceid=US:en"

def fetch_news():
    print("Fetching RSS Feed...")
    feed = feedparser.parse(RSS_FEED_URL)
    articles = []
    for entry in feed.entries[:8]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": getattr(entry, 'published', 'Date Unknown')
        })
    return articles

def summarize_news(articles):
    print("Generating AI Insights...")
    headlines = "\n".join([f"- {a['title']}" for a in articles])
    prompt = f"Summarize these tech headlines into 3 catchy bullet points for a newsletter:\n{headlines}"
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Summary currently unavailable."

def update_files(summary, articles):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # FIX: Prepare the summary for HTML BEFORE putting it in the f-string
    # This avoids the "backslash in f-string" error
    html_summary = summary.replace('\n', '<br>')

    # 1. Update data.json
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump({"last_update": timestamp, "summary": summary, "articles": articles}, f, indent=4)

    # 2. Update index.html
    links_html = "".join([f'<li><a href="{a["link"]}" target="_blank">{a["title"]}</a></li>' for a in articles])
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>UnicrisAI News</title>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 20px; color: #333; }}
            .summary {{ background: #f4f4f4; padding: 15px; border-left: 5px solid #1a73e8; }}
        </style>
    </head>
    <body>
        <h1>UnicrisAI News Update</h1>
        <p><strong>Updated:</strong> {timestamp}</p>
        <div class="summary">
            {html_summary}
        </div>
        <h3>Top Stories</h3>
        <ul>{links_html}</ul>
        <p><a href="archive.html">View Archive</a></p>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

    # 3. Update archive.html
    if not os.path.exists("archive.html"):
        with open("archive.html", "w", encoding="utf-8") as f:
            f.write("<h1>Archive</h1><hr>")
            
    with open("archive.html", "a", encoding="utf-8") as f:
        f.write(f"<p>{timestamp}: {summary[:100]}... <a href='index.html'>Full Story</a></p><hr>\n")

if __name__ == "__main__":
    items = fetch_news()
    if items:
        report = summarize_news(items)
        update_files(report, items)
        print("Success!")
