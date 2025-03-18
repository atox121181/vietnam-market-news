import requests
import pandas as pd
import feedparser
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Cấu hình email ---
SENDER_EMAIL = "atox121181@gmail.com"  # Thay bằng email của bạn
SENDER_PASSWORD = "kfng bcyv frqe mxnj"  # Thay bằng mật khẩu ứng dụng (App Password nếu dùng Gmail)
RECEIVER_EMAIL = "atox121181@gmail.com"  # Email của tôi hoặc của bạn để nhận dữ liệu

# --- Hàm gửi email ---
def send_email(subject, body, attachment_path=None):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    if attachment_path:
        with open(attachment_path, 'rb') as f:
            part = MIMEText(f.read(), 'plain', 'utf-8')
            part.add_header('Content-Disposition', 'attachment', filename=attachment_path)
            msg.attach(part)
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
    print(f"Đã gửi email: {subject}")

# --- Hàm thu thập tin tức từ NewsAPI ---
def collect_newsapi():
    api_key = "f15580bb18004764b6bf1f95f86991d8"  # Thay bằng API key của bạn
    url = f"https://newsapi.org/v2/everything?q=Vietnam+stock+market+OR+Vietnam+economy&language=en&sortBy=publishedAt&apiKey={api_key}"
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
    return news_list

# --- Hàm thu thập tin tức từ CafeF RSS ---
def collect_cafef_rss():
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

# --- Hàm thu thập tin tức từ Vietstock RSS ---
def collect_vietstock_rss():
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

# --- Hàm chính ---
def main():
    print("Bắt đầu thu thập dữ liệu...")
    
    # Thu thập tin tức
    newsapi_data = collect_newsapi()
    cafef_data = collect_cafef_rss()
    vietstock_data = collect_vietstock_rss()
    all_news = newsapi_data + cafef_data + vietstock_data
    
    # Lưu tin tức vào CSV
    news_df = pd.DataFrame(all_news)
    news_df["Ngày thu thập"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    news_file = "vietnam_market_news.csv"
    news_df.to_csv(news_file, index=False, encoding="utf-8-sig")
    
    # Yêu cầu tìm kiếm trên X (ghi vào file để gửi)
    x_search_query = "Thị trường chứng khoán Việt Nam hôm nay"
    with open("x_search_request.txt", "w", encoding="utf-8") as f:
        f.write(x_search_query)
    
    # Gửi email với dữ liệu
    subject = f"Dữ liệu tin tức thị trường Việt Nam - {datetime.now().strftime('%Y-%m-%d')}"
    body = "Dữ liệu tin tức từ NewsAPI, CafeF, Vietstock và yêu cầu tìm kiếm X đã được đính kèm."
    send_email(subject, body, news_file)
    
    print(f"Hoàn tất. Dữ liệu đã được lưu vào {news_file} và gửi qua email.")

if __name__ == "__main__":
    main()
