import psycopg2
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# === CONFIG ===
DB_CONFIG = {
    "dbname": "affiliate_db",
    "user": "your_db_user",
    "password": "your_db_password",
    "host": "localhost",
    "port": "5432"
}

API_KEY = "YOUR_CUELINKS_API_KEY"


# === DATABASE HELPER ===
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


# === AFFILIATE LINK ===
def get_affiliate_link(url):
    api_url = "https://api.cuelinks.com/deeplink.json"
    headers = {"Authorization": f"Token {API_KEY}", "Content-Type": "application/json"}
    payload = {"url": url}
    r = requests.post(api_url, json=payload, headers=headers)
    data = r.json()
    return data["data"]["affiliate_link"]


# === SCRAPER ===
def scrape_product(url, store):
    headers = {"User-Agent": "Mozilla/5.0"}
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, "html.parser")

    title, price, image = "No Title", "0", ""

    if store == "ajio":
        title = soup.find("h1").text.strip() if soup.find("h1") else "No Title"
        price = soup.find("span", {"class": "prod-sp"}).text.strip("₹") if soup.find("span", {"class": "prod-sp"}) else "0"
        image = soup.find("img", {"class": "rilrtl-lazy-img"})["src"] if soup.find("img", {"class": "rilrtl-lazy-img"}) else ""

    elif store == "myntra":
        title = soup.find("h1").text.strip() if soup.find("h1") else "No Title"
        price = soup.find("span", {"class": "pdp-price"}).text.replace("Rs.", "").strip() if soup.find("span", {"class": "pdp-price"}) else "0"
        image = soup.find("img", {"class": "image-grid-image"})["src"] if soup.find("img", {"class": "image-grid-image"}) else ""

    elif store == "amazon":
        title = soup.find("span", {"id": "productTitle"})
        title = title.text.strip() if title else "No Title"
        price = soup.find("span", {"class": "a-price-whole"})
        price = price.text.strip().replace(",", "") if price else "0"
        image = soup.find("img", {"id": "landingImage"})
        image = image["src"] if image else ""

    elif store == "flipkart":
        title = soup.find("span", {"class": "B_NuCI"})
        title = title.text.strip() if title else "No Title"
        price = soup.find("div", {"class": "_30jeq3"})
        price = price.text.strip("₹").replace(",", "") if price else "0"
        image = soup.find("img", {"class": "_396cs4"})
        image = image["src"] if image else ""

    return {"title": title, "price": float(price.replace("₹", "").replace(",", "") or 0), "image": image}


# === SAVE TO DB ===
def save_product(store, url, category="general"):
    details = scrape_product(url, store)
    affiliate = get_affiliate_link(url)

    conn = get_db_connection()
    cur = conn.cursor()

    # Insert or update
    cur.execute("""
        INSERT INTO products (store, title, price, image, product_url, affiliate_link, category, last_updated)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (product_url) DO UPDATE
        SET price = EXCLUDED.price,
            image = EXCLUDED.image,
            affiliate_link = EXCLUDED.affiliate_link,
            last_updated = EXCLUDED.last_updated
        RETURNING id;
    """, (store, details["title"], details["price"], details["image"], url, affiliate, category, datetime.now()))

    product_id = cur.fetchone()[0]

    # Log price history
    cur.execute("INSERT INTO price_history (product_id, price, checked_at) VALUES (%s, %s, %s)",
                (product_id, details["price"], datetime.now()))

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Saved {details['title']} ({store})")


# === MAIN ===
if __name__ == "__main__":
    # Example URLs
    urls = {
        "ajio": ["https://www.ajio.com/men-black-running-shoes/p/461432222_black"],
        "myntra": ["https://www.myntra.com/shoes/puma-shoes/12345678/buy"],
        "amazon": ["https://www.amazon.in/dp/B0C12345"],
        "flipkart": ["https://www.flipkart.com/puma-shoes/p/itm123456"]
    }

    for store, links in urls.items():
        for link in links:
            save_product(store, link, category="shoes")
