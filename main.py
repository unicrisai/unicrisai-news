import os
import json
import feedparser
from datetime import datetime
from google import genai

# --- 1. SETUP & CONFIG ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

try:
    client = genai.Client(api_key=GEMINI_KEY)
    # This checks for the most stable model available to your key
    available_models = client.models.list()
    TARGET_MODEL = next((m.name for m in available_models if 'generateContent' in m.supported_methods), "gemini-1.5-flash")
    print(f"Using model: {TARGET_MODEL}")
except Exception as e:
    print(f"Setup Error: {e}")
    TARGET_MODEL = None

# Using a focused query for Deep Tech and AI
RSS_URL = "https://news.google.com/rss?q=artificial+intelligence+deep+tech+startup&hl=en-US&gl=US&ceid=US:en"

def fetch_news():
    print("Fetching Deep Tech feed...")
    feed = feedparser.parse(RSS_URL)
    return [{"title": e.title, "link": e.link, "source": getattr(e, 'source', {'title': 'News'}).get('title', 'Tech News')} for e in feed.entries[:10]]

def summarize_news(articles):
    if not TARGET_MODEL or not GEMINI_KEY:
        return "AI Executive Insights are temporarily offline."
    
    headlines = "\n".join([f"- {a['title']}" for a in articles])
    prompt = f"Act as a Deep Tech Analyst. Summarize these headlines into 3 bold, professional bullet points for the UnicrisAI Innovation Engine:\n{headlines}"
    
    try:
        response = client.models.generate_content(model=TARGET_MODEL, contents=prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "AI model not available. Please check the API quota."

def update_files(summary, articles):
    timestamp = datetime.now().strftime("%B %d, %Y | %H:%M")
    html_summary = summary.replace('\n', '<br>')
    
    # Build the link list with source tags
    links_html = "".join([
        f'<li><a href="{a["link"]}" target="_blank">{a["title"]}</a> <span class="source-tag">{a["source"]}</span></li>' 
        for a in articles
    ])

    style = """
    :root { --primary: #1a73e8; --dark: #2c3e50; --bg: #f8f9fa; }
    body { font-family: 'Inter', -apple-system, sans-serif; line-height: 1.6; max-width: 900px; margin: auto; padding: 40px 20px; background: var(--bg); color: var(--dark); }
    .container { background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }
    .header { border-bottom: 2px solid #eee; margin-bottom: 30px; padding-bottom: 20px; }
    h1 { color: var(--primary); margin: 0; font-size: 2.2em; letter-spacing: -1px; }
    .timestamp { font-size: 0.9em; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px; }
    .summary-section { background: #f0f7ff; padding: 25px; border-radius: 12px; border-left: 6px solid var(--primary); margin-bottom: 40px; }
    .summary-section h3 { margin-top: 0; color: var(--primary); }
    .news-list { list-style: none; padding: 0; }
    .news-list li { margin-bottom: 18px; padding-bottom: 10px; border-bottom: 1px solid #f1f1f1; }
    .news-list a { color: var(--dark); text-decoration: none; font-weight: 500; font-size: 1.1em; transition: 0.2s; }
    .news-list a:hover { color: var(--primary); }
    .source-tag { font-size: 0.75em; background: #eee; padding: 2px 8px; border-radius: 4px; margin-left: 10px; color: #666; vertical-align: middle; }
    .footer { text-align: center; margin-top: 50px; font-size: 0.9em; border-top: 1px solid #eee; padding-top: 20px; }
    .archive-link { display: inline-block; margin-top: 20px; color: var(--primary); font-weight: bold; }
    """

    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>UnicrisAI Innovation Engine</title>
        <style>{style}</style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>UnicrisAI News</h1>
                <div class="timestamp">Innovation Engine Update • {timestamp}</div>
            </div>
            
            <div class="summary-section">
                <h3>🤖 AI Executive Insights</h3>
                <p>{html_summary}</p>
            </div>

            <h3>Top Deep Tech Stories</h3>
            <ul class="news-list">{links_html}</ul>
            
            <div class="footer">
                <p>Curated by <strong>UnicrisAI</strong> Innovation Engine</p>
                <a href="archive.html" class="archive-link">Explore Full Archive →</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    # 1. Update index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    
    # 2. Update archive.html (RESTORES HISTORY)
    if not os.path.exists("archive.html"):
        with open("archive.html", "w", encoding="utf-8") as f:
            f.write("<html><head><title>UnicrisAI Archive</title></head><body><h1>UnicrisAI History</h1><hr>")
            
    with open("archive.html", "a", encoding="utf-8") as f:
        f.write(f"<div><strong>{timestamp}</strong>: {summary[:150]}... <a href='index.html'>Read Update</a></div><hr>")

    # 3. Update data.json
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump({"date": timestamp, "summary": summary, "articles": articles}, f, indent=4)

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        summary_text = summarize_news(news_data)
        update_files(summary_text, news_data)
        print("UnicrisAI Engine: Files generated successfully.")
