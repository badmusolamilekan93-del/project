import pandas as pd
import plotly.express as px
import streamlit as st

# --- 1. DATA LOADING & CACHING ---
@st.cache_data
def load_data():
    # Loading both datasets
    df = pd.read_csv('cleaned_dvd_rental_dataset.csv')
    df1 = pd.read_csv('STORE_AND_STAFF_PERFORMANCE.csv')
    
    # Ensure date conversion
    df['film_last_rental_date'] = pd.to_datetime(df['film_last_rental_date'])
    return df, df1

df, df1 = load_data()

# --- 2. SHARED FILTER COMPONENT ---
def get_filtered_data():
    st.sidebar.header("Global Filters")
    
    # Date Range Setup
    min_date = df['film_last_rental_date'].min().date()
    max_date = df['film_last_rental_date'].max().date()

    date_range = st.sidebar.date_input(
        "Date Range", 
        value=(min_date, max_date), 
        min_value=min_date, 
        max_value=max_date
    )

    # Multiselects
    selected_country = st.sidebar.multiselect("Country Filter", options=df['country'].unique(), default=df['country'].unique())
    selected_category = st.sidebar.multiselect("Category Filter", options=df['category'].unique(), default=df['category'].unique())
    
    # Apply Filtering Logic
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        mask = (
            (df['film_last_rental_date'].dt.date >= start_date) & 
            (df['film_last_rental_date'].dt.date <= end_date) &
            (df['country'].isin(selected_country)) &
            (df['category'].isin(selected_category)) 
        )
        f_df = df[mask]
    else:
        f_df = df[(df['country'].isin(selected_country)) & (df['category'].isin(selected_category))]

    # Sidebar Download Button
    st.sidebar.markdown("---")
    csv = f_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Download Filtered Data", data=csv, file_name="filtered_rental_data.csv", mime="text/csv")
    
    return f_df

# --- PAGE 1: EXECUTIVE OVERVIEW ---
def page_executive():
    f_df = get_filtered_data()
    st.title("📈 Executive Overview")

    # Core Stats
    total_rev = f_df['film_total_rental_revenue'].sum()
    total_rentals = f_df['film_total_rental'].sum()
    
    # Active 60-day logic
    current_date = df['film_last_rental_date'].max()
    cust_recency = f_df.groupby('customer_id').agg(last_rental=('film_last_rental_date', 'max'))
    active_count = cust_recency[(current_date - cust_recency['last_rental']).dt.days <= 60].shape[0]

    # --- ADVANCED MONTHLY GROWTH CALCULATION ---
    monthly_rev = f_df.groupby('film_last_rental_date')['film_total_rental_revenue'].sum().sort_index().reset_index()
    growth_pct = 0.0
    latest_rev = 0.0
    
    if len(monthly_rev) > 1:
        latest_rev = monthly_rev.iloc[-1]['film_total_rental_revenue']
        prev_rev = monthly_rev.iloc[-2]['film_total_rental_revenue']
        if prev_rev > 0:
            growth_pct = ((latest_rev - prev_rev) / prev_rev) * 100
    elif len(monthly_rev) == 1:
        latest_rev = monthly_rev.iloc[-1]['film_total_rental_revenue']

    # KPI Rows
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${total_rev:,.2f}")
    col2.metric("Total Rentals", f"{total_rentals:,}")
    col3.metric("Active Customers", f"{active_count:,}")
    col4.metric("Monthly Revenue", f"${latest_rev:,.2f}", delta=f"{growth_pct:.2f}% vs Prev Month")

    st.subheader("Revenue Performance Trend")
    st.plotly_chart(px.line(monthly_rev, x='film_last_rental_date', y='film_total_rental_revenue'), use_container_width=True)

