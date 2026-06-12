import pandas as pd
import streamlit as st
import json

st.set_page_config(
    page_title="Myntra Market Insights | Live Product Review Scraper",
    page_icon="logo.jpg",
    layout="wide"
)

from src.scrapper.scrape import ScrapeReviews
try:
    from src.cloud_io import MongoIO
    MONGO_AVAILABLE = True
except Exception:
    MONGO_AVAILABLE = False

SESSION_PRODUCT_KEY = "product_name"

seo_schema = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "Myntra Market Insights",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Web",
    "description": "A live web scraper and sentiment analysis dashboard for tracking Myntra product reviews, pricing, and customer feedback."
}
st.markdown(
    f'<script type="application/ld+json">{json.dumps(seo_schema)}</script>',
    unsafe_allow_html=True
)

st.title("🛍️ Myntra Review Scrapper")

if "data" not in st.session_state:
    st.session_state["data"] = False

if SESSION_PRODUCT_KEY not in st.session_state:
    st.session_state[SESSION_PRODUCT_KEY] = ""

if "scraped_dataframe" not in st.session_state:
    st.session_state["scraped_dataframe"] = pd.DataFrame()

SORT_OPTIONS = {
    "Recommended": "",
    "What's New": "new",
    "Popularity": "popularity",
    "Better Discount": "discount",
    "Price: High to Low": "price_desc",
    "Price: Low to High": "price_asc",
    "Customer Rating": "rating"
}


def form_input():
    product = st.text_input("Search Products", value=st.session_state[SESSION_PRODUCT_KEY])
    no_of_products = st.number_input("No of products to search", step=1, min_value=1, max_value=8, value=4)
    sort_choice = st.selectbox("Sort by", options=list(SORT_OPTIONS.keys()), key="sort_state")

    if st.button("Scrape Reviews"):
        if product.strip() == "":
            st.warning("Please enter a product name.")
            return

        with st.spinner("Scraping data... Please wait."):
            try:
                sort_param = SORT_OPTIONS[sort_choice]
                scrapper = ScrapeReviews(
                    product_name=product,
                    no_of_products=int(no_of_products),
                    sort_by=sort_param
                )
                scrapped_data = scrapper.get_review_data()

                if scrapped_data is not None and not scrapped_data.empty:
                    st.session_state["data"] = True
                    st.session_state[SESSION_PRODUCT_KEY] = product
                    st.session_state["scraped_dataframe"] = scrapped_data

                    if MONGO_AVAILABLE:
                        try:
                            mongoio = MongoIO()
                            mongoio.store_reviews(product_name=product, reviews=scrapped_data)
                            print("Stored Data into MongoDB")
                        except Exception as mongo_err:
                            print(f"MongoDB store failed (non-fatal): {mongo_err}")

                    st.success("Successfully scraped data!")
                else:
                    st.error(
                        "Scraper ran but found 0 reviews. "
                        "Myntra may be blocking the bot or the product has no reviews."
                    )
            except Exception as e:
                st.error(f"An error occurred: {e}")

    if st.session_state["data"] and not st.session_state["scraped_dataframe"].empty:
        st.markdown(f"### Currently Viewing: {st.session_state[SESSION_PRODUCT_KEY]}")
        st.dataframe(st.session_state["scraped_dataframe"], hide_index=True)


if __name__ == "__main__":
    form_input()
