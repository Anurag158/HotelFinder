from pathlib import Path
import hashlib
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "hotel_recommender_features.csv"
DATA_FILE_GZ = BASE_DIR / "data" / "hotel_recommender_features.csv.gz"

# These are the real columns in the cleaned dataset.
HOTEL_COLUMNS = [
    "hotelcode", "hotelname", "address", "city", "country", "zipcode",
    "propertytype", "starrating", "latitude", "longitude", "url", "curr",
    "room_record_count", "distinct_room_types", "distinct_amenities",
    "hotel_amenities", "room_types", "valid_rate_count", "avg_onsiterate",
    "median_onsiterate", "min_observed_onsiterate", "max_observed_onsiterate",
    "avg_discount", "promo_rate_share", "breakfast_rate_share", "rate_currency",
    "first_rate_date", "last_rate_date", "min", "max", "Diff_Min", "Diff_Max",
    "Score"
]

def load_hotels():
    """Read the cleaned one-row-per-hotel feature table."""
    # Prefer the original CSV when present; otherwise read the GitHub-friendly
    # gzip-compressed copy. pandas detects gzip from the .gz extension.
    dataset_path = DATA_FILE if DATA_FILE.exists() else DATA_FILE_GZ
    if not dataset_path.exists():
        raise FileNotFoundError(
            "Dataset not found. Keep hotel_recommender_features.csv or "
            "hotel_recommender_features.csv.gz in the data/ directory."
        )
    df = pd.read_csv(dataset_path, low_memory=False)
    # Numeric columns are converted safely so missing values remain missing.
    numeric = [
        "hotelcode", "starrating", "latitude", "longitude", "room_record_count",
        "distinct_room_types", "distinct_amenities", "valid_rate_count",
        "avg_onsiterate", "median_onsiterate", "min_observed_onsiterate",
        "max_observed_onsiterate", "avg_discount", "promo_rate_share",
        "breakfast_rate_share", "min", "max", "Score"
    ]
    for col in numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["hotelname", "city", "country", "address", "propertytype", "curr", "rate_currency"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
    return df

def format_hotel_records(df):
    """Convert pandas rows into template-safe dictionaries."""
    records = []
    for _, row in df.iterrows():
        records.append({
            "hotelcode": int(row["hotelcode"]) if pd.notna(row.get("hotelcode")) else "",
            "image_file": (
                f"hotel_{(int(hashlib.sha256(str(int(row['hotelcode'])).encode('utf-8')).hexdigest()[:8], 16) % 50) + 1:02d}.jpg"
                if pd.notna(row.get("hotelcode")) else "hotel_01.jpg"
            ),
            "hotelname": row.get("hotelname") if pd.notna(row.get("hotelname")) and str(row.get("hotelname")).strip() else "Unnamed hotel",
            "city": row.get("city") if pd.notna(row.get("city")) and str(row.get("city")).strip() else "Unknown city",
            "country": row.get("country") if pd.notna(row.get("country")) else "",
            "address": row.get("address") if pd.notna(row.get("address")) else "",
            "propertytype": row.get("propertytype") if pd.notna(row.get("propertytype")) else "",
            "starrating": float(row["starrating"]) if pd.notna(row.get("starrating")) else None,
            "currency": (row.get("rate_currency") if pd.notna(row.get("rate_currency")) and str(row.get("rate_currency")).strip() else (row.get("curr") if pd.notna(row.get("curr")) else "")),
            "avg_price": float(row["avg_onsiterate"]) if pd.notna(row.get("avg_onsiterate")) else None,
            "median_price": float(row["median_onsiterate"]) if pd.notna(row.get("median_onsiterate")) else None,
            "min_price": float(row["min_observed_onsiterate"]) if pd.notna(row.get("min_observed_onsiterate")) else None,
            "max_price": float(row["max_observed_onsiterate"]) if pd.notna(row.get("max_observed_onsiterate")) else None,
            "rate_count": int(row["valid_rate_count"]) if pd.notna(row.get("valid_rate_count")) else 0,
            "room_types": row.get("room_types") if pd.notna(row.get("room_types")) else "",
            "amenities": row.get("hotel_amenities") if pd.notna(row.get("hotel_amenities")) else "",
            "url": row.get("url") if pd.notna(row.get("url")) else "",
            "latitude": float(row["latitude"]) if pd.notna(row.get("latitude")) else None,
            "longitude": float(row["longitude"]) if pd.notna(row.get("longitude")) else None,
        })
    return records

@app.context_processor
def inject_globals():
    return {"site_name": "HotelFinder"}

@app.route("/")
def index():
    df = load_hotels()
    # Feature the highest-rated hotels; use rate count as a tie-breaker.
    featured = df.sort_values(
        ["starrating", "valid_rate_count"],
        ascending=[False, False],
        na_position="last"
    ).head(9)
    cities = sorted([x for x in df["city"].dropna().astype(str).unique() if x.strip()])[:]
    countries = sorted([x for x in df["country"].dropna().astype(str).unique() if x.strip()])
    return render_template(
        "index.html",
        hotels=format_hotel_records(featured),
        hotel_count=len(df),
        city_count=df["city"].nunique(),
        country_count=df["country"].nunique(),
        cities=cities[:300],
        countries=countries[:300]
    )

@app.route("/search", methods=["GET"])
def search():
    df = load_hotels()
    query = request.args.get("q", "").strip()
    city = request.args.get("city", "").strip()
    country = request.args.get("country", "").strip()
    min_rating_raw = request.args.get("min_rating", "").strip()
    max_price_raw = request.args.get("max_price", "").strip()
    price_currency = request.args.get("currency", "").strip().upper()
    has_price = request.args.get("has_price", "") == "1"

    filtered = df.copy()

    if query:
        search_cols = ["hotelname", "city", "country", "address", "propertytype"]
        mask = pd.Series(False, index=filtered.index)
        for col in search_cols:
            mask |= filtered[col].fillna("").astype(str).str.contains(query, case=False, regex=False)
        filtered = filtered[mask]

    if city:
        filtered = filtered[
            filtered["city"].fillna("").astype(str).str.contains(city, case=False, regex=False)
        ]

    if country:
        filtered = filtered[
            filtered["country"].fillna("").astype(str).str.contains(country, case=False, regex=False)
        ]

    if min_rating_raw:
        try:
            min_rating = float(min_rating_raw)
            filtered = filtered[pd.to_numeric(filtered["starrating"], errors="coerce") >= min_rating]
        except ValueError:
            pass

    if has_price:
        filtered = filtered[pd.to_numeric(filtered["avg_onsiterate"], errors="coerce").notna()]

    if price_currency:
        currency_col = filtered["rate_currency"].fillna("").astype(str).str.upper()
        # When rate currency is absent, use the hotel's metadata currency.
        currency_col = currency_col.where(currency_col.ne(""), filtered["curr"].fillna("").astype(str).str.upper())
        filtered = filtered[currency_col == price_currency]

    if max_price_raw:
        try:
            max_price = float(max_price_raw)
            filtered = filtered[
                pd.to_numeric(filtered["avg_onsiterate"], errors="coerce").notna()
                & (pd.to_numeric(filtered["avg_onsiterate"], errors="coerce") <= max_price)
            ]
        except ValueError:
            pass

    # Put hotels with a recorded price first, then order by rating.
    filtered = filtered.sort_values(
        ["valid_rate_count", "starrating"],
        ascending=[False, False],
        na_position="last"
    )
    total = len(filtered)
    page_raw = request.args.get("page", "1")
    try:
        page = max(1, int(page_raw))
    except ValueError:
        page = 1
    per_page = 24
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages)
    shown = filtered.iloc[(page - 1) * per_page: page * per_page]

    currencies = sorted(
        set(df["rate_currency"].dropna().astype(str).str.upper())
        | set(df["curr"].dropna().astype(str).str.upper())
    )
    return render_template(
        "search.html",
        hotels=format_hotel_records(shown),
        total=total, page=page, pages=pages,
        q=query, city=city, country=country,
        min_rating=min_rating_raw, max_price=max_price_raw,
        currency=price_currency, has_price=has_price,
        currencies=[c for c in currencies if c]
    )

@app.route("/recommend")
def recommend():
    df = load_hotels()
    # Dataset-based ranking: rating, observed valid rate count, then lower median rate.
    rated = df[df["valid_rate_count"].fillna(0) > 0].copy()
    if rated.empty:
        rated = df.copy()
    rated = rated.sort_values(
        ["starrating", "valid_rate_count", "median_onsiterate"],
        ascending=[False, False, True],
        na_position="last"
    ).head(24)
    return render_template("recommend.html", hotels=format_hotel_records(rated))

@app.route("/hotel/<int:hotelcode>")
def hotel_detail(hotelcode):
    df = load_hotels()
    match = df[pd.to_numeric(df["hotelcode"], errors="coerce") == hotelcode]
    if match.empty:
        return render_template("404.html"), 404
    return render_template("hotel_detail.html", hotel=format_hotel_records(match.head(1))[0])

@app.route("/about")
def about():
    return render_template("about.html")

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
