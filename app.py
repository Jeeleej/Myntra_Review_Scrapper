import pandas as pd
import streamlit as st
import json

st.set_page_config(
    page_title="Ajio Market Insights | Live Product Review Scraper",
    page_icon="🛒",
    layout="wide"
)

from src.scrapper.scrape import ScrapeReviews

try:
    from src.cloud_io import MongoIO
    MONGO_AVAILABLE = True
except Exception:
    MONGO_AVAILABLE = False

SESSION_PRODUCT_KEY = "product_name"

SORT_OPTIONS = {
    "Recommended":      "",
    "What's New":       "new",
    "Popularity":       "popularity",
    "Better Discount":  "discount",
    "Price: High to Low": "price_desc",
    "Price: Low to High": "price_asc",
    "Customer Rating":  "rating",
}

st.title("🛒 Ajio Review Scrapper")
st.markdown("Search for any product on Ajio and scrape real customer reviews.")

if "data" not in st.session_state:
    st.session_state["data"] = False
if SESSION_PRODUCT_KEY not in st.session_state:
    st.session_state[SESSION_PRODUCT_KEY] = ""
if "scraped_dataframe" not in st.session_state:
    st.session_state["scraped_dataframe"] = pd.DataFrame()


def form_input():
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        product = st.text_input("🔍 Search Products", value=st.session_state[SESSION_PRODUCT_KEY], placeholder="e.g. blue jeans, running shoes...")
    with col2:
        no_of_products = st.number_input("No. of Products", step=1, min_value=1, max_value=8, value=4)
    with col3:
        sort_choice = st.selectbox("Sort by", options=list(SORT_OPTIONS.keys()))

    if st.button("🚀 Scrape Reviews", use_container_width=True):
        if product.strip() == "":
            st.warning("Please enter a product name.")
            return

        with st.spinner(f"Scraping Ajio reviews for '{product}'... Please wait, this may take a minute."):
            try:
                scrapper = ScrapeReviews(
                    product_name=product,
                    no_of_products=int(no_of_products),
                    sort_by=SORT_OPTIONS[sort_choice]
                )
                scrapped_data = scrapper.get_review_data()

                if scrapped_data is not None and not scrapped_data.empty:
                    st.session_state["data"] = True
                    st.session_state[SESSION_PRODUCT_KEY] = product
                    st.session_state["scraped_dataframe"] = scrapped_data

                    if MONGO_AVAILABLE:
                        try:
                            MongoIO().store_reviews(product_name=product, reviews=scrapped_data)
                        except Exception:
                            pass

                    st.success(f"✅ Successfully scraped {len(scrapped_data)} reviews!")
                else:
                    st.error(
                        "Scraper ran but found 0 reviews. "
                        "Ajio may be rate-limiting or the product has no reviews yet."
                    )
            except Exception as e:
                st.error(f"An error occurred: {e}")

    if st.session_state["data"] and not st.session_state["scraped_dataframe"].empty:
        df = st.session_state["scraped_dataframe"]
        st.markdown(f"### 📊 Results for: **{st.session_state[SESSION_PRODUCT_KEY]}**")

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Reviews", len(df))
        with col2:
            try:
                avg = pd.to_numeric(df["Rating"], errors="coerce").mean()
                st.metric("Avg Rating", f"{avg:.1f} ⭐")
            except Exception:
                st.metric("Avg Rating", "N/A")
        with col3:
            st.metric("Products Scraped", df["Product Index"].nunique() if "Product Index" in df.columns else "N/A")
        with col4:
            try:
                positive = (pd.to_numeric(df["Rating"], errors="coerce") >= 4).sum()
                st.metric("Positive Reviews", positive)
            except Exception:
                st.metric("Positive Reviews", "N/A")

        st.dataframe(df, hide_index=True, use_container_width=True)

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"ajio_reviews_{st.session_state[SESSION_PRODUCT_KEY].replace(' ', '_')}.csv",
            mime="text/csv",
        )


form_input()
