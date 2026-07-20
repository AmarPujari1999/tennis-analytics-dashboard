import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- Configurations ---
# Set the directory path where your downloaded CSV files are saved
BASE_DIR = os.path.dirname(__file__) if '__file__' in locals() else os.getcwd()

@st.cache_data
def load_csv_data():
    """
    Loads necessary data from the local CSV files exported from MySQL.
    Automatically normalizes column names to lowercase to prevent visualization issues.
    """
    # 1. Competitor Rankings Details
    rankings_path = os.path.join(BASE_DIR, "competitor_ranking_details.csv")
    if os.path.exists(rankings_path):
        rankings = pd.read_csv(rankings_path)
        rankings.columns = rankings.columns.str.strip().str.lower().str.replace(' ', '_')
    else:
        st.error(f"Could not find Rankings file at: {rankings_path}")
        rankings = pd.DataFrame()

    # 2. Competition Details
    comp_path = os.path.join(BASE_DIR, "competition_details.csv")
    if os.path.exists(comp_path):
        competitions = pd.read_csv(comp_path)
        competitions.columns = competitions.columns.str.strip().str.lower().str.replace(' ', '_')
    else:
        st.error(f"Could not find Competitions file at: {comp_path}")
        competitions = pd.DataFrame()

    # 3. Venue Details
    venue_path = os.path.join(BASE_DIR, "venue_details.csv")
    if os.path.exists(venue_path):
        venues = pd.read_csv(venue_path)
        venues.columns = venues.columns.str.strip().str.lower().str.replace(' ', '_')
    else:
        st.error(f"Could not find Venues file at: {venue_path}")
        venues = pd.DataFrame()

    return rankings, competitions, venues

# Initialize Page Config
st.set_page_config(page_title="Tennis Game Analytics", layout="wide")
st.title("🎾 Tennis Game Analytics Dashboard")

# Fetch Data from Local CSV Files
rankings, competitions, venues = load_csv_data()

# Early exit safeguard if files are missing or empty
if rankings.empty or competitions.empty or venues.empty:
    st.warning("Please verify that your CSV files exist in the designated directory and contain data.")
    st.stop()

# ==================== SIDEBAR FILTERS (GLOBAL INTERACTIVITY) ====================
st.sidebar.header("🎯 Global Dashboard Filters")
st.sidebar.write("Filter the rankings dataset dynamically across views.")

# 1. Points Range Filter
if 'points' in rankings.columns:
    min_pts_val = int(rankings['points'].min()) if not pd.isna(rankings['points'].min()) else 0
    max_pts_val = int(rankings['points'].max()) if not pd.isna(rankings['points'].max()) else 10000
    pts_range = st.sidebar.slider(
        "Select Ranking Points Range",
        min_value=min_pts_val,
        max_value=max_pts_val,
        value=(min_pts_val, max_pts_val),
        step=50
    )
else:
    pts_range = (0, 10000)

# 2. Country Multi-select Filter
if 'country' in rankings.columns:
    available_countries = sorted(rankings['country'].dropna().unique().tolist())
    selected_countries = st.sidebar.multiselect(
        "Select Countries / Nations",
        options=available_countries,
        default=[]
    )
else:
    selected_countries = []

# Apply Sidebar Filters globally to the core rankings dataframe copy
rankings_filtered = rankings.copy()
if 'points' in rankings_filtered.columns:
    rankings_filtered = rankings_filtered[
        (rankings_filtered['points'] >= pts_range[0]) & 
        (rankings_filtered['points'] <= pts_range[1])
    ]
if selected_countries and 'country' in rankings_filtered.columns:
    rankings_filtered = rankings_filtered[rankings_filtered['country'].isin(selected_countries)]


# --- Application Tabs Layout ---
tab_home, tab_comp, tab_rank, tab_country, tab_venue = st.tabs([
    "🏠 Homepage", "🏆 Competitions", "👤 Competitor Search", "🌍 Country Analysis", "📍 Venues"
])

