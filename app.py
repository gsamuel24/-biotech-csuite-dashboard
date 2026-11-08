
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="Biotech C-Suite Intelligence",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA_FOLDER = Path(__file__).parent

ROLES = [
    "CEO", "CFO", "CMO", "CSO", "CTO", "COO",
    "CBO", "CHRO", "CPO", "CIO", "CLO", "CCO"
]

@st.cache_data
def load_data():
    companies = pd.read_csv(
        DATA_FOLDER / "dashboard_companies.csv",
        dtype={"company_id": str},
        keep_default_na=False
    ).fillna("")

    executives = pd.read_csv(
        DATA_FOLDER / "dashboard_executives.csv",
        dtype={"company_id": str},
        keep_default_na=False
    ).fillna("")

    return companies, executives

companies, executives = load_data()

for role in ROLES:
    if role not in companies.columns:
        companies[role] = ""

companies["has_executives"] = companies[ROLES].ne("").any(axis=1)

# ------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------

def get_options(column, multi=False):
    if column not in companies.columns:
        return []

    values = companies[column].astype(str)

    if multi:
        return sorted({
            part.strip()
            for value in values
            for part in value.split(";")
            if part.strip()
        })

    return sorted({
        value.strip()
        for value in values
        if value.strip()
    })


def apply_selection(data, column, selected, multi=False):
    if not selected:
        return data

    if multi:
        selected_set = set(selected)
        return data[
            data[column].astype(str).apply(
                lambda value: bool(
                    selected_set.intersection(
                        part.strip()
                        for part in value.split(";")
                    )
                )
            )
        ]

    return data[data[column].isin(selected)]


# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

st.title("🧬 Biotech C-Suite Intelligence")

st.caption(
    "Search biotech companies and explore AI-extracted "
    "executive leadership information."
)

m1, m2, m3, m4 = st.columns(4)

m1.metric("Companies", f"{len(companies):,}")
m2.metric("Executive Records", f"{len(executives):,}")
m3.metric(
    "Companies With C-Suite Data",
    f"{companies['has_executives'].sum():,}"
)
m4.metric(
    "Companies Researched",
    f"{(companies['scrape_status'] != 'Not yet researched').sum():,}"
)

st.divider()

# ------------------------------------------------------------
# COMPACT SEARCH BAR
# ------------------------------------------------------------

search_col, exec_col, toggle_col = st.columns([2, 2, 1.5])

with search_col:
    company_search = st.text_input(
        "Search Company",
        placeholder="Enter company name..."
    )

with exec_col:
    executive_search = st.text_input(
        "Search Executive",
        placeholder="Enter executive name..."
    )

with toggle_col:
    st.write("")
    st.write("")
    only_with_executives = st.checkbox(
        "Only companies with C-suite data"
    )

# ------------------------------------------------------------
# COLLAPSIBLE FILTERS
# ------------------------------------------------------------

with st.expander("Advanced Filters", expanded=False):

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        company_type = st.multiselect(
            "Company Type",
            get_options("company_type")
        )

        public_private = st.multiselect(
            "Public / Private",
            get_options("public_private")
        )

    with f2:
        therapeutic_area = st.multiselect(
            "Therapeutic Area",
            get_options("all_therapeutic_areas", multi=True)
        )

        technology = st.multiselect(
            "Technology",
            get_options("all_technologies", multi=True)
        )

    with f3:
        stage = st.multiselect(
            "Development Stage",
            get_options("lates_stage")
        )

        status = st.multiselect(
            "Company Status",
            get_options("status")
        )

    with f4:
        country = st.multiselect(
            "Country",
            get_options("country")
        )

        state = st.multiselect(
            "State / Province",
            get_options("state_province")
        )

# ------------------------------------------------------------
# APPLY FILTERS
# ------------------------------------------------------------

filtered = companies.copy()

if company_search:
    filtered = filtered[
        filtered["company_name"].str.contains(
            company_search,
            case=False,
            regex=False,
            na=False
        )
    ]

if executive_search:
    matching_ids = executives.loc[
        executives["executive_name"].str.contains(
            executive_search,
            case=False,
            regex=False,
            na=False
        ),
        "company_id"
    ].unique()

    filtered = filtered[
        filtered["company_id"].isin(matching_ids)
    ]

if only_with_executives:
    filtered = filtered[filtered["has_executives"]]

filter_settings = [
    ("company_type", company_type, False),
    ("public_private", public_private, False),
    ("all_therapeutic_areas", therapeutic_area, True),
    ("all_technologies", technology, True),
    ("lates_stage", stage, False),
    ("status", status, False),
    ("country", country, False),
    ("state_province", state, False)
]

for column, selected, multi in filter_settings:
    filtered = apply_selection(
        filtered, column, selected, multi
    )

filtered = filtered.sort_values("company_name")

st.markdown(f"**{len(filtered):,} companies found**")

# ------------------------------------------------------------
# MAIN C-SUITE GRID — FULL WIDTH
# ------------------------------------------------------------

st.subheader("C-Suite Leadership Directory")

st.caption(
    "AI-extracted executive records require verification. "
    "Blank fields do not indicate vacant positions. "
    "Scroll horizontally to view additional C-suite roles."
)

display_columns = ["company_name"] + ROLES

st.dataframe(
    filtered[display_columns],
    hide_index=True,
    use_container_width=True,
    height=550,
    column_config={
        "company_name": st.column_config.TextColumn(
            "Company",
            width="large",
            pinned=True
        ),
        **{
            role: st.column_config.TextColumn(
                role,
                width="medium"
            )
            for role in ROLES
        }
    }
)

# ------------------------------------------------------------
# COMPANY DETAILS AND SOURCE VERIFICATION
# ------------------------------------------------------------

st.divider()

with st.expander("Company Details & Executive Sources"):

    if filtered.empty:
        st.info("No companies match your current filters.")

    else:
        company_labels = (
            filtered.set_index("company_id")["company_name"]
            .to_dict()
        )

        selected_id = st.selectbox(
            "Select a Company",
            options=filtered["company_id"].tolist(),
            format_func=lambda cid: company_labels.get(cid, cid)
        )

        company = filtered.loc[
            filtered["company_id"] == selected_id
        ].iloc[0]

        st.markdown(f"### {company['company_name']}")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.write(
                "**Therapeutic Area:**",
                company.get("primary_therapeutic_area", "")
            )

        with c2:
            st.write(
                "**Technology:**",
                company.get("primary_tech", "")
            )

        with c3:
            st.write(
                "**Development Stage:**",
                company.get("lates_stage", "")
            )

        company_executives = executives[
            executives["company_id"] == selected_id
        ]

        if company_executives.empty:
            st.info(
                "No executive records available. "
                f"Scraping status: {company.get('scrape_status', '')}"
            )
        else:
            st.dataframe(
                company_executives[
                    [
                        "executive_name",
                        "executive_title",
                        "executive_function",
                        "verification_status",
                        "source_url"
                    ]
                ],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "source_url": st.column_config.LinkColumn(
                        "Source",
                        display_text="View Source"
                    )
                }
            )

            with st.expander("Extraction Evidence"):
                for _, row in company_executives.iterrows():
                    st.markdown(
                        f"**{row['executive_name']}**"
                    )
                    st.write(row.get("evidence", ""))
                    st.divider()

st.caption(
    "BAIB 620 | Biotech C-Suite Intelligence Prototype | "
    "Executive information is AI-extracted and unverified."
)
