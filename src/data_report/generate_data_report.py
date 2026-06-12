import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os, sys
from src.exception import CustomException

class DashboardGenerator:
    def __init__(self, data):
        self.data = data.drop_duplicates(subset=['Product Name', 'Name', 'Comment'])

    def display_general_info(self):
        st.header('Executive Summary')
        
        clean_data = self.data.copy()
        clean_data['Numeric_Price'] = pd.to_numeric(clean_data['Price'].astype(str).str.replace('₹', '').str.replace(',', ''), errors='coerce')
        clean_data['Numeric_Global_Rating'] = pd.to_numeric(clean_data['Over_All_Rating'], errors='coerce')

        total_products = clean_data['Product Name'].nunique()
        total_reviews = len(clean_data)
        
        product_grouped = clean_data.groupby('Product Name').agg({
            'Numeric_Price': 'mean',
            'Numeric_Global_Rating': 'first' 
        }).reset_index()
        
        avg_market_price = product_grouped['Numeric_Price'].mean()
        avg_market_rating = product_grouped['Numeric_Global_Rating'].mean()

        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(label="🛍️ Total Products", value=f"{total_products}")
        with col2:
            st.metric(label="📝 Reviews Analyzed", value=f"{total_reviews}")
        with col3:
            price_display = f"₹{avg_market_price:,.2f}" if pd.notnull(avg_market_price) else "N/A"
            st.metric(label="💰 Avg Market Price", value=price_display)
        with col4:
            rating_display = f"{avg_market_rating:.2f} ★" if pd.notnull(avg_market_rating) else "N/A"
            st.metric(label="⭐ Avg Global Rating", value=rating_display)
        
        st.divider()
        
        st.header('General Information')
        
        plot_df = product_grouped.dropna(subset=['Numeric_Global_Rating', 'Numeric_Price']).copy()
        
        plot_df['Short Name'] = plot_df['Product Name'].apply(lambda x: (x[:30] + '...') if len(x) > 30 else x)

        fig_pie = px.pie(
            plot_df, 
            values='Numeric_Global_Rating', 
            names='Short Name',
            title='Rating Weight Distribution'
        )
        fig_pie.update_traces(textposition='inside', textinfo='label+percent')
        fig_pie.update_layout(showlegend=True) 
        st.plotly_chart(fig_pie, width='stretch')

        st.divider()

        fig_bar = px.bar(
            plot_df, 
            x='Short Name', 
            y='Numeric_Price', 
            color='Short Name',
            title='Average Price Comparison',
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_bar.update_layout(showlegend=True, xaxis_title="", yaxis_title="Average Price (₹)")
        st.plotly_chart(fig_bar, width='stretch')

        st.divider()

    def display_advanced_visualizations(self):
        st.header('Advanced Data Insights')
        
        plot_data = self.data.copy()
        plot_data['Numeric_Rating'] = pd.to_numeric(plot_data['Rating'], errors='coerce')
        plot_data['Numeric_Price'] = pd.to_numeric(plot_data['Price'].astype(str).str.replace('₹', '').str.replace(',', ''), errors='coerce')
        
        plot_data = plot_data.dropna(subset=['Numeric_Rating', 'Numeric_Price'])

        if plot_data.empty:
            st.warning("Not enough valid numeric data to generate advanced graphs.")
            return

        group_cols = ['Product Index', 'Product Name'] if 'Product Index' in plot_data.columns else ['Product Name']
        
        avg_stats = plot_data.groupby(group_cols).agg({
            'Numeric_Rating': 'mean', 
            'Numeric_Price': 'mean'
        }).reset_index()
        
        def make_display_name(row):
            name = row['Product Name']
            short = (name[:35] + '...') if len(name) > 35 else name
            if 'Product Index' in row:
                return f"{int(row['Product Index'])}. {short}"
            return short
            
        avg_stats['Display Name'] = avg_stats.apply(make_display_name, axis=1)

        tab1, tab2, tab3 = st.tabs(["📊 Rating Distribution", "💰 Price vs Rating", "🏆 Product Leaderboard"])

        with tab1:
            st.subheader("Total Scraped Rating Distribution")
            st.caption("A breakdown of all individual reviews scraped during this session.")
            
            rating_counts = plot_data['Numeric_Rating'].value_counts().reset_index()
            rating_counts.columns = ['Star Rating', 'Count']
            
            fig1 = px.bar(
                rating_counts, 
                x='Star Rating', 
                y='Count', 
                color='Star Rating',
                color_continuous_scale='Viridis',
                text='Count'
            )
            fig1.update_xaxes(type='category', categoryorder='array', categoryarray=[1, 2, 3, 4, 5])
            st.plotly_chart(fig1, width='stretch')

        with tab2:
            st.subheader("Does Price Affect Rating?")
            st.caption("Each dot represents a unique product. Hover to see full details.")
            
            fig2 = px.scatter(
                avg_stats, 
                x='Numeric_Price', 
                y='Numeric_Rating', 
                hover_name='Product Name',
                text='Product Index' if 'Product Index' in avg_stats.columns else None,
                size='Numeric_Price', 
                color='Numeric_Rating',
                color_continuous_scale='RdYlGn',
                labels={'Numeric_Price': 'Average Price (₹)', 'Numeric_Rating': 'Scraped Avg Rating'}
            )
            fig2.update_traces(textposition='top center')
            st.plotly_chart(fig2, width='stretch')

        with tab3:
            st.subheader("Top Products by Scraped Rating")
            
            avg_rating = avg_stats.sort_values(by='Numeric_Rating', ascending=True)
            
            fig3 = px.bar(
                avg_rating, 
                x='Numeric_Rating', 
                y='Display Name',
                orientation='h',
                color='Numeric_Rating',
                color_continuous_scale='RdYlGn',
                hover_name='Product Name',
                labels={'Numeric_Rating': 'Average Star Rating', 'Display Name': ''}
            )
            fig3.update_layout(showlegend=False)
            st.plotly_chart(fig3, width='stretch')
    
    def display_product_sections(self):
        
        st.header('Product Sections')
        product_names = self.data['Product Name'].unique()

        for product_name in product_names:
            product_data = self.data[self.data['Product Name'] == product_name].copy()
            
            p_index = f"{product_data['Product Index'].iloc[0]}. " if 'Product Index' in product_data.columns else ""
            
            with st.expander(f"{p_index}📦 {product_name} ({len(product_data)} Reviews Loaded)", expanded=False):
                
                sort_option = st.selectbox(
                    "Sort Reviews By:",
                    ["Date (Newest First)", "Date (Oldest First)", "Rating (High to Low)", "Rating (Low to High)"],
                    key=f"sort_{product_name}"
                )
                
                product_data['Numeric_Rating'] = pd.to_numeric(product_data['Rating'], errors='coerce')
                product_data['Clean_Date'] = pd.to_datetime(product_data['Date'], errors='coerce')
                
                col1, col2 = st.columns(2)
                with col1:
                    avg_price = pd.to_numeric(product_data['Price'].astype(str).str.replace('₹', '').str.replace(',', ''), errors='coerce').mean()
                    actual_rating = product_data['Over_All_Rating'].iloc[0] if 'Over_All_Rating' in product_data.columns else "N/A"
                    
                    st.markdown(f"💰 **Average Price:** ₹{avg_price:.2f}")
                    st.markdown(f"⭐ **Global Product Rating:** {actual_rating}")
                    st.markdown(f"📊 **Total Synced Reviews:** {len(product_data)}") 
                    
                    st.subheader('Global Verified Ratings')
                    
                    if 'Total_5_Star' in product_data.columns:
                        st.write(f"▪️ 5★ Ratings: **{product_data['Total_5_Star'].iloc[0]}**")
                        st.write(f"▪️ 4★ Ratings: **{product_data['Total_4_Star'].iloc[0]}**")
                        st.write(f"▪️ 3★ Ratings: **{product_data['Total_3_Star'].iloc[0]}**")
                        st.write(f"▪️ 2★ Ratings: **{product_data['Total_2_Star'].iloc[0]}**")
                        st.write(f"▪️ 1★ Ratings: **{product_data['Total_1_Star'].iloc[0]}**")
                    else:
                        st.warning("No global data found. Please run a fresh scrape search.")
                        
                with col2:
                    st.subheader('Reviews Sub-list')
                    if not product_data.empty:
                        for _, row in product_data.head(10).iterrows():
                            badge = "🔹" if row['Numeric_Rating'] >= 4.0 else "🔻"
                            st.markdown(f"{badge} **{row['Rating']}★** ({row['Date']}) - *{row['Name']}*")
                            st.caption(f"\"{row['Comment']}\"")
                            st.write("---")
                    else:
                        st.info("No reviews available to sort.")