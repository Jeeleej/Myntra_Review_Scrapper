import pandas as pd
import streamlit as st
from src.cloud_io import MongoIO
from src.constants import SESSION_PRODUCT_KEY
from src.scrapper.scrape import ScrapeReviews

st.set_page_config(page_title="Myntra Review Scrapper")
st.title("Myntra Review Scrapper")

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
                
                mongoio = MongoIO()
                mongoio.store_reviews(product_name=product, reviews=scrapped_data)
                print("Stored Data into mongodb")
                st.success("Successfully scraped and stored data!")
            else:
                st.error("Scraper ran, but found 0 reviews. Myntra might be loading too slowly or the product has no reviews.")

    if st.session_state["data"] and not st.session_state["scraped_dataframe"].empty:
        st.markdown(f"### Currently Viewing: {st.session_state[SESSION_PRODUCT_KEY]}")
        st.dataframe(st.session_state["scraped_dataframe"], hide_index=True)

if __name__ == "__main__":
    form_input()