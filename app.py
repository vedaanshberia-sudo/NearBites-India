
import math
import re
import time
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd
import requests
import streamlit as st

# -------------------- PAGE SETUP --------------------
st.set_page_config(
    page_title="NearBites India",
    page_icon="🍰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

.stApp {
    background: linear-gradient(145deg, #fffaf0 0%, #f4f9e9 52%, #fff0e9 100%);
    color: #26362c;
    font-family: 'DM Sans', sans-serif;
}
.block-container { max-width: 1150px; padding-top: 2rem; padding-bottom: 4rem; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; color: #26362c; }
.hero {
    background: #d9f49b;
    padding: 2rem;
    border-radius: 28px;
    border: 2px solid #26362c;
    box-shadow: 6px 6px 0 #26362c;
    margin-bottom: 1.5rem;
}
.hero h1 { font-size: clamp(2rem, 5vw, 3.6rem); margin: 0; line-height: 1.08; }
.hero p { font-size: 1.05rem; margin: .7rem 0 0; }
.pill {
    display: inline-block;
    background: #f1ddff;
    border: 1px solid #26362c;
    border-radius: 999px;
    padding: 5px 12px;
    margin: 3px 4px 3px 0;
    font-size: .82rem;
    font-weight: 700;
}
.result-card {
    background: #fffdf8;
    border: 1.5px solid #26362c;
    border-radius: 20px;
    padding: 18px;
    margin: 10px 0;
    box-shadow: 3px 3px 0 #d9e4ce;
}
.result-card h3 { margin: 0 0 8px; font-size: 1.25rem; }
.small { color: #59675c; font-size: .9rem; }
div.stButton > button {
    background: #26362c;
    color: white;
    border: 2px solid #26362c;
    border-radius: 14px;
    min-height: 3rem;
    font-weight: 700;
}
div.stButton > button:hover { background: #7958c4; color: white; border-color: #7958c4; }
[data-testid="stTextInput"] input { border-radius: 12px; }
div[data-baseweb="select"] > div { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# -------------------- SETTINGS --------------------
DATA_FILE = Path(__file__).parent / "data" / "zomato_clean.csv"
USER_AGENT = "NearBitesIndia/1.0 (restaurant discovery demo)"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# -------------------- HELPERS --------------------
def clean_text(value):
    if value is None or pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()

def normalize(value):
    value = clean_text(value).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())

def number(value):
    try:
        if pd.isna(value) or value == "":
            return None
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None

def distance_km(lat1, lon1, lat2, lon2):
    radius = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(min(1, math.sqrt(a)))

@st.cache_data(ttl=3600, show_spinner=False)
def load_zomato():
    if not DATA_FILE.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(DATA_FILE, low_memory=False)
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()

def geocode_location(city, state, road):
    parts = [road.strip(), city.strip(), state.strip(), "India"]
    query = ", ".join(p for p in parts if p)
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "in"},
        headers={"User-Agent": USER_AGENT},
        timeout=25,
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        return None
    return {
        "lat": float(results[0]["lat"]),
        "lon": float(results[0]["lon"]),
        "display_name": results[0].get("display_name", query),
    }

def get_tag(tags, *keys):
    for key in keys:
        value = clean_text(tags.get(key, ""))
        if value:
            return value
    return ""

def find_nearby(lat, lon, radius=5000):
    around = f"(around:{radius},{lat},{lon})"
    query = f"""
    [out:json][timeout:35];
    (
      node["amenity"~"^(cafe|restaurant|fast_food|food_court|ice_cream)$"]["name"]{around};
      way["amenity"~"^(cafe|restaurant|fast_food|food_court|ice_cream)$"]["name"]{around};
      relation["amenity"~"^(cafe|restaurant|fast_food|food_court|ice_cream)$"]["name"]{around};
      node["shop"~"^(bakery|pastry|confectionery|coffee)$"]["name"]{around};
      way["shop"~"^(bakery|pastry|confectionery|coffee)$"]["name"]{around};
      relation["shop"~"^(bakery|pastry|confectionery|coffee)$"]["name"]{around};
    );
    out center tags;
    """
    last_error = None
    for endpoint in OVERPASS_URLS:
        try:
            response = requests.post(
                endpoint,
                data={"data": query},
                headers={"User-Agent": USER_AGENT},
                timeout=45,
            )
            response.raise_for_status()
            elements = response.json().get("elements", [])
            places = []
            seen = set()

            for element in elements:
                tags = element.get("tags", {})
                name = get_tag(tags, "name")
                if not name:
                    continue

                coords = element.get("center", element)
                place_lat = number(coords.get("lat"))
                place_lon = number(coords.get("lon"))
                if place_lat is None or place_lon is None:
                    continue

                key = (normalize(name), round(place_lat, 4), round(place_lon, 4))
                if key in seen:
                    continue
                seen.add(key)

                amenity = get_tag(tags, "amenity")
                shop = get_tag(tags, "shop")
                category = shop or amenity or "food place"
                address_parts = [
                    get_tag(tags, "addr:housenumber"),
                    get_tag(tags, "addr:street"),
                    get_tag(tags, "addr:suburb", "addr:neighbourhood"),
                    get_tag(tags, "addr:city"),
                ]
                address = ", ".join(p for p in address_parts if p)

                places.append({
                    "name": name,
                    "category": category.replace("_", " ").title(),
                    "lat": place_lat,
                    "lon": place_lon,
                    "distance": distance_km(lat, lon, place_lat, place_lon),
                    "address": address,
                    "cuisine": get_tag(tags, "cuisine"),
                    "website": get_tag(tags, "website", "contact:website"),
                    "phone": get_tag(tags, "phone", "contact:phone"),
                    "osm_id": f'{element.get("type", "")}/{element.get("id", "")}',
                    "rating": None,
                    "votes": None,
                    "cost": None,
                    "zomato_cuisine": "",
                    "source": "OpenStreetMap",
                })
            return places
        except Exception as exc:
            last_error = exc
            time.sleep(1)

    raise RuntimeError(
        "The nearby-place service is temporarily unavailable. Please try again in a minute."
    ) from last_error

def enrich_with_zomato(places, df, city):
    if df.empty:
        return places

    # Use only records that have usable coordinates.
    lat_col = "latitude"
    lon_col = "longitude"
    name_col = "restaurant_name"
    if not all(c in df.columns for c in [lat_col, lon_col, name_col]):
        return places

    data = df.copy()
    data["_lat"] = pd.to_numeric(data[lat_col], errors="coerce")
    data["_lon"] = pd.to_numeric(data[lon_col], errors="coerce")
    data = data.dropna(subset=["_lat", "_lon"])

    city_col = "city" if "city" in data.columns else None
    city_norm = normalize(city)
    if city_col:
        same_city = data[data[city_col].apply(normalize) == city_norm]
        # If city names differ in the dataset, retain all rows and rely on distance/name.
        if not same_city.empty:
            data = same_city

    for place in places:
        best_row = None
        best_score = 0
        place_name = normalize(place["name"])

        # Coordinate filtering keeps matching local and relatively quick.
        nearby_rows = data[
            (data["_lat"] - place["lat"]).abs() < 0.06
        ]
        nearby_rows = nearby_rows[
            (nearby_rows["_lon"] - place["lon"]).abs() < 0.06
        ]

        for _, row in nearby_rows.iterrows():
            dataset_name = normalize(row.get(name_col, ""))
            if not dataset_name:
                continue
            similarity = SequenceMatcher(None, place_name, dataset_name).ratio()
            km = distance_km(
                place["lat"], place["lon"], float(row["_lat"]), float(row["_lon"])
            )
            if km > 3:
                continue
            score = similarity - (km * 0.02)
            if score > best_score:
                best_score = score
                best_row = row

        if best_row is not None and best_score >= 0.72:
            place["rating"] = number(best_row.get("aggregate_rating"))
            place["votes"] = number(best_row.get("votes"))
            place["cost"] = number(best_row.get("average_cost_for_two_inr"))
            place["zomato_cuisine"] = clean_text(best_row.get("cuisines", ""))
            place["source"] = "OpenStreetMap + Zomato dataset"

    return places

def rank_places(places, priority, kind):
    def score(place):
        category = place["category"].lower()
        cafe_bonus = 2.0 if "cafe" in category or "coffee" in category else 0
        bakery_bonus = 1.5 if any(x in category for x in ["bakery", "pastry", "confectionery"]) else 0
        restaurant_bonus = 1.0 if any(x in category for x in ["restaurant", "food court"]) else 0
        if kind == "Cafés":
            type_bonus = cafe_bonus * 2 + bakery_bonus
        elif kind == "Bakeries & desserts":
            type_bonus = bakery_bonus * 2 + cafe_bonus
        else:
            type_bonus = cafe_bonus + bakery_bonus + restaurant_bonus

        rating = place.get("rating") or 0
        rating_bonus = rating * 0.45 if priority == "Top rated" else 0
        distance_bonus = -place["distance"] * (0.35 if priority == "Closest" else 0.12)
        return type_bonus + rating_bonus + distance_bonus

    filtered = places
    if kind == "Cafés":
        filtered = [p for p in places if any(x in p["category"].lower() for x in ["cafe", "coffee"])]
    elif kind == "Bakeries & desserts":
        filtered = [p for p in places if any(x in p["category"].lower() for x in ["bakery", "pastry", "confectionery", "ice cream"])]

    return sorted(filtered, key=score, reverse=True)

# -------------------- USER INTERFACE --------------------
st.markdown("""
<div class="hero">
  <div class="pill">🇮🇳 MADE FOR INDIA</div>
  <div class="pill">☕ CAFÉS · 🍰 BAKERIES · 🍜 RESTAURANTS</div>
  <h1>Find your next<br>happy food place.</h1>
  <p>Little cafés, lovely bakeries, local favourites and hidden gems — around your chosen location.</p>
</div>
""", unsafe_allow_html=True)

st.subheader("📍 Where are you exploring?")
st.caption("Enter a city and state. Add a road or neighbourhood to narrow the search. No GPS required.")

with st.form("location_form"):
    c1, c2 = st.columns(2)
    with c1:
        city = st.text_input("City *", placeholder="e.g. Guwahati")
        state = st.text_input("State *", placeholder="e.g. Assam")
        road = st.text_input("Road or neighbourhood (optional)", placeholder="e.g. GS Road")
    with c2:
        kind = st.selectbox(
            "What are you craving?",
            ["Everything", "Cafés", "Bakeries & desserts"],
        )
        priority = st.selectbox(
            "Sort your discoveries",
            ["Best overall", "Closest", "Top rated"],
        )
        radius_label = st.selectbox("Search distance", ["3 km", "5 km", "10 km"], index=1)

    submitted = st.form_submit_button("✨ Find my food spots", use_container_width=True)

if submitted:
    if not city.strip() or not state.strip():
        st.error("Please enter both your city and state.")
    else:
        radius = int(radius_label.replace(" km", "")) * 1000
        with st.spinner("Finding your area and searching for lovely food spots..."):
            try:
                location = geocode_location(city, state, road)
                if not location:
                    st.error("We couldn't find that location. Check the spelling and try again.")
                    st.stop()

                st.session_state["near_bites_location"] = location
                places = find_nearby(location["lat"], location["lon"], radius)
                dataset = load_zomato()
                places = enrich_with_zomato(places, dataset, city)
                places = rank_places(places, priority, kind)
                places = [p for p in places if p["distance"] <= radius / 1000]
                st.session_state["near_bites_results"] = places
                st.session_state["near_bites_search"] = {
                    "city": city, "state": state, "road": road,
                    "kind": kind, "priority": priority,
                    "radius": radius_label,
                }
                st.session_state["near_bites_dataset_count"] = len(dataset)
            except requests.exceptions.RequestException:
                st.error("The location or map service is busy. Please try again shortly.")
            except RuntimeError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error("Something went wrong while searching. Please try again.")
                st.caption(f"Technical detail: {exc}")

# -------------------- RESULTS --------------------
if "near_bites_results" in st.session_state:
    results = st.session_state["near_bites_results"]
    location = st.session_state.get("near_bites_location", {})
    search = st.session_state.get("near_bites_search", {})

    st.divider()
    st.subheader("🍓 Your food-place shortlist")
    if location.get("display_name"):
        st.caption(f"Search area: {location['display_name']}")

    dataset_count = st.session_state.get("near_bites_dataset_count", 0)
    st.markdown(
        f'<span class="pill">🗺️ OpenStreetMap results</span>'
        f'<span class="pill">📚 {dataset_count:,} dataset records loaded</span>',
        unsafe_allow_html=True,
    )

    if not results:
        st.info(
            "No matching places were found in this radius. Try a larger search distance "
            "or remove the road/neighbourhood to search a broader area."
        )
    else:
        st.success(f"Found {len(results)} places matching your search.")
        for i, place in enumerate(results, start=1):
            rating = place.get("rating")
            votes = place.get("votes")
            cost = place.get("cost")
            cuisine = place.get("zomato_cuisine") or place.get("cuisine")
            distance = place.get("distance", 0)

            rating_text = f"⭐ {rating:.1f}/5" if rating is not None else "⭐ No dataset rating"
            votes_text = f" · {int(votes):,} votes" if votes is not None else ""
            cost_text = f"₹{cost:,.0f} for two (dataset estimate)" if cost is not None else "Cost estimate unavailable"
            cuisine_text = f"🍽️ {cuisine}" if cuisine else "Cuisine not listed"
            address_text = place.get("address") or "Address not provided by OpenStreetMap"

            st.markdown(f"""
            <div class="result-card">
              <div class="pill">#{i}</div>
              <div class="pill">{place['category']}</div>
              <h3>{place['name']}</h3>
              <div><b>{rating_text}</b>{votes_text}</div>
              <p>{cuisine_text}</p>
              <p>📍 {distance:.1f} km away · {address_text}</p>
              <p>💸 {cost_text}</p>
              <div class="small">Data: {place['source']}</div>
            </div>
            """, unsafe_allow_html=True)

            maps_url = (
                "https://www.openstreetmap.org/"
                f"?mlat={place['lat']}&mlon={place['lon']}#map=18/"
                f"{place['lat']}/{place['lon']}"
            )
            st.markdown(f"[🧭 View {place['name']} on OpenStreetMap]({maps_url})")

            extra = []
            if place.get("website"):
                extra.append(f"[Website]({place['website']})")
            if place.get("phone"):
                extra.append(f"Phone: {place['phone']}")
            if extra:
                st.caption(" · ".join(extra))

    with st.expander("ℹ️ About the information"):
        st.write(
            "Nearby places and their map positions come from OpenStreetMap. "
            "Ratings, votes, cuisines and cost estimates are added only when a sufficiently "
            "similar restaurant can be matched to your local Zomato dataset. "
            "A missing rating or cost means no confident match was found; it does not mean "
            "the place has a poor rating or is free."
        )
        st.write(
            "Dataset information may be old or incomplete. Always confirm opening hours, "
            "prices and business details before visiting."
        )

st.divider()
st.caption("Made with ☕ and curiosity · NearBites India")
