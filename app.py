from pathlib import Path
import re
import html

import pandas as pd
import streamlit as st


# ============================================================
# NEARBITES INDIA — RESTAURANT DISCOVERY APP
# ============================================================

st.set_page_config(
    page_title="NearBites India",
    page_icon="🍓",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent

DATA_CANDIDATES = [
    BASE_DIR / "data" / "swiggy_file.csv.gz",
    BASE_DIR / "swiggy_file.csv.gz",
    BASE_DIR / "data" / "swiggy_file.csv",
    BASE_DIR / "swiggy_file.csv",
]

EXPECTED_COLUMNS = [
    "Restaurant Name",
    "Cuisine",
    "Rating",
    "Number of Ratings",
    "Average Price",
    "Number of Offers",
    "Offer Name",
    "Area",
    "Pure Veg",
    "Location",
]


# ============================================================
# DESIGN
# ============================================================

st.markdown(
    """
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
        background: linear-gradient(
            145deg,
            #fffaf0 0%,
            #f2f8e9 55%,
            #fff0e8 100%
        );
        color: var(--ink);
        font-family: 'DM Sans', sans-serif;
        font-size: 17px;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 1.8rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4 {
        color: var(--ink) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.4px;
    }

    h1 {
        font-size: clamp(2.4rem, 5vw, 3.8rem) !important;
    }

    h2 {
        font-size: 1.9rem !important;
    }

    h3 {
        font-size: 1.35rem !important;
    }

    p, li, label, .stMarkdown, .stText {
        line-height: 1.6;
    }

    [data-testid="stCaptionContainer"] {
        color: #47594d !important;
        font-size: 0.94rem !important;
    }

    .hero {
        background: linear-gradient(
            120deg,
            #e1f6a9 0%,
            #fff0cb 52%,
            #f0e3ff 100%
        );
        padding: clamp(1.4rem, 4vw, 2.7rem);
        border: 2px solid var(--ink);
        border-radius: 28px;
        box-shadow: 7px 7px 0 var(--ink);
        margin-bottom: 1.8rem;
    }

    .hero h1 {
        margin: 0.7rem 0 0.6rem 0;
        line-height: 1.05;
    }

    .hero p {
        font-size: 1.12rem;
        max-width: 760px;
        margin-bottom: 0;
        color: #34483a;
    }

    .eyebrow {
        display: inline-block;
        background: #fffdf7;
        border: 1.5px solid var(--ink);
        border-radius: 100px;
        padding: 7px 12px;
        margin: 0 5px 5px 0;
        font-size: 0.83rem;
        font-weight: 800;
    }

    .restaurant-name {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.35rem;
        font-weight: 700;
        line-height: 1.25;
        color: #20372b;
        overflow-wrap: anywhere;
    }

    .restaurant-area {
        color: #47594d;
        margin-top: 0.3rem;
        margin-bottom: 0.6rem;
    }

    div[data-testid="stForm"] {
        background: #fffdf7;
        border: 1.5px solid #d4dfca;
        border-radius: 22px;
        padding: 1.25rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 20px !important;
        border-color: #d4dfca !important;
    }

    div.stButton > button {
        background: #263d2e !important;
        color: #ffffff !important;
        border: 2px solid #263d2e !important;
        border-radius: 13px !important;
        min-height: 2.8rem;
        font-weight: 800 !important;
    }

    div.stButton > button:hover {
        background: #7958c4 !important;
        border-color: #7958c4 !important;
    }

    section[data-testid="stSidebar"] {
        background: #f4edff;
    }

    @media (max-width: 640px) {
        .block-container {
            padding: 1rem 0.8rem 2rem 0.8rem;
        }

        .hero {
            border-radius: 21px;
            box-shadow: 4px 4px 0 var(--ink);
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return re.sub(r"\s+", " ", str(value)).strip()


def parse_first_number(series):
    cleaned = series.astype(str).str.replace(",", "", regex=False)
    extracted = cleaned.str.extract(
        r"(\d+(?:\.\d+)?)",
        expand=False,
    )
    return pd.to_numeric(extracted, errors="coerce")


@st.cache_data(show_spinner="Loading restaurant data...")
def load_restaurants(path_string):
    frame = pd.read_csv(path_string, low_memory=False)

    frame.columns = [
        str(column).strip()
        for column in frame.columns
    ]

    missing = [
        column
        for column in EXPECTED_COLUMNS
        if column not in frame.columns
    ]

    if missing:
        raise ValueError(
            "The dataset is missing these columns: "
            + ", ".join(missing)
        )

    for column in EXPECTED_COLUMNS:
        frame[column] = (
            frame[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    frame = frame[
        frame["Restaurant Name"].ne("")
        & frame["Location"].ne("")
    ].copy()

    frame["_rating"] = pd.to_numeric(
        frame["Rating"].replace(
            {
                "NEW": "",
                "New": "",
                "-": "",
                "": "",
                "N/A": "",
            }
        ),
        errors="coerce",
    )

    frame["_price"] = parse_first_number(
        frame["Average Price"]
    )

    frame["_ratings_count"] = parse_first_number(
        frame["Number of Ratings"]
    )

    frame["_offer_count"] = pd.to_numeric(
        frame["Number of Offers"],
        errors="coerce",
    ).fillna(0)

    frame["_search"] = (
        frame["Restaurant Name"]
        + " "
        + frame["Cuisine"]
        + " "
        + frame["Area"]
        + " "
        + frame["Location"]
    ).str.casefold()

    frame["_is_veg"] = frame["Pure Veg"].str.casefold().isin(
        [
            "yes",
            "true",
            "1",
            "pure veg",
            "vegetarian",
        ]
    )

    frame["_has_offer"] = (
        frame["_offer_count"].gt(0)
        | frame["Offer Name"].ne("")
    )

    return frame


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <span class="eyebrow">🇮🇳 MADE FOR FOOD EXPLORERS</span>
        <span class="eyebrow">☕ CAFÉS</span>
        <span class="eyebrow">🍰 SWEET TREATS</span>
        <span class="eyebrow">🍜 LOCAL FAVOURITES</span>

        <h1>Your next happy food place is waiting. 🍓</h1>

        <p>
            Find restaurants by city and area, explore cuisines and ratings,
            compare listed prices, and discover offers recorded in the dataset.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Dataset-based discovery • No GPS needed • No made-up distances • "
    "Saved ratings, prices and offers may be outdated"
)


# ============================================================
# LOAD DATASET
# ============================================================

data_path = next(
    (
        path
        for path in DATA_CANDIDATES
        if path.exists()
    ),
    None,
)

if data_path is None:
    st.error(
        "Dataset not found. Please upload the file to "
        "data/swiggy_file.csv.gz in your GitHub repository."
    )

    st.info(
        "You can also upload the uncompressed file as "
        "data/swiggy_file.csv."
    )

    st.stop()


try:
    restaurants = load_restaurants(str(data_path))

except Exception as exc:
    st.error(f"Could not load the restaurant dataset: {exc}")
    st.stop()


if restaurants.empty:
    st.error(
        "The dataset loaded, but it contains no usable restaurant records."
    )
    st.stop()


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.markdown("## 🧁 Find your food")
st.sidebar.caption("Choose a city, then narrow your shortlist.")

cities = sorted(
    restaurants["Location"]
    .loc[restaurants["Location"].ne("")]
    .unique()
    .tolist(),
    key=str.casefold,
)

default_city_index = next(
    (
        index
        for index, city_name in enumerate(cities)
        if city_name.casefold() == "guwahati"
    ),
    0,
)

selected_city = st.sidebar.selectbox(
    "📍 City",
    options=cities,
    index=default_city_index,
)

city_data = restaurants[
    restaurants["Location"].str.casefold()
    == selected_city.casefold()
].copy()


area_options = sorted(
    city_data["Area"]
    .loc[city_data["Area"].ne("")]
    .unique()
    .tolist(),
    key=str.casefold,
)

selected_areas = st.sidebar.multiselect(
    "🗺️ Area / locality",
    options=area_options,
    default=[],
    help="Leave empty to include all areas listed for this city.",
)


search_term = st.sidebar.text_input(
    "🔎 Restaurant or keyword",
    placeholder="Try pizza, café, biryani...",
)


cuisine_set = set()

for cuisine_string in city_data["Cuisine"]:
    for cuisine_name in cuisine_string.split(","):
        cuisine_name = cuisine_name.strip()

        if cuisine_name:
            cuisine_set.add(cuisine_name)


cuisine_options = sorted(
    cuisine_set,
    key=str.casefold,
)

selected_cuisines = st.sidebar.multiselect(
    "🍕 Cuisine",
    options=cuisine_options,
    default=[],
)


rating_values = city_data["_rating"].dropna()

if not rating_values.empty:
    min_rating = st.sidebar.slider(
        "⭐ Minimum rating",
        min_value=0.0,
        max_value=5.0,
        value=0.0,
        step=0.5,
        help=(
            "Listings with NEW or missing ratings are excluded "
            "when you choose a rating above zero."
        ),
    )
else:
    min_rating = 0.0
    st.sidebar.caption(
        "No numeric ratings are available for this city."
    )


price_values = city_data["_price"].dropna()

if not price_values.empty:
    highest_price = max(
        100,
        int(price_values.max()),
    )

    price_step = 50 if highest_price >= 50 else 1

    max_price = st.sidebar.slider(
        "💸 Maximum listed average price for two (₹)",
        min_value=0,
        max_value=highest_price,
        value=highest_price,
        step=price_step,
        help=(
            "Uses the first number in the dataset's "
            "Average Price field."
        ),
    )
else:
    highest_price = None
    max_price = None

    st.sidebar.caption(
        "No numeric prices are available for this city."
    )


veg_only = st.sidebar.checkbox(
    "🌿 Pure vegetarian only",
    value=False,
)

offers_only = st.sidebar.checkbox(
    "🎁 Only listings with offers",
    value=False,
)


sort_choice = st.sidebar.selectbox(
    "Sort results",
    [
        "Highest rated",
        "Most ratings",
        "Lowest listed price",
        "Restaurant name A–Z",
    ],
)


st.sidebar.divider()

st.sidebar.markdown(
    """
    **A little data note 💛**

    This app uses a saved dataset, not a live Swiggy feed.
    Restaurant status, ratings, prices and offers may have changed.
    The dataset has no latitude or longitude, so NearBites does not
    calculate distances.
    """
)


# ============================================================
# APPLY FILTERS
# ============================================================

results = city_data.copy()


if selected_areas:
    results = results[
        results["Area"].isin(selected_areas)
    ]


if search_term.strip():
    results = results[
        results["_search"].str.contains(
            re.escape(search_term.strip().casefold()),
            regex=True,
            na=False,
        )
    ]


if selected_cuisines:
    cuisine_pattern = "|".join(
        re.escape(item)
        for item in selected_cuisines
    )

    results = results[
        results["Cuisine"].str.contains(
            cuisine_pattern,
            case=False,
            regex=True,
            na=False,
        )
    ]


if min_rating > 0:
    results = results[
        results["_rating"].ge(min_rating)
    ]


if max_price is not None:
    if max_price < highest_price:
        results = results[
            results["_price"].notna()
            & results["_price"].le(max_price)
        ]
    else:
        results = results[
            results["_price"].isna()
            | results["_price"].le(max_price)
        ]


if veg_only:
    results = results[
        results["_is_veg"]
    ]


if offers_only:
    results = results[
        results["_has_offer"]
    ]


# ============================================================
# SORT RESULTS
# ============================================================

if sort_choice == "Highest rated":
    results = results.sort_values(
        [
            "_rating",
            "_ratings_count",
            "Restaurant Name",
        ],
        ascending=[False, False, True],
        na_position="last",
    )

elif sort_choice == "Most ratings":
    results = results.sort_values(
        [
            "_ratings_count",
            "_rating",
        ],
        ascending=[False, False],
        na_position="last",
    )

elif sort_choice == "Lowest listed price":
    results = results.sort_values(
        "_price",
        ascending=True,
        na_position="last",
    )

else:
    results = results.sort_values(
        "Restaurant Name",
        key=lambda column: column.str.casefold(),
    )


# ============================================================
# RESULTS SUMMARY
# ============================================================

st.header("🥑 Your food shortlist")

metric_a, metric_b, metric_c = st.columns(3)

metric_a.metric(
    "Listings found",
    f"{len(results):,}",
)

metric_b.metric(
    "Selected city",
    selected_city,
)

metric_c.metric(
    "Areas in this city",
    f"{len(area_options):,}",
)


if selected_areas:
    st.caption(
        "Showing areas: " + ", ".join(selected_areas)
    )
else:
    st.caption(
        f"Showing all areas listed for {selected_city}."
    )


st.divider()


if results.empty:
    st.warning(
        "No restaurants match these filters. Try clearing the area "
        "or cuisine filters, lowering the minimum rating, or "
        "increasing the price limit."
    )
    st.stop()


# ============================================================
# PAGINATION
# ============================================================

page_size = 12

total_pages = max(
    1,
    (len(results) + page_size - 1) // page_size,
)

if "near_bites_page" not in st.session_state:
    st.session_state.near_bites_page = 1

st.session_state.near_bites_page = min(
    max(1, st.session_state.near_bites_page),
    total_pages,
)


previous_col, page_col, next_col = st.columns([1, 2, 1])


with previous_col:
    if st.button(
        "← Previous",
        disabled=st.session_state.near_bites_page <= 1,
        use_container_width=True,
    ):
        st.session_state.near_bites_page -= 1
        st.rerun()


with page_col:
    st.markdown(
        f"<p style='text-align:center;padding-top:8px;'>"
        f"Page {st.session_state.near_bites_page} "
        f"of {total_pages}</p>",
        unsafe_allow_html=True,
    )


with next_col:
    if st.button(
        "Next →",
        disabled=st.session_state.near_bites_page >= total_pages,
        use_container_width=True,
    ):
        st.session_state.near_bites_page += 1
        st.rerun()


start = (
    st.session_state.near_bites_page - 1
) * page_size

page_results = results.iloc[
    start:start + page_size
]


# ============================================================
# RESTAURANT CARDS
# ============================================================

for _, restaurant in page_results.iterrows():

    name = clean_text(
        restaurant["Restaurant Name"]
    )

    area = (
        clean_text(restaurant["Area"])
        or "Area not listed"
    )

    cuisine = (
        clean_text(restaurant["Cuisine"])
        or "Cuisine not listed"
    )

    rating = (
        clean_text(restaurant["Rating"])
        or "Not listed"
    )

    ratings_count = (
        clean_text(restaurant["Number of Ratings"])
        or "Not listed"
    )

    price = (
        clean_text(restaurant["Average Price"])
        or "Not listed"
    )

    veg = clean_text(
        restaurant["Pure Veg"]
    )

    offer_name = clean_text(
        restaurant["Offer Name"]
    )

    offer_count = int(
        restaurant["_offer_count"]
    )


    with st.container(border=True):

        left, right = st.columns([3, 1])


        with left:

            st.markdown(
                f"<div class='restaurant-name'>"
                f"{html.escape(name)}</div>",
                unsafe_allow_html=True,
            )

            st.markdown(
                f"<div class='restaurant-area'>"
                f"📍 {html.escape(area)} · "
                f"{html.escape(selected_city)}</div>",
                unsafe_allow_html=True,
            )

            st.write(
                f"🍽️ **Cuisine:** {cuisine}"
            )

            st.write(
                f"💸 **Average price:** {price}"
            )


            if veg.casefold() in [
                "yes",
                "true",
                "1",
                "pure veg",
                "vegetarian",
            ]:
                st.write(
                    "🌿 **Pure vegetarian:** Yes"
                )

            elif veg.casefold() in [
                "no",
                "false",
                "0",
            ]:
                st.write(
                    "🌿 **Pure vegetarian:** No"
                )

            else:
                st.write(
                    "🌿 **Pure vegetarian:** Not listed"
                )


        with right:

            if rating.casefold() not in [
                "",
                "new",
                "-",
                "n/a",
                "nan",
            ]:
                st.metric(
                    "⭐ Rating",
                    rating,
                )
            else:
                st.metric(
                    "⭐ Rating",
                    "NEW / N.A.",
                )

            st.caption(
                f"🗳️ {ratings_count}"
            )


            if offer_count > 0 or offer_name:
                display_count = (
                    offer_count
                    if offer_count > 0
                    else "Listed"
                )

                st.success(
                    f"🎁 {display_count} offer(s)"
                )

            else:
                st.caption(
                    "No offer listed"
                )


        if offer_name:

            with st.expander(
                "🎉 Offer details in the dataset"
            ):

                st.text(offer_name)

                st.caption(
                    "This offer text comes from the saved dataset. "
                    "It may be expired or subject to conditions; "
                    "confirm before ordering."
                )


        st.caption(
            "Source: uploaded Swiggy dataset • Not live-verified"
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center;padding:0.7rem 0;color:#47594d;">
        <div style="font-size:1.25rem;font-weight:800;">
            Made with ☕ and curiosity.
        </div>
        <div>
            NearBites India · Find your next little favourite. 🍓
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
