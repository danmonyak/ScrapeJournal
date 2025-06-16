# ScrapeJournal: Nature Article Metadata Collector

This project scrapes research article metadata from [Nature.com](https://www.nature.com/) and stores it in a local MySQL database for further analysis or querying. The metadata includes titles, authors, publication dates, DOIs, ORCID IDs, article types, and more.

---

See the published [Tableau workbook](https://public.tableau.com/app/profile/daniel.monyak/viz/NaturePortfolioBreastCancer/NaturePortfolio) for results and interpretations.

---

## Project Structure

```
ScrapeJournal/
├── bin/                  # Shell scripts for starting/stopping MySQL  (excluded from Git)
├── data/                 # Contains login credentials (excluded from Git)
├── src/                  # All main source code and logic modules
│   ├── sitelogic/        # Site-specific scraping logic for Nature.com
│   └── util.py           # Utility functions (insertion, parsing, etc.)
├── download.py           # Main script to scrape and insert data
├── schemaSetup.sql       # SQL schema for database structure
└── README.md             # This file
```

---

## Requirements

- Python 3.8+
- MySQL Server (running locally)
- Python packages:
  - `requests`
  - `beautifulsoup4`
  - `sqlalchemy`
  - `mysql-connector-python`

Install dependencies:

```bash
pip install requests beautifulsoup4 sqlalchemy mysql-connector-python
```

---

## Setup

1. **Create your MySQL schema:**

   Run the schema setup:

   ```bash
   mysql -u root -p < src/schemaSetup.sql
   ```

2. **Add your MySQL credentials:**

   Create a file at `data/db_login.json`:

   ```json
   {
     "user": "your_username",
     "password": "your_password"
   }
   ```

   This file is excluded from version control by `.gitignore`.

---

## Running the Scraper

Run the main scraping script:

```bash
python download.py
```

The script fetches article listings from Nature's research articles pages, parses metadata from individual articles, and populates your MySQL database tables (`ARTICLES`, `AUTHORS`, `ARTICLES_AUTHORS`).

You can modify the starting page or set limits directly inside `download.py`.

---

## Code Overview

- **src/sitelogic/Nature.py** – Extracts metadata from article previews on Nature's index pages.
- **src/sitelogic/NatureArticle.py** – Extracts full metadata from individual article pages.
- **src/util.py** – Helper functions for database inserts, scraping wrappers, and field cleaning.
- **download.py** – The main script that ties everything together.

---

## Database Schema

Key tables:

- `ARTICLES` — Article-level metadata (title, DOI, date, type)
- `AUTHORS` — Author names and ORCID IDs
- `ARTICLES_AUTHORS` — Many-to-many join table linking articles and authors

See `src/schemaSetup.sql` for full definitions.

---

## Notes

- The scraper respects pagination but stops after a page limit (default: 50 pages).
- Duplicate DOIs are ignored to prevent redundant inserts.
- Make sure the structure of Nature.com's HTML hasn't changed; otherwise, CSS selectors may need updating.

