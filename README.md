<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white"/>
  <img src="https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white"/>
  <img src="https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white"/>
</p>

<h1 align="center">🛍️ Myntra Review Scrapper</h1>

<p align="center">
  A web scraping tool built with <strong>Python</strong> and <strong>Streamlit</strong> that lets you search Myntra products, scrape customer reviews, and explore interactive analytics — all from a clean browser-based UI.
</p>

---

## ✨ Features

- 🔍 **Product Search** — Search any product on Myntra by keyword
- 🔢 **Configurable Scraping** — Choose how many products to fetch and sort order (e.g. What's New, Popularity, Price)
- ⭐ **Review Collection** — Scrapes customer reviews including star ratings, reviewer names, and review text
- 📊 **Analytics Dashboard** — Auto-generated charts including:
  - Rating weight distribution (pie chart)
  - Average price comparison (bar chart)
  - Total scraped rating distribution
  - Price vs Rating scatter
  - Product leaderboard
- 📋 **Executive Summary** — At-a-glance stats: total products, reviews analyzed, avg market price, and avg global rating
- 🗃️ **Raw Data View** — Inspect all scraped data in its raw JSON form

---

## ⚙️ How It Works

```
Input: Search Query (e.g. "Genz Tshirts for man")
    │
    ▼
Selenium Browser Automation   ← Launches Chrome & searches Myntra
    │
    ▼
Product Listing Scrape        ← Collects product URLs from search results
    │
    ▼
Per-Product Review Scrape     ← Opens each product page, extracts reviews
    │  (BeautifulSoup4 parsing)
    ▼
Data Aggregation              ← Merges ratings, prices, reviewer info
    │
    ▼
Streamlit Dashboard           ← Displays reviews + interactive Plotly charts
    │
    ▼
Output: Review Sub-lists, Global Ratings, Executive Summary, Charts
```

**Key steps explained:**

- **Selenium** automates Chrome to browse Myntra, handle dynamic content, and paginate results
- **BeautifulSoup4** parses the raw HTML to extract ratings, prices, reviewer names, and text
- **Pandas / NumPy** aggregate and clean the collected data
- **Plotly** renders interactive charts in the Streamlit UI
- **MongoDB** (optional) can be used to persist scraped data across sessions

---

## 🖼️ Screenshots

### Scraper UI
Search for products, set quantity, and choose sort order before scraping.

### Review Data
View per-product review sub-lists with ratings, dates, and reviewer names.

### Analysis Dashboard
Executive summary and interactive charts generated from the scraped data.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI / Frontend | Streamlit |
| Scraping | Selenium + BeautifulSoup4 |
| Data Processing | Pandas, NumPy |
| Visualizations | Plotly |
| Database (optional) | MongoDB (pymongo) |
| Environment Config | python-dotenv |

---

## ⚙️ Prerequisites

- Python 3.10+
- Google Chrome installed
- ChromeDriver matching your Chrome version

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Jeeleej/Myntra_Review_Scrapper.git
cd Myntra_Review_Scrapper
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root if you plan to use MongoDB:

```env
MONGO_URI=your_mongodb_connection_string
```

### 4. Run the app

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 📖 Usage

1. Enter a search term in the **Search Products** field (e.g. `Genz Tshirts for man`)
2. Set the **number of products** to scrape using the `+` / `-` controls
3. Choose a **Sort By** option from the dropdown
4. Click **Scrape Reviews** and wait for data to load
5. Navigate to **Generate Analysis** in the sidebar to view the full dashboard

---

## 📁 Project Structure

```
Myntra_Review_Scrapper/
├── app.py                      # Main Streamlit app (scraper UI)
├── pages/
│   └── generate_analysis.py    # Analytics dashboard page
├── src/                        # Core scraping logic
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 📦 Dependencies

```
pandas==2.0.3
numpy==1.26.4
bs4
chromedriver-binary
pymongo
gunicorn
plotly
pysocks
python-dotenv
selenium
streamlit
tiktoken
certifi
```

---

## ⚠️ Disclaimer

This project is intended for **educational and personal use only**. Scraping websites may violate their Terms of Service. Always review [Myntra's ToS](https://www.myntra.com/termsofuse) before use. Use responsibly.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

This project is open source. Feel free to fork and build on it.

---

<p align="center">Made with ❤️ by <a href="https://github.com/Jeeleej">Jeeleej</a></p>
