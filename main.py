import requests
import pandas as pd
import feedparser
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# --- Cấu hình từ GitHub Secrets ---
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# --- Hàm gửi email ---
def send_email(subject, body, attachment_paths=None):
    try:
        if not all([SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL]):
            raise ValueError("Thiếu thông tin email từ GitHub Secrets")
        
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        if attachment_paths:
            for path in attachment_paths:
                with open(path, 'rb') as f:
                    part = MIMEText(f.read(), 'plain', 'utf-8')
                    part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(path))
                    msg.attach(part)
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"Đã gửi email: {subject}")
    except Exception as e:
        print(f"Lỗi gửi email: {e}")

# --- Hàm thu thập tin tức từ NewsAPI ---
def collect_newsapi():
    try:
        if not NEWSAPI_KEY:
            raise ValueError("Thiếu NEWSAPI_KEY từ GitHub Secrets")
        
        url = f"https://newsapi.org/v2/everything?q=Vietnam+stock+market+OR+Vietnam+economy&language=en&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
        response = requests.get(url)
        news_list = []
        if response.status_code == 200:
            articles = response.json()["articles"]
            for article in articles[:10]:
                news_list.append({
                    "Tiêu đề": article["title"],
                    "Nguồn": article["source"]["name"],
                    "Mô tả": article["description"] or "N/A",
                    "Link": article["url"],
                    "Ngày đăng": article["publishedAt"]
                })
        else:
            print(f"Lỗi NewsAPI: {response.status_code}")
        return news_list
    except Exception as e:
        print(f"Lỗi NewsAPI: {e}")
        return []

# --- Hàm thu thập tin tức từ CafeF RSS ---
def collect_cafef_rss():
    try:
        feed = feedparser.parse("https://cafef.vn/rss/thi-truong-chung-khoan")
        news_list = []
        for entry in feed.entries[:10]:
            news_list.append({
                "Tiêu đề": entry.title,
                "Nguồn": "CafeF",
                "Mô tả": entry.summary if "summary" in entry else "N/A",
                "Link": entry.link,
                "Ngày đăng": entry.published if "published" in entry else "N/A"
            })
        return news_list
    except Exception as e:
        print(f"Lỗi CafeF RSS: {e}")
        return []

# --- Hàm thu thập tin tức từ Vietstock RSS ---
def collect_vietstock_rss():
    try:
        feed = feedparser.parse("https://vietstock.vn/chung-khoan.rss")
        news_list = []
        for entry in feed.entries[:10]:
            news_list.append({
                "Tiêu đề": entry.title,
                "Nguồn": "Vietstock",
                "Mô tả": entry.summary if "summary" in entry else "N/A",
                "Link": entry.link,
                "Ngày đăng": entry.published if "published" in entry else "N/A"
            })
        return news_list
    except Exception as e:
        print(f"Lỗi Vietstock RSS: {e}")
        return []

# --- Hàm chính ---
def main():
    print("Bắt đầu thu thập dữ liệu...")
    
    newsapi_data = collect_newsapi()
    cafef_data = collect_cafef_rss()
    vietstock_data = collect_vietstock_rss()
    all_news = newsapi_data + cafef_data + vietstock_data
    
    if not all_news:
        print("Không thu thập được tin tức nào.")
        return
    
    news_df = pd.DataFrame(all_news)
    news_df["Ngày thu thập"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    news_file = f"vietnam_market_news_{datetime.now().strftime('%Y-%m-%d')}.csv"
    news_df.to_csv(news_file, index=False, encoding="utf-8-sig")
    
    x_search_query = "Thị trường chứng khoán Việt Nam hôm nay OR VN-Index OR Vietnam stock market"
    x_file = f"x_search_request_{datetime.now().strftime('%Y-%m-%d')}.txt"
    with open(x_file, "w", encoding="utf-8") as f:
        f.write(x_search_query)
    
    subject = f"Dữ liệu tin tức thị trường Việt Nam - {datetime.now().strftime('%Y-%m-%d')}"
    body = "Dữ liệu tin tức từ NewsAPI, CafeF, Vietstock và yêu cầu tìm kiếm X đã được đính kèm."
    send_email(subject, body, [news_file, x_file])
    
    print(f"Hoàn tất. Dữ liệu đã được lưu vào {news_file} và gửi qua email.")

if __name__ == "__main__":
    main()
