import pandas as pd
import streamlit as st
from src.constants import SESSION_PRODUCT_KEY
from src.data_report.generate_data_report import DashboardGenerator

def create_analysis_page(review_data: pd.DataFrame):
    if review_data is not None and not review_data.empty:
        st.success("Analysis Data Loaded Successfully!")
        
        with st.expander("View Raw Scraped Data"):
            st.dataframe(review_data, hide_index=True)
            
        dashboard = DashboardGenerator(review_data)
        dashboard.display_general_info()
        dashboard.display_advanced_visualizations()
        dashboard.display_product_sections()

try:
    product_query = st.session_state.get(SESSION_PRODUCT_KEY, "")
    
    if st.session_state.get("data") == True and product_query != "":
        data = st.session_state.get("scraped_dataframe", pd.DataFrame())

        if not data.empty:
            if '_id' in data.columns:
                data = data.drop(columns=['_id'])
            
            create_analysis_page(data)
        else:
            st.warning("No Data Available for analysis. Please Go to search page.")
    else:
        st.info("Please go to the Search Page to scrape a product first.")
            
except Exception as e:
    st.error(f"Error loading analysis: {e}")