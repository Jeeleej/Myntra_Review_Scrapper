from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin, quote
import re
import pandas as pd
import sys
import time


class CustomException(Exception):
    def __init__(self, error_message, error_detail=None):
        super().__init__(str(error_message))
        self.error_message = str(error_message)

    def __str__(self):
        return self.error_message


class ScrapeReviews:

    def __init__(self, product_name: str, no_of_products: int, sort_by: str = ""):
        self.product_name = product_name
        self.no_of_products = no_of_products
        self.sort_by = sort_by
        self.product_title = "Unknown Product"
        self.product_rating_value = "0"
        self.product_price = "0"

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Use system-installed Chromium (installed via packages.txt on Streamlit Cloud)
        try:
            options.binary_location = "/usr/bin/chromium"
            service = Service("/usr/bin/chromedriver")
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception:
            # Fallback: let Selenium find Chrome automatically
            self.driver = webdriver.Chrome(options=options)

        stealth(
            self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

    def scrape_product_urls(self, product_name):
        try:
            encoded_query = quote(product_name)

            # Build Ajio search URL with optional sort
            sort_map = {
                "new":        "freshness",
                "popularity": "popularity",
                "discount":   "discount",
                "price_desc": "price-desc",
                "price_asc":  "price-asc",
                "rating":     "rating",
            }
            sort_param = sort_map.get(self.sort_by, "")

            if sort_param:
                base_url = f"https://www.ajio.com/search/?text={encoded_query}&sort={sort_param}"
            else:
                base_url = f"https://www.ajio.com/search/?text={encoded_query}"

            print(f"--- DEBUG: Loading URL: {base_url} ---")
            self.driver.get(base_url)
            time.sleep(6)

            # Wait for product grid
            try:
                WebDriverWait(self.driver, 12).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "rilrtl-products-list"))
                )
            except Exception:
                print("--- DEBUG: Timed out waiting for rilrtl-products-list ---")

            page_html = self.driver.page_source
            print(f"--- DEBUG: Page HTML length: {len(page_html)} ---")

            soup = bs(page_html, "html.parser")

            # Ajio product cards
            product_cards = soup.find_all("div", {"class": re.compile(r"rilrtl-products-list__item", re.IGNORECASE)})
            print(f"--- DEBUG: Found {len(product_cards)} product cards ---")

            product_urls = []
            for card in product_cards:
                link = card.find("a", href=True)
                if link:
                    href = link["href"]
                    if not href.startswith("http"):
                        href = urljoin("https://www.ajio.com", href)
                    product_urls.append(href)

            return product_urls

        except Exception as e:
            print(f"--- DEBUG: Error in scrape_product_urls: {e} ---")
            return []

    def extract_reviews(self, product_link):
        try:
            self.driver.get(product_link)
            time.sleep(4)

            page_html = self.driver.page_source
            soup = bs(page_html, "html.parser")

            # Product title
            title_elem = (
                soup.find("h1", {"class": re.compile(r"title|name|product", re.IGNORECASE)})
                or soup.find("title")
            )
            if title_elem:
                self.product_title = title_elem.get_text(strip=True).replace(" | Ajio", "").replace("| AJIO", "").strip()
            else:
                self.product_title = "Unknown Product"

            # Overall rating
            self.product_rating_value = "0"
            rating_elem = soup.find(attrs={"class": re.compile(r"rating.*count|overall.*rating|prod-rating", re.IGNORECASE)})
            if not rating_elem:
                rating_elem = soup.find("span", {"class": re.compile(r"rating", re.IGNORECASE)})
            if rating_elem:
                text = rating_elem.get_text(strip=True)
                match = re.search(r"(\d+\.?\d*)", text)
                if match:
                    self.product_rating_value = match.group(1)

            # Price
            self.product_price = "0"
            price_elem = soup.find(attrs={"class": re.compile(r"price|cost|amount", re.IGNORECASE)})
            if price_elem:
                self.product_price = price_elem.get_text(strip=True)

            # Check if reviews section exists — look for review/rating link or section
            review_link = (
                soup.find("a", {"class": re.compile(r"review|rating", re.IGNORECASE)})
                or soup.find("div", {"class": re.compile(r"review.*section|ratings.*review", re.IGNORECASE)})
                or soup.find("a", href=re.compile(r"review", re.IGNORECASE))
            )

            # Even if no explicit link, return the product_link to extract reviews from same page
            return product_link

        except Exception as e:
            print(f"--- DEBUG: Error in extract_reviews: {e} ---")
            return None

    def scroll_to_load_reviews(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def extract_products(self, product_link):
        try:
            # On Ajio, reviews are on the same product page — scroll to load them
            self.driver.get(product_link)
            time.sleep(4)
            self.scroll_to_load_reviews()

            page_html = self.driver.page_source
            soup = bs(page_html, "html.parser")

            # --- Global star counts ---
            global_counts = {"5": "0", "4": "0", "3": "0", "2": "0", "1": "0"}
            try:
                # Ajio shows star breakdown in elements like "5 star", "4 star" etc.
                star_rows = soup.find_all(attrs={"class": re.compile(r"star.*bar|rating.*bar|bar.*rating", re.IGNORECASE)})
                if not star_rows:
                    star_rows = soup.find_all("div", {"class": re.compile(r"ratingStar|ratingBar", re.IGNORECASE)})
                for idx, row in enumerate(star_rows[:5]):
                    count_text = row.get_text(strip=True)
                    nums = re.findall(r"\d+", count_text)
                    star_num = str(5 - idx)
                    if nums:
                        global_counts[star_num] = nums[-1]
            except Exception as e:
                print(f"--- DEBUG: Star count extraction failed: {e} ---")

            # --- Individual reviews ---
            # Ajio review containers
            review_containers = soup.find_all(
                attrs={"class": re.compile(r"review.*item|user.*review|prod.*review|reviewCard|review-card", re.IGNORECASE)}
            )
            if not review_containers:
                review_containers = soup.find_all("div", {"class": re.compile(r"review", re.IGNORECASE)})

            print(f"--- DEBUG: Found {len(review_containers)} review containers ---")

            if not review_containers:
                return pd.DataFrame()

            reviews = []
            pos_count = 0
            neg_count = 0

            for container in review_containers:
                if pos_count >= 7 and neg_count >= 5:
                    break

                # Rating
                try:
                    rating_elem = container.find(attrs={"class": re.compile(r"rating|star|score", re.IGNORECASE)})
                    rating_text = rating_elem.get_text(strip=True) if rating_elem else self.product_rating_value
                    match = re.search(r"(\d+\.?\d*)", rating_text)
                    rating_str = match.group(1) if match else self.product_rating_value
                    rating_val = float(rating_str)
                except Exception:
                    rating_str = self.product_rating_value
                    rating_val = float(rating_str) if rating_str else 0.0

                is_positive = rating_val >= 4.0
                is_negative = rating_val <= 3.0

                if is_positive and pos_count >= 5:
                    continue
                if is_negative and neg_count >= 5:
                    continue

                # Comment
                try:
                    comment_elem = container.find(attrs={"class": re.compile(r"comment|text|body|content|description", re.IGNORECASE)})
                    comment = comment_elem.get_text(strip=True) if comment_elem else container.get_text(strip=True)
                    comment = comment[:500] if comment else "No comment given"
                except Exception:
                    comment = "No comment given"

                # Reviewer name
                try:
                    name_elem = container.find(attrs={"class": re.compile(r"name|user|author|reviewer", re.IGNORECASE)})
                    name = name_elem.get_text(strip=True) if name_elem else "Verified Buyer"
                except Exception:
                    name = "Verified Buyer"

                # Date
                try:
                    date_elem = container.find(attrs={"class": re.compile(r"date|time|posted|when", re.IGNORECASE)})
                    if not date_elem:
                        date_elem = container.find("time")
                    date = date_elem.get_text(strip=True) if date_elem else "Recent"
                except Exception:
                    date = "Recent"

                mydict = {
                    "Product Name":  self.product_title,
                    "Over_All_Rating": self.product_rating_value,
                    "Price":         self.product_price,
                    "Date":          date,
                    "Rating":        rating_str,
                    "Name":          name,
                    "Comment":       comment,
                    "Total_5_Star":  global_counts["5"],
                    "Total_4_Star":  global_counts["4"],
                    "Total_3_Star":  global_counts["3"],
                    "Total_2_Star":  global_counts["2"],
                    "Total_1_Star":  global_counts["1"],
                }
                reviews.append(mydict)

                if is_positive:
                    pos_count += 1
                elif is_negative:
                    neg_count += 1

            return pd.DataFrame(reviews, columns=[
                "Product Name", "Over_All_Rating", "Price",
                "Date", "Rating", "Name", "Comment",
                "Total_5_Star", "Total_4_Star", "Total_3_Star", "Total_2_Star", "Total_1_Star"
            ])

        except Exception as e:
            print(f"--- DEBUG: Error extracting products: {e} ---")
            return pd.DataFrame()

    def get_review_data(self) -> pd.DataFrame:
        try:
            product_urls = self.scrape_product_urls(product_name=self.product_name) or []
            print(f"--- DEBUG: Found {len(product_urls)} product URLs ---")

            if not product_urls:
                self.driver.quit()
                return pd.DataFrame()

            product_details = []
            for url in product_urls:
                if len(product_details) >= self.no_of_products:
                    break

                print(f"--- DEBUG: Processing: {url} ---")
                product_link = self.extract_reviews(url)

                if product_link:
                    product_detail = self.extract_products(product_link)
                    if not product_detail.empty:
                        product_details.append(product_detail)
                        print(f"--- DEBUG: Collected {len(product_details)} / {self.no_of_products} ---")
                    else:
                        print("--- DEBUG: No reviews on this product, skipping ---")
                else:
                    print("--- DEBUG: Could not load product page, skipping ---")

            self.driver.quit()

            if product_details:
                data = pd.concat(product_details, axis=0, ignore_index=True)
                unique_products = data["Product Name"].unique()
                index_mapping = {name: i + 1 for i, name in enumerate(unique_products)}
                data.insert(0, "Product Index", data["Product Name"].map(index_mapping))
                data.to_csv("data.csv", index=False)
                return data

            return pd.DataFrame()

        except Exception as e:
            try:
                self.driver.quit()
            except Exception:
                pass
            raise CustomException(e, sys)
