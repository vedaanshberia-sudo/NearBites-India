
import html
import math
import re
import time
from pathlib import Path
from difflib import SequenceMatcher

import pandas as pd
import requests
import streamlit as st

# =========================================================
# NEARBITES INDIA — SETTINGS
# =========================================================

st.set_page_config(
    page_title="NearBites India",
    page_icon="🍓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_FILE = Path(__file__).parent / "data" / "zomato_clean.csv"
USER_AGENT = "NearBitesIndia/2.0 restaurant-discovery-app"

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# =========================================================
# DESIGN — LARGER, CLEARER, MORE COLOURFUL
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --ink: #20372b;
    --muted: #47594d;
    --green: #dff6a7;
    --purple: #f0e3ff;
    --orange: #ffe1cd;
    --paper: #fffdf7;
}

.stApp {
    background: linear-gradient(145deg, #fffaf0 0%, #f2f8e9 55%, #fff0e8 100%);
    color: var(--ink);
    font-family: 'DM Sans', sans-serif;
    font-size: 18px;
}

.block-container {
    max-width: 1180px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

h1, h2, h3, h4 {
    color: var(--ink) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.5px;
}

h1 { font-size: clamp(2.5rem, 5vw, 4rem) !important; }
h2 { font-size: 2rem !important; }
h3 { font-size: 1.45rem !important; }

p, li, label, .stMarkdown, .stText, .stCaption {
    line-height: 1.7;
}

.stMarkdown p {
    font-size: 1.05rem;
}

.stCaption, [data-testid="stCaptionContainer"] {
    color: #47594d !important;
    font-size: 0.96rem !important;
}

.hero {
    background: linear-gradient(120deg, #e1f6a9, #eff8cf);
    padding: clamp(1.5rem, 4vw, 3rem);
    border: 2px solid var(--ink);
    border-radius: 30px;
    box-shadow: 7px 7px 0 var(--ink);
    margin: 0 0 2rem 0;
}

.hero h1 {
    margin: 1rem 0 0.7rem 0;
    line-height: 1.05;
}

.hero p {
    font-size: 1.2rem;
    max-width: 720px;
    margin-bottom: 0;
}

.eyebrow {
    display: inline-block;
    background: #fffdf7;
    border: 1.5px solid var(--ink);
    border-radius: 100px;
    padding: 8px 15px;
    margin: 0 6px 6px 0;
    font-size: 0.9rem;
    font-weight: 800;
}

.section-box {
    background: rgba(255, 253, 247, 0.95);
    border: 1.5px solid #cbd7c7;
    border-radius: 24px;
    padding: 1.3rem;
    margin: 1rem 0;
}

div[data-testid="stForm"] {
    background: #fffdf7;
    border: 2px solid #d4dfca;
    border-radius: 24px;
    padding: 1.5rem;
}

.stTextInput label, .stSelectbox label {
    color: var(--ink) !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
}

.stTextInput input {
    min-height: 3.2rem;
    font-size: 1.08rem !important;
    color: var(--ink) !important;
    background: #ffffff !important;
    border: 1.5px solid #9eafa0 !important;
    border-radius: 13px !important;
}

div[data-baseweb="select"] > div {
    min-height: 3.2rem;
    background: #ffffff !important;
    border: 1.5px solid #9eafa0 !important;
    border-radius: 13px !important;
    font-size: 1.05rem !important;
}

div.stButton > button,
div[data-testid="stFormSubmitButton"] button {
    background: #263d2e !important;
    color: #ffffff !important;
    border: 2px solid #263d2e !important;
    border-radius: 15px !important;
    min-height: 3.4rem;
    font-size: 1.08rem !important;
    font-weight: 800 !important;
    transition: 0.2s ease;
}

div.stButton > button:hover,
div[data-testid="stFormSubmitButton"] button:hover {
    background: #7958c4 !important;
    border-color: #7958c4 !important;
    transform: translateY(-1px);
}

.result-card {
    background: var(--paper);
    border: 1.5px solid #cbd7c7;
    border-radius: 22px;
    padding: 1.35rem;
    margin: 1rem 0 0.4rem 0;
    box-shadow: 0 5px 0 #e0e8d8;
}

.result-card h3 {
    font-size: 1.5rem !important;
    margin: 0.65rem 0 0.6rem 0;
    overflow-wrap: anywhere;
}

.result-card p {
    font-size: 1.04rem;
    margin: 0.45rem 0;
}

.tag {
    display: inline-block;
    background: #f0e3ff;
    color: #39235f;
    border: 1px solid #b7a0d8;
    border-radius: 100px;
    padding: 6px 12px;
    margin: 0 6px 5px 0;
    font-size: 0.9rem;
    font-weight: 800;
}

.rating {
    color: #67410a;
    background: #fff0bd;
    display: inline-block;
    padding: 7px 12px;
    border-radius: 10px;
    font-size: 1.05rem;
    font-weight: 800;
}

.result-meta {
    color: #47594d;
    font-size: 0.96rem;
    line-height: 1.8;
}

div[data-testid="stAlert"] {
    border-radius: 16px;
    font-size: 1rem;
}

hr {
    border-color: #d6dfcf;
    margin: 2rem 0;
}

a {
    font-weight: 700;
}

@media (max-width: 640px) {
    .block-container {
        padding: 1rem 0.8rem 2rem 0.8rem;
    }
    .hero {
        border-radius: 22px;
        box-shadow: 4px 4px 0 var(--ink);
    }
    .result-card {
        padding: 1rem;
    }
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# GENERAL HELPERS
# =========================================================

def clean_text(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return re.sub(r"\s+", " ", str(value)).strip()


def safe(value):
    return html.escape(clean_text(value))


def normalize(value):
    value = clean_text(value).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def number(value):
    try:
        if value is None or pd.isna(value) or value == "":
            return None
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def distance_km(lat1, lon1, lat2, lon2):
    radius = 6371
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )
    return 2 * radius * math.asin(min(1, math.sqrt(a)))


def get_tag(tags, *keys):
    for key in keys:
        value = clean_text(tags.get(key, ""))
        if value:
            return value
    return ""


# =========================================================
# DATASET
# =========================================================

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


# =========================================================
# IMPROVED LOCATION SEARCH
# Try the full address, then city + state, then city.
# =========================================================

def geocode_location(city, state, road=""):
    city = city.strip()
    state = state.strip()
    road = road.strip()

    queries = []

    if road:
        queries.append(", ".join([road, city, state, "India"]))

    queries.append(", ".join([city, state, "India"]))
    queries.append(", ".join([city, "India"]))

    # Remove duplicate attempts.
    queries = list(dict.fromkeys(q for q in queries if q.strip()))
    last_error = None

    for index, query in enumerate(queries):
        if index > 0:
            time.sleep(1)

        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": query,
                    "format": "jsonv2",
                    "limit": 5,
                    "countrycodes": "in",
                    "addressdetails": 1,
                },
                headers={"User-Agent": USER_AGENT},
                timeout=20,
            )
            response.raise_for_status()
            results = response.json()

            if not results:
                continue

            # Prefer a result whose city/town/village matches the input.
            wanted_city = normalize(city)
            best = None

            for result in results:
                address = result.get("address", {})
                possible_names = [
                    address.get("city", ""),
                    address.get("town", ""),
                    address.get("municipality", ""),
                    address.get("village", ""),
                    address.get("county", ""),
                    result.get("name", ""),
                    result.get("display_name", "").split(",")[0],
                ]

                names = [normalize(n) for n in possible_names if n]
                if wanted_city and any(
                    wanted_city == n or wanted_city in n or n in wanted_city
                    for n in names
                    if n
                ):
                    best = result
                    break

            if best is None:
                best = results[0]

            return {
                "lat": float(best["lat"]),
                "lon": float(best["lon"]),
                "display_name": best.get("display_name", query),
                "matched_query": query,
            }

        except (requests.RequestException, ValueError, KeyError) as exc:
            last_error = exc

    if last_error:
        raise RuntimeError(
            "The location service could not complete your search. Please try again."
        ) from last_error

    return None


# =========================================================
# OPENSTREETMAP NEARBY SEARCH
# =========================================================

def find_nearby(lat, lon, radius=2000):
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

                key = (
                    normalize(name),
                    round(place_lat, 4),
                    round(place_lon, 4),
                )
                if key in seen:
                    continue
                seen.add(key)

                amenity = get_tag(tags, "amenity")
                shop = get_tag(tags, "shop")
                category = (shop or amenity or "food place").replace("_", " ").title()

                address_parts = [
                    get_tag(tags, "addr:housenumber"),
                    get_tag(tags, "addr:street"),
                    get_tag(tags, "addr:suburb", "addr:neighbourhood"),
                    get_tag(tags, "addr:city"),
                ]

                places.append({
                    "name": name,
                    "category": category,
                    "lat": place_lat,
                    "lon": place_lon,
                    "distance": distance_km(
                        lat, lon, place_lat, place_lon
                    ),
                    "address": ", ".join(p for p in address_parts if p),
                    "cuisine": get_tag(tags, "cuisine"),
                    "website": get_tag(tags, "website", "contact:website"),
                    "phone": get_tag(tags, "phone", "contact:phone"),
                    "rating": None,
                    "votes": None,
                    "cost": None,
                    "zomato_cuisine": "",
                    "source": "OpenStreetMap",
                })

            return places

        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            time.sleep(1)

    raise RuntimeError(
        "The nearby map service is busy. Wait a little and search again."
    ) from last_error


# =========================================================
# MATCH NEARBY PLACES WITH THE ZOMATO DATASET
# =========================================================

def enrich_with_zomato(places, df, city):
    if df.empty:
        return places

    required = ["latitude", "longitude", "restaurant_name"]
    if not all(column in df.columns for column in required):
        return places

    data = df.copy()
    data["_lat"] = pd.to_numeric(data["latitude"], errors="coerce")
    data["_lon"] = pd.to_numeric(data["longitude"], errors="coerce")
    data = data.dropna(subset=["_lat", "_lon"])

    if "city" in data.columns:
        same_city = data[
            data["city"].apply(normalize) == normalize(city)
        ]
        if not same_city.empty:
            data = same_city

    for place in places:
        nearby = data[
            (data["_lat"] - place["lat"]).abs() < 0.06
        ]
        nearby = nearby[
            (nearby["_lon"] - place["lon"]).abs() < 0.06
        ]

        best_row = None
        best_score = 0
        name = normalize(place["name"])

        for _, row in nearby.iterrows():
            other_name = normalize(row.get("restaurant_name", ""))
            if not other_name:
                continue

            similarity = SequenceMatcher(None, name, other_name).ratio()

            km = distance_km(
                place["lat"],
                place["lon"],
                float(row["_lat"]),
                float(row["_lon"]),
            )

            if km > 3:
                continue

            score = similarity - km * 0.02

            if score > best_score:
                best_score = score
                best_row = row

        if best_row is not None and best_score >= 0.72:
            place["rating"] = number(best_row.get("aggregate_rating"))
            place["votes"] = number(best_row.get("votes"))
            place["cost"] = number(
                best_row.get("average_cost_for_two_inr")
            )
            place["zomato_cuisine"] = clean_text(
                best_row.get("cuisines", "")
            )
            place["source"] = "OpenStreetMap + Zomato dataset"

    return places


# =========================================================
# FILTERING AND SORTING
# =========================================================

def rank_places(places, priority, kind):
    filtered = []

    for place in places:
        category = place["category"].lower()

        is_cafe = "cafe" in category or "coffee" in category
        is_bakery = any(
            word in category
            for word in ["bakery", "pastry", "confectionery", "ice cream"]
        )

        if kind == "Cafés" and not is_cafe:
            continue

        if kind == "Bakeries & desserts" and not is_bakery:
            continue

        filtered.append(place)

    def score(place):
        category = place["category"].lower()

        cafe_bonus = (
            4 if "cafe" in category or "coffee" in category else 0
        )
        bakery_bonus = (
            3 if any(
                word in category
                for word in ["bakery", "pastry", "confectionery", "ice cream"]
            ) else 0
        )
        restaurant_bonus = (
            2 if any(
                word in category
                for word in ["restaurant", "food court"]
            ) else 0
        )

        type_bonus = cafe_bonus + bakery_bonus + restaurant_bonus
        rating = place.get("rating") or 0

        if priority == "Top rated":
            return rating * 1.5 + type_bonus - place["distance"] * 0.1

        if priority == "Closest":
            return type_bonus - place["distance"] * 1.2

        return type_bonus + rating * 0.35 - place["distance"] * 0.15

    return sorted(filtered, key=score, reverse=True)


# =========================================================
# MAIN PAGE
# =========================================================

st.markdown("""
<div class="hero">
    <span class="eyebrow">🇮🇳 YOUR INDIA FOOD GUIDE</span>
    <span class="eyebrow">☕ CAFÉS</span>
    <span class="eyebrow">🍰 SWEET TREATS</span>
    <span class="eyebrow">🍜 LOCAL FAVOURITES</span>
    <h1>Your next happy<br>food place is waiting. 🍓</h1>
    <p>
        Find cosy cafés, bakeries, restaurants and little local discoveries.
        Choose your area, set your distance, and let's find something lovely.
    </p>
</div>
""", unsafe_allow_html=True)

st.header("📍 First, choose your area")
st.write(
    "Enter your city and state below. You can leave the road empty "
    "if you want to search around the city."
)

with st.form("location_form"):
    col1, col2 = st.columns(2)

    with col1:
        city = st.text_input(
            "City or town *",
            placeholder="Example: Guwahati",
            help="Enter the city or town name, not your country.",
        )

        state = st.text_input(
            "State *",
            placeholder="Example: Assam",
            help="Enter the Indian state where your city is located.",
        )

        road = st.text_input(
            "Road or neighbourhood (optional)",
            placeholder="Example: GS Road",
            help="Leave this blank if you are not sure.",
        )

    with col2:
        kind = st.selectbox(
            "What would you like to discover?",
            ["Everything", "Cafés", "Bakeries & desserts"],
        )

        priority = st.selectbox(
            "What matters most?",
            ["Best overall", "Closest", "Top rated"],
        )

        radius_label = st.selectbox(
            "How far should we look?",
            [
                "500 metres",
                "1 km",
                "2 km",
                "3 km",
                "5 km",
                "10 km",
            ],
            index=2,
        )

    submitted = st.form_submit_button(
        "🍓 Find my food spots",
        use_container_width=True,
    )


# =========================================================
# SEARCH
# =========================================================

if submitted:
    if not city.strip() or not state.strip():
        st.error(
            "Please fill in both required fields: City or town and State."
        )
        st.info(
            "Example: City = Guwahati, State = Assam. "
            "The road or neighbourhood is optional."
        )
    else:
        radius_values = {
            "500 metres": 500,
            "1 km": 1000,
            "2 km": 2000,
            "3 km": 3000,
            "5 km": 5000,
            "10 km": 10000,
        }

        radius = radius_values[radius_label]

        # Clear old results so a failed new search cannot look successful.
        st.session_state.pop("near_bites_results", None)
        st.session_state.pop("near_bites_location", None)

        with st.spinner(
            "Finding your location and looking for nearby food places..."
        ):
            try:
                location = geocode_location(city, state, road)

                if not location:
                    st.error(
                        f"We couldn't locate '{city}, {state}, India'."
                    )
                    st.write(
                        "Check the city and state spelling. Try leaving "
                        "the optional road field blank and search again."
                    )
                else:
                    places = find_nearby(
                        location["lat"],
                        location["lon"],
                        radius,
                    )

                    dataset = load_zomato()
                    places = enrich_with_zomato(
                        places, dataset, city
                    )
                    places = rank_places(places, priority, kind)

                    # Apply the exact selected radius.
                    places = [
                        p for p in places
                        if p["distance"] <= radius / 1000
                    ]

                    st.session_state["near_bites_results"] = places
                    st.session_state["near_bites_location"] = location
                    st.session_state["near_bites_search"] = {
                        "city": city,
                        "state": state,
                        "road": road,
                        "kind": kind,
                        "priority": priority,
                        "radius": radius_label,
                    }
                    st.session_state["near_bites_dataset_count"] = len(dataset)

            except (requests.RequestException, RuntimeError) as exc:
                st.error(str(exc))
                st.info(
                    "The public location or map service may be busy. "
                    "Please wait a short time and try again."
                )
            except Exception as exc:
                st.error("Something unexpected happened during the search.")
                st.caption(f"Technical detail: {exc}")


# =========================================================
# RESULTS
# =========================================================

if "near_bites_results" in st.session_state:
    results = st.session_state["near_bites_results"]
    location = st.session_state.get("near_bites_location", {})
    search = st.session_state.get("near_bites_search", {})
    dataset_count = st.session_state.get("near_bites_dataset_count", 0)

    st.divider()
    st.header("✨ Your food-place shortlist")

    if location.get("display_name"):
        st.caption("Area found: " + location["display_name"])

    st.markdown(
        f'<span class="tag">🗺️ Nearby map listings</span>'
        f'<span class="tag">📚 {dataset_count:,} dataset records loaded</span>'
        f'<span class="tag">📏 Within {safe(search.get("radius", ""))}</span>',
        unsafe_allow_html=True,
    )

    if not results:
        st.warning(
            "We couldn't find matching places in this search. "
            "That doesn't necessarily mean there are no restaurants nearby."
        )

        st.markdown("""
        **Try these quick fixes:**

        - Choose a larger distance, such as 3 km or 5 km.
        - Choose **Everything** instead of a specific food category.
        - Leave the road/neighbourhood field blank.
        - Try the city centre or a well-known neighbourhood.
        - Search again later if the public map service is temporarily unavailable.
        """)

    else:
        st.success(f"We found {len(results)} food places for you!")

        for index, place in enumerate(results, start=1):
            rating = place.get("rating")
            votes = place.get("votes")
            cost = place.get("cost")

            cuisine = (
                place.get("zomato_cuisine")
                or place.get("cuisine")
                or "Cuisine not listed"
            )

            if rating is not None and rating > 0:
                rating_html = (
                    f'<span class="rating">⭐ {rating:.1f} / 5</span>'
                )
            else:
                rating_html = (
                    '<span class="rating">⭐ Rating unavailable</span>'
                )

            if votes is not None:
                votes_html = f" · {int(votes):,} votes"
            else:
                votes_html = ""

            if cost is not None and cost > 0:
                cost_text = f"₹{cost:,.0f} for two (dataset estimate)"
            else:
                cost_text = "Cost estimate unavailable"

            address = (
                place.get("address")
                or "A detailed street address is not available"
            )

            st.markdown(f"""
            <div class="result-card">
                <span class="tag">#{index}</span>
                <span class="tag">{safe(place['category'])}</span>
                <h3>{safe(place['name'])}</h3>
                {rating_html}
                <span class="result-meta">{safe(votes_html)}</span>
                <p>🍽️ <b>Cuisine:</b> {safe(cuisine)}</p>
                <p>📍 <b>Distance:</b> {place['distance']:.2f} km</p>
                <p>🛣️ <b>Address:</b> {safe(address)}</p>
                <p>💸 <b>Typical cost:</b> {safe(cost_text)}</p>
                <div class="result-meta">Information source: {safe(place['source'])}</div>
            </div>
            """, unsafe_allow_html=True)

            maps_url = (
                "https://www.openstreetmap.org/"
                f"?mlat={place['lat']}&mlon={place['lon']}"
                f"#map=18/{place['lat']}/{place['lon']}"
            )

            st.markdown(
                f"[🧭 Open {safe(place['name'])} on the map]({maps_url})"
            )

            extra = []
            website = place.get("website", "")
            phone = place.get("phone", "")

            if website:
                extra.append(f"[Visit website]({website})")
            if phone:
                extra.append(f"Phone: {phone}")

            if extra:
                st.caption(" · ".join(extra))

    with st.expander("ℹ️ Where does this information come from?"):
        st.write(
            "OpenStreetMap provides nearby food-place listings and map positions. "
            "The included Zomato dataset may provide ratings, votes, cuisines "
            "and average cost for two when a sufficiently similar nearby record "
            "can be matched."
        )
        st.write(
            "The dataset may be incomplete or outdated. A missing rating does "
            "not mean a restaurant has a poor rating. Prices, opening hours, "
            "and business details should be confirmed before visiting."
        )

        if dataset_count == 0:
            st.warning(
                "The dataset could not be loaded. Check that your file is "
                "named data/zomato_clean.csv in GitHub."
            )

st.divider()

st.markdown("""
<div style="text-align:center; padding: 1rem 0; color:#47594d;">
    <div style="font-size:1.3rem; font-weight:800;">
        Made with ☕ and curiosity.
    </div>
    <div style="font-size:1rem;">
        NearBites India · Find your next little favourite.
    </div>
</div>
""", unsafe_allow_html=True)