# --- PAGE 2: CUSTOMER ANALYTICS & RETENTION ---
def page_customers():
    f_df = get_filtered_data()
    st.title("👥 Customer Analytics & Retention")

    customer_stats = f_df.groupby('customer_id').agg(
        full_name=('full_name', 'first'),
        total_spend=('total_amount_spent', 'sum'),
        rental_count=('total_rental', 'sum'),
        last_date=('film_last_rental_date', 'max'),
        first_date=('film_last_rental_date', 'min')
    )
    
    current_db_date = f_df['film_last_rental_date'].max()
    customer_stats['days_since_last'] = (current_db_date - customer_stats['last_date']).dt.days
    customer_stats['churn_risk'] = customer_stats['days_since_last'].apply(lambda x: 'High Risk' if x > 60 else 'Active')
    customer_stats['tenure'] = (customer_stats['last_date'] - customer_stats['first_date']).dt.days
    
    repeat_rate = (customer_stats[customer_stats['rental_count'] > 1].shape[0] / len(customer_stats)) * 100

    m1, m2, m3 = st.columns(3)
    m1.metric("Repeat Purchase Rate", f"{repeat_rate:.1f}%")
    m2.metric("Avg Spend per Customer", f"${customer_stats['total_spend'].mean():,.2f}")
    m3.metric("High Churn Risk Count", len(customer_stats[customer_stats['churn_risk'] == 'High Risk']))

    left, right = st.columns(2)
    with left:
        st.subheader("Top 10 High-Value Customers")
        st.plotly_chart(px.bar(customer_stats.nlargest(10, 'total_spend'), x='total_spend', y='full_name', orientation='h'), use_container_width=True)
    with right:
        st.subheader("Customer Tenure vs. Spend")
        st.plotly_chart(px.scatter(customer_stats, x='tenure', y='total_spend', color='churn_risk', hover_data=['full_name']), use_container_width=True)

    st.subheader("Detailed Retention Table")
    st.dataframe(customer_stats[['full_name', 'total_spend', 'days_since_last', 'churn_risk']], use_container_width=True)

# --- PAGE 3: FILM & CATEGORY PERFORMANCE ---
def page_films():
    f_df = get_filtered_data()
    st.title("🎬 Film & Category Performance")

    l, r = st.columns(2)
    with l:
        st.subheader("Top Films by Revenue")
        top_f = f_df.groupby('film_title')['film_total_rental_revenue'].sum().nlargest(10).reset_index()
        st.plotly_chart(px.bar(top_f, x='film_total_rental_revenue', y='film_title', orientation='h'), use_container_width=True)
    with r:
        st.subheader("Revenue by Category")
        cat_rev = f_df.groupby('category')['film_total_rental_revenue'].sum().reset_index()
        st.plotly_chart(px.pie(cat_rev, values='film_total_rental_revenue', names='category', hole=0.4), use_container_width=True)

    st.subheader("Inventory Utilization Risk")
    inv = f_df.groupby('film_title').agg(rentals=('film_total_rental', 'sum'), stock=('inventory_count', 'first')).reset_index()
    inv['utilization'] = inv['rentals'] / inv['stock'].replace(0, 1)
    st.plotly_chart(px.bar(inv.nsmallest(10, 'utilization'), x='film_title', y='utilization',  color_continuous_scale='Reds'), use_container_width=True)

# --- PAGE 4: STORE & STAFF PERFORMANCE ---
def page_stores():
    f_df = get_filtered_data()
    st.title("🏪 Store & Staff Performance")

    l, r = st.columns(2)
    with l:
        st.subheader("Store Revenue Comparison")
        st.plotly_chart(px.bar(df1.groupby('store_id')['total_revenue'].sum().reset_index(), x='store_id', y='total_revenue'), use_container_width=True)
    with r:
        st.subheader("Staff Efficiency (Avg Transaction)")
        st.plotly_chart(px.bar(df1.groupby('full_name')['total_revenue'].mean().reset_index(), x='full_name', y='total_revenue'), use_container_width=True)

# --- PAGE 5: GEOGRAPHIC INSIGHTS ---
def page_geo():
    f_df = get_filtered_data()
    st.title("🌎 Geographic Insights")

    geo_data = f_df.groupby('country').agg(rev=('film_total_rental_revenue', 'sum'), cust=('customer_id', 'nunique')).reset_index()
    st.plotly_chart(px.choropleth(geo_data, locations="country", locationmode='country names', color="country", color_continuous_scale='Viridis'), use_container_width=True)
    
    st.subheader("Regional Preferences")
    top_countries = geo_data.nlargest(10, 'rev')['country']
    reg_df = f_df[f_df['country'].isin(top_countries)].groupby(['country', 'category'])['film_total_rental_revenue'].sum().reset_index()
    st.plotly_chart(px.bar(reg_df, x="country", y="film_total_rental_revenue", color="category", barmode="stack"), use_container_width=True)

# --- MAIN NAVIGATION SETUP ---
pg = st.navigation([
    st.Page(page_executive, title="Executive Overview", icon="📈"),
    st.Page(page_customers, title="Customer Analytics", icon="👥"),
    st.Page(page_films, title="Film Performance", icon="🎬"),
    st.Page(page_stores, title="Store & Staff", icon="🏪"),
    st.Page(page_geo, title="Geographic Insights", icon="🌎")
])

# Global Config
st.set_page_config(page_title="Rental BI Dashboard", layout="wide")
pg.run()