# ==================== HOMEPAGE ====================
with tab_home:
    st.header("Executive Tournament Summary")
    
    # KPI Metric Cards Block
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Players Tracked", f"{len(rankings_filtered):,}")
    
    avg_pts = rankings_filtered['points'].mean() if 'points' in rankings_filtered.columns else 0
    m2.metric("Average Points", f"{int(avg_pts):,}")
    
    top_country = rankings_filtered['country'].value_counts().idxmax() if 'country' in rankings_filtered.columns and not rankings_filtered['country'].empty else "N/A"
    m3.metric("Top Performing Country", top_country)
    
    max_pts = rankings_filtered['points'].max() if 'points' in rankings_filtered.columns else 0
    m4.metric("Highest Individual Score", f"{max_pts:,}")
    
    st.divider()
    
    # Layout Adjustment: Giving the Leaderboard more horizontal breathing room (ratio 3:2)
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.subheader("🏆 The Elite Top 10 (By Points)")
        if 'rank' in rankings_filtered.columns and 'points' in rankings_filtered.columns:
            # Get absolute top 10 based on rank inside the active selection
            top_10 = rankings_filtered.sort_values(by='rank').head(10)
            
            if not top_10.empty:
                # Structure rank strings explicitly to present clean "Rank: X" markings inside the bars
                top_10['rank_label'] = top_10['rank'].apply(lambda x: f"Rank: {int(x)}" if not pd.isna(x) else "")
                
                # Setup structured hover display configs
                hover_data_dict = {
                    'competitor_name': True,
                    'points': ':,',
                    'rank': True,
                    'rank_label': False
                }
                if 'country' in top_10.columns:
                    hover_data_dict['country'] = True

                fig_leader = px.bar(
                    top_10, 
                    x='competitor_name', 
                    y='points', 
                    color='points',
                    text='rank_label', 
                    title="Top 10 Leaderboard Overview", 
                    color_continuous_scale='Portland',
                    hover_data=hover_data_dict
                )
                
                fig_leader.update_traces(
                    textposition='inside',
                    insidetextanchor='middle',
                    textfont=dict(size=13, color='white')
                )
                
                fig_leader.update_layout(
                    xaxis_title="Player Name",
                    yaxis_title="Ranking Points",
                    coloraxis_colorbar=dict(title="Points"),
                    margin=dict(t=40, b=40, l=40, r=20)
                )
                st.plotly_chart(fig_leader, use_container_width=True)
            else:
                st.info("No leaderboard data match current filters.")
                
    with col_right:
        st.subheader("🌍 Competitors per Country (Top 5)")
        if 'country' in rankings_filtered.columns:
            country_counts = rankings_filtered['country'].value_counts().head(5).reset_index()
            country_counts.columns = ['Country', 'Total Players']
            
            if not country_counts.empty:
                fig_pie = px.pie(
                    country_counts, 
                    names='Country', 
                    values='Total Players', 
                    hole=0.4, 
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                # Ensure legend doesn't clutter or clip on viewport switches
                fig_pie.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                    margin=dict(t=40, b=40, l=20, r=20)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No country distribution data match current filters.")
    
    st.divider()
    st.subheader("📊 Points Distribution Across All Players")
    if 'points' in rankings_filtered.columns:
        fig_dist = px.histogram(
            rankings_filtered, 
            x='points', 
            nbins=30, 
            title="Statistical Spread of Ranking Field",
            color_discrete_sequence=['#636EFA'], 
            marginal="box"
        )
        fig_dist.update_layout(
            xaxis_title="Ranking Points",
            yaxis_title="Player Count"
        )
        st.plotly_chart(fig_dist, use_container_width=True)
        
        # Recruiter Contextual Insight Caption
        st.markdown(
            "💡 **Data Analyst Insight:** *The distribution displays a heavy right-skew pattern. "
            "This highlights that less than 5% of elite professional competitors control the vast, high-tier "
            "majority of ranking scores across the league field, while the rest of the bulk player population operates underneath the 1,000 points margin.*"
        )

# ==================== COMPETITIONS ====================
with tab_comp:
    st.header("Tournament Structure & Hierarchy")
    
    opts_cat = sorted(competitions['category_name'].dropna().unique().tolist()) if 'category_name' in competitions.columns else []
    opts_gen = sorted(competitions['gender'].dropna().unique().tolist()) if 'gender' in competitions.columns else []
    opts_typ = sorted(competitions['type'].dropna().unique().tolist()) if 'type' in competitions.columns else []

    s1, s2, s3 = st.columns(3)
    with s1:
        selected_categories = st.multiselect("Category", options=opts_cat, default=opts_cat)
    with s2:
        selected_gender = st.multiselect("Gender", options=opts_gen, default=opts_gen)
    with s3:
        selected_type = st.multiselect("Type", options=opts_typ, default=opts_typ)
    
    comp_filtered = competitions.copy()
    if 'category_name' in comp_filtered.columns:
        comp_filtered = comp_filtered[comp_filtered['category_name'].isin(selected_categories)]
    if 'gender' in comp_filtered.columns:
        comp_filtered = comp_filtered[comp_filtered['gender'].isin(selected_gender)]
    if 'type' in comp_filtered.columns:
        comp_filtered = comp_filtered[comp_filtered['type'].isin(selected_type)]
    
    c1, c2 = st.columns(2)
    with c1:
        if 'category_name' in comp_filtered.columns:
            cat_counts = comp_filtered['category_name'].value_counts().reset_index()
            cat_counts.columns = ['Category', 'Event Count']
            fig_cat = px.bar(cat_counts, x='Event Count', y='Category', orientation='h', title="Volume by Category", color='Event Count')
            st.plotly_chart(fig_cat, use_container_width=True)
    with c2:
        if all(col in comp_filtered.columns for col in ['category_name', 'type']):
            fig_sun = px.sunburst(comp_filtered, path=['category_name', 'type'], title="Hierarchy: Category & Type")
            st.plotly_chart(fig_sun, use_container_width=True)
    
    st.divider()
    st.subheader("🏰 Competition Hierarchy")
    h_col1, h_col2 = st.columns(2)
    
    p_id = 'parent_id' if 'parent_id' in comp_filtered.columns else None
    
    with h_col1:
        if p_id:
            top_level = comp_filtered[comp_filtered[p_id].isna() | (comp_filtered[p_id] == '') | (comp_filtered[p_id].astype(str) == 'nan')]
        else:
            top_level = comp_filtered
        st.info(f"Found **{len(top_level)}** Top-Level Competitions.")
        st.dataframe(top_level[[c for c in ['competition_name', 'category_name', 'type'] if c in top_level.columns]], use_container_width=True, hide_index=True)
    with h_col2:
        if p_id:
            sub_level = comp_filtered[comp_filtered[p_id].notna() & (comp_filtered[p_id] != '') & (comp_filtered[p_id].astype(str) != 'nan')]
            st.warning(f"Found **{len(sub_level)}** Sub-Competitions.")
            st.dataframe(sub_level[[c for c in ['competition_name', 'category_name', 'parent_id'] if c in sub_level.columns]], use_container_width=True, hide_index=True)
        else:
            st.warning("Parent ID field missing in configuration; mapping skipped.")

    st.divider()
    st.subheader("🔍 Search All Tournament Details")
    search_comp = st.text_input("Filter by Name")
    comp_final = comp_filtered.copy()
    if search_comp and 'competition_name' in comp_final.columns:
        comp_final = comp_final[comp_final['competition_name'].str.contains(search_comp, case=False, na=False)]
    st.dataframe(comp_final[[c for c in ['competition_name', 'type', 'gender', 'category_name'] if c in comp_final.columns]], use_container_width=True, hide_index=True)

# ==================== COMPETITOR SEARCH ====================
with tab_rank:
    st.header("👤 Competitor Scouting & Performance Profile")
    r1_col1, r1_col2, r1_col3 = st.columns([2, 2, 1])
    with r1_col1:
        search_name = st.text_input("Search Competitor Name", placeholder="e.g. Zeballos")
    with r1_col2:
        max_rank_val = int(rankings_filtered['rank'].max()) if 'rank' in rankings_filtered.columns and not pd.isna(rankings_filtered['rank'].max()) else 100
        rank_range = st.slider("Filter by Rank Range", 1, max(max_rank_val, 100), (1, min(max_rank_val, 50)))
    with r1_col3:
        show_stable = st.checkbox("Stable Ranks Only")

    rankings_subset = rankings_filtered.copy()
    if show_stable and 'movement' in rankings_subset.columns:
        rankings_subset = rankings_subset[rankings_subset['movement'] == 0]
        
    if 'rank' in rankings_subset.columns:
        filtered_rankings = rankings_subset[(rankings_subset['rank'] >= rank_range[0]) & (rankings_subset['rank'] <= rank_range[1])]
    else:
        filtered_rankings = rankings_subset

    if search_name and 'competitor_name' in rankings_filtered.columns:
        profile = rankings_filtered[rankings_filtered['competitor_name'].str.contains(search_name, case=False, na=False)]
        if not profile.empty:
            st.divider()
            p = profile.iloc[0]
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Current World Rank", f"#{p.get('rank', 'N/A')}")
            p2.metric("Weekly Points", f"{p.get('points', 0):,}")
            
            move = p.get('movement', 0)
            move_status = "Stable" if move == 0 else ("Up" if move > 0 else "Down")
            p3.metric("Movement Status", move_status, delta=int(move) if not pd.isna(move) else None)
            
            if 'country' in rankings_filtered.columns and 'points' in rankings_filtered.columns:
                nation_power = rankings_filtered[rankings_filtered['country'] == p['country']]['points'].sum()
                p4.metric(f"Nation Power ({p['country']})", f"{nation_power:,}")
            st.divider()

    st.subheader("📈 Movement & Efficiency Analytics")
    v_col1, v_col2 = st.columns(2)
    with v_col1:
        if 'rank' in filtered_rankings.columns and 'movement' in filtered_rankings.columns:
            fig_move_trend = px.area(filtered_rankings.sort_values('rank'), x='rank', y='movement', 
                                     title="Rank Volatility Trend",
                                     color_discrete_sequence=['#FFA15A'])
            fig_move_trend.update_layout(xaxis_title="Rank Position", yaxis_title="Rank Shift / Movement")
            st.plotly_chart(fig_move_trend, use_container_width=True)
    with v_col2:
        if all(col in filtered_rankings.columns for col in ['competitions_played', 'points', 'movement']):
            fig_scatter_eff = px.scatter(filtered_rankings, x='competitions_played', y='points', 
                                         size='points', color='movement', hover_name='competitor_name',
                                         title="Points vs. Competitions Played Efficiency", color_continuous_scale='RdYlGn')
            fig_scatter_eff.update_layout(xaxis_title="Competitions Played Count", yaxis_title="Total Points Earned")
            st.plotly_chart(fig_scatter_eff, use_container_width=True)

    st.divider()
    st.subheader("🌍 National Competitive Presence")
    c_p1, c_p2 = st.columns([1, 2])
    with c_p1:
        if 'country' in filtered_rankings.columns:
            country_count_df = filtered_rankings['country'].value_counts().reset_index()
            country_count_df.columns = ['Country', 'Player Count']
            st.dataframe(country_count_df, height=350, hide_index=True)
    with c_p2:
        if 'country' in filtered_rankings.columns and 'points' in filtered_rankings.columns:
            country_points_df = filtered_rankings.groupby('country')['points'].sum().sort_values(ascending=False).reset_index()
            fig_country_pts = px.bar(country_points_df.head(10), x='points', y='country', orientation='h', title="Top 10 Aggregate Nation Scores", color='points')
            fig_country_pts.update_layout(xaxis_title="Total Points Accumulation", yaxis_title="Country")
            st.plotly_chart(fig_country_pts, use_container_width=True)

    st.divider()
    st.subheader("📋 Master Ranking List")
    display_rank = rankings_filtered[rankings_filtered['competitor_name'].str.contains(search_name, case=False, na=False)] if (search_name and 'competitor_name' in rankings_filtered.columns) else filtered_rankings
    st.dataframe(display_rank, use_container_width=True, hide_index=True)

# ==================== COUNTRY ANALYSIS ====================
with tab_country:
    st.header("🌍 Performance by Nation")
    if 'country' in rankings_filtered.columns and 'competitor_name' in rankings_filtered.columns and 'points' in rankings_filtered.columns:
        country_analysis = rankings_filtered.groupby('country').agg({'competitor_name':'count', 'points':'mean'}).reset_index()
        country_analysis.columns = ['Country', 'Player Count', 'Avg Points']
        
        st.subheader("Country Strength: Player Pool vs. Average Performance")
        fig_nation = px.scatter(country_analysis, x='Player Count', y='Avg Points', size='Player Count', 
                                hover_name='Country', color='Country', title="National Performance Index Matrix")
        fig_nation.update_layout(xaxis_title="Active Field Size (Player Count)", yaxis_title="Average Performance Metric (Points)")
        st.plotly_chart(fig_nation, use_container_width=True)
        
        st.subheader("Leaderboard: Highest Average Skill Level")
        st.dataframe(country_analysis.sort_values('Avg Points', ascending=False), use_container_width=True, hide_index=True)

# ==================== VENUES ====================
with tab_venue:
    st.header("📍 Venue & Complex Analytics")
    
    opts_venue_country = sorted(venues['country_name'].dropna().unique().tolist()) if 'country_name' in venues.columns else []
    
    v_col1, v_col2 = st.columns(2)
    with v_col1:
        sel_country = st.selectbox("Select Country Map", options=["All Countries"] + opts_venue_country)
        
    venue_subset = venues.copy()
    if sel_country != "All Countries" and 'country_name' in venue_subset.columns:
        venue_subset = venue_subset[venue_subset['country_name'] == sel_country]
        
    with v_col2:
        opts_complex = sorted(venue_subset['complex_name'].dropna().unique().tolist()) if 'complex_name' in venue_subset.columns else []
        sel_complex = st.multiselect("Select Complex Location", options=opts_complex, default=[])
        
    if sel_complex and 'complex_name' in venue_subset.columns:
        venue_subset = venue_subset[venue_subset['complex_name'].isin(sel_complex)]
    
    st.divider()
    m_v1, m_v2, m_v3 = st.columns(3)
    m_v1.metric("Total Venues Matches", len(venue_subset))
    m_v2.metric("Total Active Complexes", venue_subset['complex_name'].nunique() if 'complex_name' in venue_subset.columns else 0)
    m_v3.metric("Unique Timezones", venue_subset['timezone'].nunique() if 'timezone' in venue_subset.columns else 0)
    
    st.divider()
    vc_col1, vc_col2 = st.columns(2)
    with vc_col1:
        st.subheader("🏢 Venue Count per Complex")
        if 'complex_name' in venue_subset.columns:
            complex_counts = venue_subset['complex_name'].value_counts().reset_index()
            complex_counts.columns = ['Complex', 'Venues']
            fig_v_complex = px.bar(complex_counts.head(15), x='Venues', y='Complex', orientation='h', color='Venues', title="Top Facilities Breakdown")
            fig_v_complex.update_layout(xaxis_title="Court Volume Count", yaxis_title="Complex Title")
            st.plotly_chart(fig_v_complex, use_container_width=True)
    with vc_col2:
        st.subheader("🌎 Venues by Country")
        if 'country_name' in venue_subset.columns:
            country_v_counts = venue_subset['country_name'].value_counts().reset_index()
            country_v_counts.columns = ['Country', 'Venues']
            fig_v_country = px.pie(country_v_counts.head(10), names='Country', values='Venues', hole=0.4, title="Global Distribution Grid")
            fig_v_country.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_v_country, use_container_width=True)
    
    st.divider()
    st.subheader("📋 Venue Master List")
    valid_venue_cols = [c for c in ['venue_name', 'complex_name', 'city_name', 'country_name', 'timezone'] if c in venue_subset.columns]
    st.dataframe(venue_subset[valid_venue_cols], use_container_width=True, hide_index=True)

# ==================== GLOBAL UI FOOTER ====================
st.divider()

# Create columns to align links neatly across the bottom
footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])

with footer_col2:
    # Render a clean, stylized HTML markdown link
    st.markdown(
        """
        <div style="text-align: center; font-size: 15px; color: #555555; padding-top: 10px;">
            🔗 Connect with me: 
            <a href="https://www.linkedin.com/in/amar-pujari-89885b389?utm_source=share_via&utm_content=profile&utm_medium=member_android" 
               target="_blank" 
               style="color: #0A66C2; font-weight: bold; text-decoration: none;">
               LinkedIn Profile
            </a>
            <!-- You can add other app links here later using the same <a> tag structure -->
        </div>
        """,
        unsafe_allow_html=True
    )