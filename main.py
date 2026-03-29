import os
import json
import feedparser
from datetime import datetime
from google import genai

# --- 1. SETUP & AUTO-MODEL DETECTION ---
try:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    # Auto-detect a working model
    available_models = client.models.list()
    TARGET_MODEL = next((m.name for m in available_models if 'generateContent' in m.supported_methods), None)
    print(f"Detected working model: {TARGET_MODEL}")
except Exception as e:
    print(f"Setup Error: {e}")
    TARGET_MODEL = None

RSS_FEED_URL = "https://news.google.com/rss?q=artificial+intelligence+deep+tech&hl=en-US&gl=US&ceid=US:en"

def fetch_news():
    print("Fetching news...")
    feed = feedparser.parse(RSS_FEED_URL)
    return [{"title": e.title, "link": e.link} for e in feed.entries[:8]]

def summarize_news(articles):
    if not TARGET_MODEL:
        return "AI model not available."
    
    print(f"Summarizing with {TARGET_MODEL}...")
    headlines = "\n".join([f"- {a['title']}" for a in articles])
    prompt = f"Summarize these tech headlines into 3 catchy bullet points for a newsletter:\n{headlines}"
    
    try:
        response = client.models.generate_content(model=TARGET_MODEL, contents=prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Our AI is taking a coffee break. Check back shortly!"

def update_files(summary, articles):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    html_summary = summary.replace('\n', '<br>')
    links_html = "".join([f'<li><a href="{a["link"]}" target="_blank">{a["title"]}</a></li>' for a in articles])

    # Standardized CSS to keep the design consistent
    css = """
    body { font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 20px; color: #2c3e50; background: #fdfdfd; }
    h1 { color: #1a73e8; border-bottom: 2px solid #eee; padding-bottom: 10px; }
    .summary-box { background: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e1e4e8; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px; }
    ul { padding-left: 20px; }
    li { margin-bottom: 12px; }
    a { color: #1a73e8; text-decoration: none; font-weight: 500; }
    a:hover { text-decoration: underline; }
    .footer { font-size: 0.85em; color: #7f8c8d; margin-top: 60px; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }
    """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>UnicrisAI News</title>
        <style>{css}</style>
    </head>
    <body>
        <h1>UnicrisAI News Update</h1>
        <p><strong>Last Updated:</strong> {timestamp} (UTC)</p>
        
        <div class="summary-box">
            <h3>🤖 AI Executive Insights</h3>
            <p>{html_summary}</p>
        </div>

        <h3>Top Deep Tech Stories</h3>
        <ul>{links_html}</ul>

        <div class="footer">
            Built by UnicrisAI Innovation Engine | <a href="archive.html">History</a>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)
    with open("data.json", "w", encoding="utf-8") as f: json.dump({"summary": summary, "articles": articles}, f)
    
    if not os.path.exists("archive.html"):
        with open("archive.html", "w", encoding="utf-8") as f: f.write("<h1>Archive</h1><hr>")
    with open("archive.html", "a", encoding="utf-8") as f:
        f.write(f"<p>{timestamp}: {summary[:100]}... <a href='index.html'>Full Story</a></p><hr>")

if __name__ == "__main__":
    news = fetch_news()
    if news:
        report = summarize_news(news)
        update_files(report, news)
        print("Success!")
