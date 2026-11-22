# HotelFinder — dataset-driven Flask website

This version uses the cleaned dataset from the earlier data-cleaning stage.

## Included dataset
`data/hotel_recommender_features.csv.gz` is the compressed primary file used by the Flask app (pandas reads it directly). If you have the original `data/hotel_recommender_features.csv`, the app will use that instead. It contains one row per cleaned hotel and joined hotel-level room/rate features (106,193 hotel records). `data/hotel_room_features.csv` is also included for reference.

## Run locally

```bash
python -m venv venv
```

Windows:
```bash
venv\Scripts\activate
```

macOS/Linux:
```bash
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Start Flask:
```bash
python app.py
```

Open `http://127.0.0.1:5000`.

## Features
- Homepage with shared responsive navigation
- Search by hotel name, city, country, address, and property type
- Filters for city, country, minimum star rating, maximum average observed rate, rate currency, and presence of rate data
- Paginated search results
- Hotel detail pages with joined room and historical rate summaries
- Dataset-based recommendation ranking

## Important dataset notes
The rate observations were collected in October 2019 for stay dates in October 2019–January 2020. The app labels them as historical and does not present them as live prices or availability. Hotels without rate observations remain searchable and show price as unavailable.

The source dataset has no user–hotel interaction labels, so the recommendation page uses a transparent content/data ranking (star rating, valid rate count, median observed rate), not collaborative filtering.

## Project structure
```text
HotelFinder_DataDriven/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── hotel_recommender_features.csv.gz
│   ├── hotel_room_features.csv
│   └── README_cleaning_report.txt
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── search.html
│   ├── recommend.html
│   ├── hotel_detail.html
│   ├── about.html
│   ├── 404.html
│   └── _hotel_cards.html
└── static/
    └── css/
        └── style.css
```
