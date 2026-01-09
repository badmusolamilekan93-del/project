# importing of libaries
import pandas as pd
import plotly.express as px
import streamlit as st
def streamlit_app():
    # page config
    st.set_page_config(
        page_title="School Dataset Dashbord",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    # loading of dataset
    df = pd.read_csv("cleaned_education_dataset.csv")

    # header

    st.title("Education Facilities Dashboard")
    st.caption("A summary of schools' demographics teacher counts, student populstion and basic facilities access")
    st.markdown("---")
    # sidebar
    
    st.sidebar.header("Dashboard Filter")
    facility_filter = st.sidebar.multiselect(
        label="Facility  Type",
        options=df["facility_type_display"].unique(),
        default=df["facility_type_display"].unique()
    )
    management_filter = st.sidebar.multiselect(
        label="Managemnt Filter",
        options=df["management"].unique(),
        default=df["management"].unique()
    )
    lga_filter=st.sidebar.multiselect(
        label="LGA Filter",
        options=df["unique_lga"].unique(),
        default=df["unique_lga"].unique()
    )
    # applying filter
    filtered_df = df[
    (df["facility_type_display"].isin(facility_filter)) &
    (df["management"].isin(management_filter)) &
    (df["unique_lga"].isin(lga_filter))
]
    # KPI summary

    total_schools=len(filtered_df)
    total_students=filtered_df["total_student"].sum()
    avg_student=round(filtered_df["total_student"].mean(),2)
    electricty_pct=round(filtered_df["phcn_electricity"].mean() * 100,1)
    water_pct=round(filtered_df["improved_water_supply"].mean() * 100,1)


    col1, col2, col3, col4, col5= st.columns(5)


    col1.metric("Total Numbers of Schools", total_schools)
    col2.metric("Total Numbers of Students", total_students)
    col3.metric("Average Students Per School", avg_student)
    col4.metric("Percentage of Schools with Electricity",f"{electricty_pct}%")
    col5.metric("Percentage of Schools with Improved Water Supply",f"{water_pct}%")

# Row 1 -  Distribution of School Types & Student Population Distribution
    left, right = st.columns(2)
    with left:
        st.subheader(" Distribution of School Types")
        fig_management= px.bar(
            filtered_df,
            x ="management",
            barmode="group",
            title=" Distribution of School Types"
        )
        st.plotly_chart(fig_management, use_container_width=True)

    with right:
        st.subheader("Student Population Distribution")
        fig_student= px.histogram(
        filtered_df,
        x="total_student",
        barmode="group",
        title="Student Population Distribution",
        )
        st.plotly_chart(fig_student, use_container_width=True)

    # Row 2 - Public vs Private Schools and Electricity Availability
    left, right = st.columns(2)
    with left:
        st.subheader(" Public vs Private Schools")
        pub_priv = filtered_df.groupby("management")["total_student"].sum().reset_index()
        fig_pub_priv = px.bar(
        pub_priv,
        x="management",
        y="total_student",
        title="Public vs Private Schools (Total Students)",
    )
        st.plotly_chart(fig_pub_priv, use_container_width=True)


    with right:
        st.subheader("Electricity Availability")
        fig_electricity =px.pie(
        filtered_df,
        names="phcn_electricity",
        title="Distribution of Electricity Access"
)
        st.plotly_chart(fig_electricity, use_container_width=True)


# Row 3- Water Supply Access and School Locations

    left, right = st.columns(2)
    with left:
        st.subheader("Water Supply Access")
        fig_water = fig = px.pie(
        filtered_df,
        names="improved_water_supply",
        title="Distribution of Water Access"
)
        st.plotly_chart(fig_water, use_container_width=True)

    with right:
        st.subheader("School Locations Map")
        fig_location = px.scatter_mapbox(
        filtered_df,
        lat="latitude",
        lon="longitude",
        zoom=5,
        height=600,
        mapbox_style="open-street-map",
        color="management"
        )
        st.plotly_chart(fig_location, use_container_width=True)
    st.markdown("---")
    st.subheader("Data Preview")
    st.dataframe(filtered_df.head(20))
    st.header("Download Filtered Data")

    @st.cache_data
    def convert_df(df):
        return filtered_df.to_csv(index=False).encode('utf-8')

    csv_data = convert_df(filtered_df)

    st.download_button(
    label="Download Filtered Data as CSV",
    data=csv_data,
    file_name="filtered_schools_data.csv",
    mime="text/csv"
)
if st.sidebar.button("Reset Filters"):
    st.rerun()
    
streamlit_app()