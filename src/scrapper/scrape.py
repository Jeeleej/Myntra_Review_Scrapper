from selenium import webdriver
from selenium.webdriver.common.by import By
from src.exception import CustomException
from bs4 import BeautifulSoup as bs
import re
import pandas as pd
import os, sys
import time
from urllib.parse import urljoin
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote

from packaging import version
sys.modules['distutils.version'] = version

import undetected_chromedriver as uc
import time

class ScrapeReviews:
    def __init__(self, product_name: str, no_of_products: int, sort_by: str = ""):
        self.product_name = product_name
        self.no_of_products = no_of_products
        self.sort_by = sort_by  
        
        options = Options()
        
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        self.driver = uc.Chrome(options=options, version_main=120)
        
        self.product_name = product_name
        self.no_of_products = no_of_products

    def scrape_product_urls(self, product_name):
        try:
            search_string = product_name.replace(" ", "-")
            encoded_query = quote(search_string)
            
            if self.sort_by != "":
                base_url = f"https://www.myntra.com/{search_string}?rawQuery={encoded_query}&sort={self.sort_by}"
            else:
                base_url = f"https://www.myntra.com/{search_string}?rawQuery={encoded_query}"
                
            self.driver.get(url)
            time.sleep(5) 
            
            try:
                self.driver.save_screenshot("debug_bot_block.png")
                st.error("Scraper failed to find products. Here is what the bot actually sees:")
                st.image("debug_bot_block.png")
            except Exception as e:
                print(f"Could not take screenshot: {e}")

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "results-base"))
            )
            
            myntra_text = self.driver.page_source
            print(f"--- DEBUG: Scraped HTML Length: {len(myntra_text)} ---")
            
            myntra_html = bs(myntra_text, "html.parser")
            pclass = myntra_html.findAll("ul", {"class": "results-base"})
            print(f"--- DEBUG: Found 'results-base' grid: {len(pclass) > 0} ---")

            product_urls = []
            if pclass:
                for i in pclass:
                    href = i.findAll("a", href=True)
                    for product_no in range(len(href)):
                        t = href[product_no]["href"]
                        product_urls.append(t)
            
            return product_urls

        except Exception as e:
            print(f"--- DEBUG: Error in scrape_product_urls: {e} ---")
            return []  

    def extract_reviews(self, product_link):
        try:
            productLink = urljoin("https://www.myntra.com/", product_link)
            self.driver.get(productLink)
            time.sleep(3.5)
            
            prodRes = self.driver.page_source
            prodRes_html = bs(prodRes, "html.parser")
            
            title_elem = prodRes_html.find("title")
            if title_elem:
                raw_title = title_elem.text.strip()
                
                self.product_title = raw_title.replace(" | Myntra", "").replace("| Myntra", "").strip()
            else:
                self.product_title = "Unknown Product"
            
            self.product_rating_value = "0"
            self.product_price = "0"
            overallRating = prodRes_html.find("div", {"class": "index-overallRating"})

            if overallRating and overallRating.find("div"):
                self.product_rating_value = overallRating.find("div").text.strip()
            
            price_elem = prodRes_html.find("span", {"class": "pdp-price"})
            if price_elem:
                self.product_price = price_elem.text.strip()
            
            product_reviews = prodRes_html.find("a", {"class": "detailed-reviews-allReviews"})
            
            if not product_reviews:
                return None
                
            return product_reviews

        except Exception as e:
            print(f"--- DEBUG: Error in extract_reviews: {e} ---")
            return None
        
    def scroll_to_load_reviews(self):
        self.driver.set_window_size(1920, 1080)
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            self.driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(3) 
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height:
                break
            last_height = new_height

    def extract_products(self, product_reviews):
        try:
            t2 = product_reviews["href"]
            from urllib.parse import urljoin
            Review_link = urljoin("https://www.myntra.com/", t2)
            self.driver.get(Review_link)

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Verified Buyers') or contains(text(), 'Customer Reviews')]"))
                )
            except Exception as e:
                print("--- DEBUG: Timed out waiting for Verified Buyers text ---")

            self.scroll_to_load_reviews()
            review_page = self.driver.page_source
            review_html = bs(review_page, "html.parser")
            global_counts = {"5": "0", "4": "0", "3": "0", "2": "0", "1": "0"}
            
            try:
                count_nodes = review_html.find_all(class_=re.compile("countNode", re.IGNORECASE))
                if not count_nodes or len(count_nodes) < 5:
                    
                    rows = review_html.find_all("div", class_=re.compile("ratingBarProgress|flexRow", re.IGNORECASE))
                    if rows:
                        count_nodes = []
                        for row in rows:
                            
                            texts = list(row.stripped_strings)
                            
                            
                            if texts and texts[0] in ["5", "4", "3", "2", "1"] and texts[-1].isdigit():
                                count_nodes.append(texts[-1])
                                
                if count_nodes and len(count_nodes) >= 5:
                    def get_text(node): return node.text.strip() if hasattr(node, 'text') else str(node)
                    
                    global_counts["5"] = get_text(count_nodes[0])
                    global_counts["4"] = get_text(count_nodes[1])
                    global_counts["3"] = get_text(count_nodes[2])
                    global_counts["2"] = get_text(count_nodes[3])
                    global_counts["1"] = get_text(count_nodes[4])

            except Exception as e:
                print(f"--- DEBUG: Global ratings extract failed: {e} ---")

            review_container = review_html.find("div", class_=re.compile("userReviewsContainer", re.IGNORECASE))
            
            if not review_container:
                return pd.DataFrame()

            user_rating = review_container.find_all("div", class_=re.compile("showRating", re.IGNORECASE))
            user_comment = review_container.find_all("div", class_=re.compile("reviewTextWrapper", re.IGNORECASE))
            user_name = review_container.find_all("div", class_=re.compile("user-review-left", re.IGNORECASE))

            reviews = []
            pos_count = 0
            neg_count = 0
            total_elements = min(len(user_rating), len(user_comment), len(user_name))
            
            for i in range(total_elements):
                
                if pos_count >= 7 and neg_count >= 5:
                    break
                
                try:
                    rating_span = user_rating[i].find("span", class_=re.compile("starRating", re.IGNORECASE))
                    rating_str = rating_span.get_text().strip() if rating_span else str(self.product_rating_value)
                    rating_val = float(rating_str)
                except Exception as e:
                    rating_str = str(self.product_rating_value) or "0"
                    rating_val = float(rating_str)

                is_positive = rating_val >= 4.0
                is_negative = rating_val <= 3.0

                if is_positive and pos_count >= 5:
                    continue
                if is_negative and neg_count >= 5:
                    continue

                try:
                    comment = user_comment[i].text.strip()
                except:
                    comment = "No comment Given"

                try:
                    name_span = user_name[i].find("span")
                    name = name_span.text.strip() if name_span else "Verified Buyer"
                except:
                    name = "Verified Buyer"

                try:
                    spans = user_name[i].find_all("span")
                    date = spans[1].text.strip() if len(spans) > 1 else "Recent"
                except:
                    date = "Recent"

                mydict = {
                    "Product Name": self.product_title,
                    "Over_All_Rating": self.product_rating_value,
                    "Price": self.product_price,
                    "Date": date,
                    "Rating": rating_str,
                    "Name": name,
                    "Comment": comment,
                    "Total_5_Star": global_counts["5"],
                    "Total_4_Star": global_counts["4"],
                    "Total_3_Star": global_counts["3"],
                    "Total_2_Star": global_counts["2"],
                    "Total_1_Star": global_counts["1"],
                }
                
                reviews.append(mydict)
                
                if is_positive:
                    pos_count += 1
                elif is_negative:
                    neg_count += 1

            review_data = pd.DataFrame(
                reviews,
                columns=[
                    "Product Name", "Over_All_Rating", "Price", 
                    "Date", "Rating", "Name", "Comment",
                    "Total_5_Star", "Total_4_Star", "Total_3_Star", "Total_2_Star", "Total_1_Star"
                ],
            )
            return review_data

        except Exception as e:
            print(f"--- DEBUG: Error extracting products: {e} ---")
            return pd.DataFrame()
    
    def skip_products(self, search_string, no_of_products, skip_index):
        product_urls: list = self.scrape_product_urls(search_string, no_of_products + 1)
        product_urls.pop(skip_index)

    def get_review_data(self) -> pd.DataFrame:
        try:
            product_urls = self.scrape_product_urls(product_name=self.product_name)
            
            if product_urls is None:
                product_urls = []
            print(f"--- DEBUG: Found {len(product_urls)} product URLs on search page ---")
            
            if not product_urls:
                self.driver.quit()
                return pd.DataFrame()

            product_details = []

            for url in product_urls:
                if len(product_details) >= self.no_of_products:
                    break
                    
                print(f"--- DEBUG: Checking product: {url} ---")
                review = self.extract_reviews(url)
                
                if review:
                    print("--- DEBUG: Reviews found! Extracting comments... ---")
                    product_detail = self.extract_products(review)
                      
                    if not product_detail.empty:
                        product_details.append(product_detail)
                        print(f"--- DEBUG: Success! Collected {len(product_details)} / {self.no_of_products} products ---")
                    else:
                        print("--- DEBUG: Product skipped (Not enough matching reviews). ---")
                else:
                    print("--- DEBUG: Skipped (No reviews). Moving to next product. ---")

            self.driver.quit()

            if product_details:
                data = pd.concat(product_details, axis=0)
                unique_products = data['Product Name'].unique()
                index_mapping = {name: i+1 for i, name in enumerate(unique_products)}
                data.insert(0, 'Product Index', data['Product Name'].map(index_mapping))
                data.to_csv("data.csv", index=False)
                return data
            
            else:
                return pd.DataFrame()

        except Exception as e:
            try:
                self.driver.quit()
            except:
                pass
            raise CustomException(e, sys)
        
