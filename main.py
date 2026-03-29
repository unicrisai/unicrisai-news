import os
import json
import feedparser
from datetime import datetime
from google import genai

# --- 1. SETUP ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

try:
    client = genai.Client(api_key=GEMINI_KEY)
    # This force-checks for the most common stable model
    TARGET_MODEL = "gemini-1.5-flash" 
    print(f"Targeting model: {TARGET_MODEL}")
except Exception as e:
    print(f"Setup Error: {e}")
    TARGET_MODEL = None

RSS_URL = "https://news.google.com/rss?q=artificial+intelligence+deep+tech&hl=en-US&gl=US&ceid=US:en"

def fetch_news():
    print("Fetching news...")
    feed = feedparser.parse(RSS_URL)
    return [{"title": e.title, "link": e.link} for e in feed.entries[:8]]

def summarize_news(articles):
    if not TARGET_MODEL or not GEMINI_KEY:
        return "AI configuration missing."
    
    headlines = "\n".join([f"- {a['title']}" for a in articles])
    prompt = f"Summarize these tech headlines into 3 catchy bullet points:\n{headlines}"
    
    try:
        response = client.models.generate_content(model=TARGET_MODEL, contents=prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Summary generation failed. Check API quota."

def update_files(summary, articles):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # We use a simple structure to avoid f-string backslash errors
    html_summary = summary.replace('\n', '<br>')
    links = "".join([f'<li><a href="{a["link"]}" target="_blank">{a["title"]}</a></li>' for a in articles])

    style = """
    body { font-family: sans-serif; max-width: 800px; margin: auto; padding: 20px; background: #f4f7f6; }
    .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    h1 { color: #1a73e8; }
    """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head><style>{style}</style></head>
    <body>
        <div class="card">
            <h1>UnicrisAI News</h1>
            <p><small>Updated: {timestamp}</small></p>
            <hr>
            <h3>🤖 AI Summary</h3>
            <p>{html_summary}</p>
            <hr>
            <h3>Links</h3>
            <ul>{links}</ul>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(full_html)
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump({"date": timestamp, "summary": summary}, f)

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        summary_text = summarize_news(news_data)
        update_files(summary_text, news_data)
        print("Files updated successfully.")
