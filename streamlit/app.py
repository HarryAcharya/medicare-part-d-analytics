"""
Medicare Part D Drug Analytics -- Streamlit dashboard.

Live companion to the GitHub analytical project at:
https://github.com/HarryAcharya/medicare-part-d-analytics

Reads pre-computed CSV outputs from docs/sql_outputs/. No database connection
required at runtime -- fully deployable to Streamlit Cloud as-is.

Run locally:
    streamlit run streamlit/app.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "docs" / "sql_outputs"


@st.cache_data
def load(name: str) -> pd.DataFrame:
    """Load a precomputed CSV result from docs/sql_outputs/."""
    df = pd.read_csv(DATA_DIR / name)
    if "year" in df.columns:
        df["year"] = df["year"].astype(int)
    return df


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Medicare Part D Analytics",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("💊 Medicare Part D Drug Analytics")
st.markdown(
    "**A GLP-1 deep-dive across five years of CMS Medicare Part D drug spending.**  \n"
    "Live companion to the "
    "[GitHub project](https://github.com/HarryAcharya/medicare-part-d-analytics)."
)


# ---------------------------------------------------------------------------
# Headline KPIs
# ---------------------------------------------------------------------------
annual = load("06_annual_yoy_growth.csv")
conversion = load("11_glp1_conversion_rate.csv")

spend_2019 = annual.loc[annual["year"] == 2019, "spend_billions"].iloc[0]
spend_2023 = annual.loc[annual["year"] == 2023, "spend_billions"].iloc[0]
growth_total = spend_2023 - spend_2019
glp1_2023 = conversion.loc[conversion["year"] == 2023, "glp1_b"].iloc[0]
glp1_pct = glp1_2023 / spend_2023 * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "2023 Part D gross spend",
    f"${spend_2023:.0f}B",
    f"+{((spend_2023/spend_2019)-1)*100:.0f}% since 2019",
)
col2.metric(
    "5-year growth",
    f"${growth_total:.0f}B",
    "$22B volume + $66B price/mix + $8B interaction",
    delta_color="off",
)
col3.metric(
    "GLP-1 diabetes spend",
    f"${glp1_2023:.1f}B",
    f"{glp1_pct:.1f}% of total Part D",
)
col4.metric(
    "Off-label Ozempic est.",
    "~593K benes",
    "2023 excess vs Trulicity growth",
    delta_color="off",
)

st.markdown("---")


# ---------------------------------------------------------------------------
# Tabs (placeholders -- filled in over next steps)
# ---------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(
    ["📊 Drug Explorer", "🔮 GLP-1 Forecast", "💡 UM Intervention Simulator"]
)

with tab1:
    st.header("📊 Drug Explorer")
    st.markdown(
        "Browse the **top 25 Medicare Part D drugs by 2023 spend**, with 1-year "
        "and 5-year growth metrics. Filter by drug name to find a specific medication."
    )

    top25 = load("07_top25_drugs_growth.csv")

    # Search row
    col_search, col_count = st.columns([3, 1])
    search = col_search.text_input(
        "🔍 Search by brand or generic name",
        placeholder="e.g. Ozempic, Eliquis, semaglutide...",
    )

    if search:
        mask = (
            top25["Brnd_Name"].str.contains(search, case=False, na=False)
            | top25["Gnrc_Name"].str.contains(search, case=False, na=False)
        )
        filtered = top25[mask]
    else:
        filtered = top25

    col_count.metric("Drugs shown", f"{len(filtered)} / {len(top25)}")

    if len(filtered) == 0:
        st.warning(f"No drugs matching '{search}' in the top 25.")
    else:
        display = filtered[[
            "rnk", "Brnd_Name", "Gnrc_Name",
            "spend_2023_b", "spend_2022_b", "yoy_pct",
            "spend_2019_b", "five_yr_pct",
        ]].copy()
        display.columns = [
            "Rank", "Brand", "Generic",
            "Spend 2023 ($B)", "Spend 2022 ($B)", "YoY %",
            "Spend 2019 ($B)", "5-yr %",
        ]

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn(width="small"),
                "Spend 2023 ($B)": st.column_config.NumberColumn(format="$%.2fB"),
                "Spend 2022 ($B)": st.column_config.NumberColumn(format="$%.2fB"),
                "Spend 2019 ($B)": st.column_config.NumberColumn(format="$%.2fB"),
                "YoY %": st.column_config.NumberColumn(format="%.1f%%"),
                "5-yr %": st.column_config.NumberColumn(format="%.1f%%"),
            },
            height=500,
        )

    # GLP-1 family deep-dive section
    st.markdown("---")
    st.subheader("🌡️ GLP-1 Family — 5-Year Trajectory")
    st.markdown(
        "All GLP-1 receptor agonists in Part D 2019–2023, normalized at parent-brand "
        "level. Diabetes-indicated brands (Part D covered) vs obesity-indicated "
        "brands (statutorily excluded by Section 1860D-2(e)(2)(A))."
    )

    glp1 = load("04_glp1_family_normalized.csv")

    glp1_display = glp1.copy()
    glp1_display.columns = [
        "Parent Brand", "Generic", "Indication",
        "2019 ($M)", "2020 ($M)", "2021 ($M)", "2022 ($M)", "2023 ($M)",
    ]

    st.dataframe(
        glp1_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "2019 ($M)": st.column_config.NumberColumn(format="$%.1fM"),
            "2020 ($M)": st.column_config.NumberColumn(format="$%.1fM"),
            "2021 ($M)": st.column_config.NumberColumn(format="$%.1fM"),
            "2022 ($M)": st.column_config.NumberColumn(format="$%.1fM"),
            "2023 ($M)": st.column_config.NumberColumn(format="$%.1fM"),
        },
    )

    st.caption(
        "Note: NaN values are CMS-suppressed (drug-year with <11 beneficiaries) "
        "or rounded down from sub-million spend to $0.0M. Wegovy 2023 = $0.2M "
        "represents $199,774 spent on 47 Medicare beneficiaries despite the drug's "
        "statutory exclusion from Part D coverage — the policy crack quantified."
    )

with tab2:
        st.header("📈 GLP-1 Forecast Tool")
        st.markdown(
            "Project Medicare Part D GLP-1 diabetes spend 2024–2027 under three policy "
            "scenarios. Tune the sliders to test alternative assumptions about market "
            "maturation, IRA negotiation impact, and hypothetical obesity coverage."
        )

        # --- Model constants ---
        BASE_2023 = 22.21          # GLP-1 diabetes spend, $B
        OZEMPIC_SHARE_2027 = 0.50  # Ozempic ~50% of GLP-1 category by 2027

        # --- Sliders ---
        col_a, col_b, col_c = st.columns(3)

        growth_2024 = col_a.slider(
            "🚀 Initial growth rate (2024 vs 2023)",
            min_value=20, max_value=70, value=49, step=1,
            help="% growth in 2024. Default 49% reflects observed 2023→2024 trajectory.",
            format="%d%%",
        )

        decay = col_a.slider(
            "📉 Growth decay (pts/year)",
            min_value=5, max_value=20, value=12, step=1,
            help="How much the growth rate slows each year as the market matures.",
            format="%d pts",
        )

        ira_cut = col_b.slider(
            "⚖️ IRA price cut on Ozempic (2027)",
            min_value=0, max_value=50, value=35, step=1,
            help="% price cut from IRA negotiation, effective 2027. Set to 0 to disable IRA scenario.",
            format="%d%%",
        )

        obesity_2027 = col_c.slider(
            "🩺 Obesity coverage 2027 cost ($B)",
            min_value=0.0, max_value=15.0, value=6.5, step=0.5,
            help="Total $B added by hypothetical Part D obesity coverage by 2027, ramping from 2025.",
            format="$%.1fB",
        )

        # --- Model ---
        years = [2023, 2024, 2025, 2026, 2027]

        def project_status_quo():
            spend = [BASE_2023]
            g = growth_2024 / 100
            for _ in years[1:]:
                spend.append(spend[-1] * (1 + g))
                g = max(0.03, g - decay / 100)
            return spend

        status_quo = project_status_quo()

        # Obesity = status quo + quadratic ramp to obesity_2027 by 2027
        obesity_scenario = [
            status_quo[i] + obesity_2027 * (max(0, (i - 1) / 3) ** 2)
            for i in range(len(years))
        ]

        # IRA = status quo, with category-level cut applied in 2027 only
        ira_scenario = status_quo.copy()
        ira_scenario[-1] *= 1 - (ira_cut / 100) * OZEMPIC_SHARE_2027

        df_fc = pd.DataFrame({
            "Year": years,
            "Status Quo": status_quo,
            "Obesity Coverage": obesity_scenario,
            "IRA Negotiation": ira_scenario,
        })

        # --- Chart ---
        import altair as alt
        df_long = df_fc.melt("Year", var_name="Scenario", value_name="Spend")
        chart = (
            alt.Chart(df_long)
            .mark_line(point=alt.OverlayMarkDef(size=80), strokeWidth=3)
            .encode(
                x=alt.X("Year:O", title="Year"),
                y=alt.Y("Spend:Q", title="GLP-1 Diabetes Spend ($B)"),
                color=alt.Color(
                    "Scenario:N",
                    scale=alt.Scale(
                        domain=["Status Quo", "Obesity Coverage", "IRA Negotiation"],
                        range=["#4C78A8", "#54A24B", "#F58518"],
                    ),
                ),
                tooltip=[
                    "Year",
                    "Scenario",
                    alt.Tooltip("Spend:Q", format="$,.1f", title="Spend ($B)"),
                ],
            )
            .properties(height=420)
        )
        st.altair_chart(chart, use_container_width=True)

        # --- Table ---
        st.dataframe(
            df_fc,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Year": st.column_config.NumberColumn(format="%d"),
                "Status Quo": st.column_config.NumberColumn(format="$%.1fB"),
                "Obesity Coverage": st.column_config.NumberColumn(format="$%.1fB"),
                "IRA Negotiation": st.column_config.NumberColumn(format="$%.1fB"),
            },
        )

        # --- Findings ---
        st.markdown("---")
        st.subheader("Key Findings at Current Settings")

        sq_2027 = status_quo[-1]
        ira_savings = sq_2027 - ira_scenario[-1]
        obesity_cost = obesity_scenario[-1] - sq_2027

        k1, k2, k3 = st.columns(3)
        k1.metric(
            "2027 Status Quo",
            f"${sq_2027:.1f}B",
            f"+${sq_2027 - BASE_2023:.1f}B from 2023",
        )
        k2.metric(
            "2027 IRA Savings",
            f"${ira_savings:.1f}B",
            "vs status quo",
        )
        k3.metric(
            "2027 Obesity Add",
            f"${obesity_cost:.1f}B",
            "vs status quo",
        )

        net = ira_savings - obesity_cost
        direction = "savings" if net >= 0 else "added cost"

        st.info(
            f"💡 **The policy scissors finding**: at current settings, "
            f"IRA Ozempic savings (**\\${ira_savings:.1f}B by 2027**) vs obesity coverage "
            f"cost (**\\${obesity_cost:.1f}B**) yield a **net \\${abs(net):.1f}B {direction}** — "
            "while nearly doubling the GLP-1 patient population."
        )

with tab3:
        st.header("💡 UM Intervention Simulator")
        st.markdown(
            "**Pick a brand-name drug with a genericized alternative**, set a target "
            "Generic Dispensing Rate (GDR), and see projected annual Medicare Part D "
            "savings from utilization management (prior authorization, step therapy, "
            "formulary tier moves)."
        )

        gdr = load("09_brand_vs_generic_gdr.csv")

        st.markdown("### Top 20 GDR Optimization Opportunities (2023)")

        gdr_display = gdr.copy()
        gdr_display.columns = [
            "Molecule", "# Brands", "Total ($M)", "Brand ($M)",
            "Generic ($M)", "GDR %", "Brand $ Share %",
        ]
        st.dataframe(
            gdr_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Total ($M)": st.column_config.NumberColumn(format="$%.0fM"),
                "Brand ($M)": st.column_config.NumberColumn(format="$%.0fM"),
                "Generic ($M)": st.column_config.NumberColumn(format="$%.0fM"),
                "GDR %": st.column_config.NumberColumn(format="%.1f%%"),
                "Brand $ Share %": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )

        st.caption(
            "GDR (Generic Dispensing Rate) = generic claims ÷ total claims. "
            "Industry benchmark target: ≥ 90%. Each percentage point below benchmark "
            "on a high-volume molecule represents recoverable spend."
        )

        st.markdown("---")
        st.markdown("### 🎯 Simulate UM Intervention on a Selected Molecule")

        col_pick, col_sliders = st.columns([1, 2])

        with col_pick:
            molecule = st.selectbox(
                "Molecule",
                options=gdr["Gnrc_Name"].tolist(),
                index=0,
            )

            row = gdr[gdr["Gnrc_Name"] == molecule].iloc[0]
            current_brand_m = float(row["brand_spend_m"])
            current_generic_m = float(row["generic_spend_m"])
            current_gdr = float(row["gdr_pct"])

            st.metric("Current brand spend", f"${current_brand_m:,.0f}M")
            st.metric("Current generic spend", f"${current_generic_m:,.0f}M")
            st.metric("Current GDR", f"{current_gdr:.1f}%")

        with col_sliders:
            min_v = min(99.0, current_gdr)
            default_v = min(99.0, max(90.0, current_gdr + 5.0))

            target_gdr = st.slider(
                "🎯 Target GDR",
                min_value=min_v,
                max_value=99.0,
                value=default_v,
                step=0.5,
                format="%.1f%%",
                help="Industry benchmark is 90%+. Set above current GDR to drive the savings calculation.",
            )

            price_ratio = st.slider(
                "💰 Brand : Generic price ratio per claim",
                min_value=2,
                max_value=30,
                value=10,
                step=1,
                help="Brand drugs typically cost 5-15x more per claim than their generic equivalents.",
            )

            # --- Savings model ---
            # Fraction of brand claims converted to generic when GDR rises from C to T
            if current_gdr < 99.9:
                converted_fraction = (target_gdr - current_gdr) / (100 - current_gdr)
            else:
                converted_fraction = 0.0
            converted_brand_m = current_brand_m * converted_fraction
            # Savings = converted brand spend × (1 - 1/ratio)
            savings_m = converted_brand_m * (1 - 1 / price_ratio)
            old_total = current_brand_m + current_generic_m

            st.markdown("#### 💰 Projected Annual Savings")
            s1, s2, s3 = st.columns(3)
            s1.metric(
                "Savings",
                f"${savings_m:,.0f}M",
                f"{(100 * savings_m / old_total) if old_total > 0 else 0:.1f}% of molecule total",
            )
            s2.metric(
                "GDR lift",
                f"+{target_gdr - current_gdr:.1f} pts",
                f"{current_gdr:.1f}% → {target_gdr:.1f}%",
            )
            s3.metric(
                "Brand $ converted",
                f"${converted_brand_m:,.0f}M",
                f"of ${current_brand_m:,.0f}M brand spend",
            )

        # --- Context-aware insight callout ---
        st.markdown("---")
        mlow = molecule.lower()
        if "lenalidomide" in mlow:
            st.info(
                f"💡 **{molecule} (Revlimid) post-LOE context**: brand-name Revlimid lost "
                "patent protection in late 2022, creating an immediate generic-substitution "
                f"opportunity. At only **{current_gdr:.1f}% GDR**, this is the largest "
                "single-molecule savings opportunity in Part D — but it's also the freshest "
                "LOE in the dataset, so GDR is naturally low. Expect organic uptake to push "
                "GDR materially higher in 2024–2025 even without active UM intervention."
            )
        elif any(k in mlow for k in ["insulin", "glargine", "aspart", "lispro", "detemir"]):
            st.warning(
                f"⚠️ **{molecule} caveat**: insulin molecules carry rebate-locked contracting "
                "between manufacturers (Novo Nordisk, Eli Lilly, Sanofi) and PBMs. The low GDR "
                "is not a clinical limitation — it is a contractual one. The hypothetical "
                "savings shown assume those contracts can be renegotiated, which is non-trivial "
                "in practice and may reduce the addressable opportunity by 50–80%."
            )
        else:
            st.info(
                f"💡 **{molecule}**: pushing GDR from {current_gdr:.1f}% to {target_gdr:.1f}% "
                f"on this single molecule could save Medicare Part D approximately "
                f"**\\${savings_m:,.0f}M per year** via prior authorization, step therapy, "
                "and formulary tier adjustments. Scale this approach across all 20 top "
                "molecules in the table for total opportunity sizing — the project's overall "
                "estimate is **\\$3–5B/year in realistic GDR-optimization savings**."
            )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(
    "Data source: CMS Medicare Part D Spending by Drug, Reporting Year 2025. "
    "Built by [Hari Acharya](https://github.com/HarryAcharya). "
    "Source: [github.com/HarryAcharya/medicare-part-d-analytics]"
    "(https://github.com/HarryAcharya/medicare-part-d-analytics)."
)