import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="HCT Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Custom styling
st.markdown("""
    <style>
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --danger-color: #d62728;
    }
    
    body {
        background-color: #f8f9fa;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    
    h1 {
        color: #1a1a2e;
        font-weight: bold;
        border-bottom: 4px solid #1f77b4;
        padding-bottom: 10px;
        margin-bottom: 5px;
    }
    
    h2 {
        color: #16213e;
        margin-top: 25px;
        margin-bottom: 15px;
        border-left: 5px solid #ff7f0e;
        padding-left: 10px;
    }
    
    h3 {
        color: #2a3f5f;
    }
    </style>
    """, unsafe_allow_html=True)

# Color palettes
COLOR_PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]
GRADIENT_PALETTE = px.colors.sequential.Blues
CATEGORICAL_PALETTE = px.colors.qualitative.Set2

# Helper function to create trend chart
def create_trend_chart(data, x_col, y_col, title, color="#1f77b4"):
    """Create an interactive trend line chart"""
    fig = px.line(
        data, 
        x=x_col, 
        y=y_col,
        title=title,
        markers=True,
        line_shape="spline"
    )
    fig.update_traces(line=dict(color=color, width=3), marker=dict(size=8))
    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title="Count",
        height=400,
        font=dict(family="Arial", size=12),
        plot_bgcolor="rgba(240, 240, 240, 0.5)",
        paper_bgcolor="white"
    )
    return fig

# Helper function to create bar chart
def create_bar_chart(data, x_col, y_col, title, color_col=None):
    """Create an interactive bar chart"""
    fig = px.bar(
        data,
        x=x_col,
        y=y_col,
        title=title,
        color=color_col if color_col else y_col,
        color_continuous_scale="Blues" if color_col else None,
        text_auto=True
    )
    fig.update_traces(textposition='auto', textangle=0)
    fig.update_layout(
        template="plotly_white",
        hovermode="x",
        height=400,
        showlegend=color_col is not None,
        font=dict(family="Arial", size=12),
        plot_bgcolor="rgba(240, 240, 240, 0.5)",
        paper_bgcolor="white"
    )
    return fig

# Helper function to create pie chart
def create_pie_chart(data, names_col, values_col, title):
    """Create an interactive pie chart"""
    fig = px.pie(
        data,
        names=names_col,
        values=values_col,
        title=title,
        color_discrete_sequence=CATEGORICAL_PALETTE
    )
    fig.update_layout(
        template="plotly_white",
        height=400,
        font=dict(family="Arial", size=12),
        paper_bgcolor="white"
    )
    return fig

st.title("🏥 HCT Programme Dashboard")
st.markdown("**Track trends, visualize impact, and monitor key metrics across locations**")

uploaded_files = st.file_uploader(
    "📁 Upload Excel files for different locations",
    type=["xlsx"],
    accept_multiple_files=True,
    help="Select one or more Excel files containing HCT data"
)

if uploaded_files:
    month_sheet_map = {
        "April": "APR 2025 HCT Captured Data",
        "May": "MAY 2025 HCT Captured Data",
        "June": "JUN 2025 HCT Captured Data",
       
    # Sidebar controls
    st.sidebar.markdown("## 📊 Dashboard Controls")
    selected_month = st.sidebar.selectbox("📅 Select Month", list(month_sheet_map.keys()))
    selected_sheet = month_sheet_map[selected_month]

    all_data = []

    for uploaded_file in uploaded_files:
        try:
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet, header=4)
            df = df.dropna(how="all")
            df.columns = [str(c).strip() for c in df.columns]

            # If Location column does not exist, use file name
            if "Location" not in df.columns:
                file_name = os.path.splitext(uploaded_file.name)[0]
                df["Location"] = file_name

            all_data.append(df)

        except Exception as e:
            st.error(f"❌ Could not read {uploaded_file.name}: {e}")

    if all_data:
        df = pd.concat(all_data, ignore_index=True)

        # Age grouping function
        if "Age" in df.columns:
            df["Age"] = pd.to_numeric(df["Age"], errors="coerce")

            def age_group(age):
                if pd.isna(age):
                    return "Unknown"
                elif age <= 4:
                    return "0-4"
                elif age <= 9:
                    return "5-9"
                elif age <= 14:
                    return "10-14"
                elif age <= 19:
                    return "15-19"
                elif age <= 24:
                    return "20-24"
                elif age <= 34:
                    return "25-34"
                elif age <= 49:
                    return "35-49"
                else:
                    return "50+"

            df["Age Group"] = df["Age"].apply(age_group)

        service_cols = [
            "Condoms Issued (Male)",
            "Condoms Issued (Female)",
            "ARV Follow-up counselling",
            "Negetive test results",
            "New HCT",
            "PCR",
            "Positive test result",
            "HIV+ Follow up",
            "ART Rx Readiness C1",
            "ART Rx Readiness C2",
            "ART Rx Readiness C3",
            "Client starting Treatment",
            "Attends ARV Club",
            "Intensive TB Rx",
            "Continuous TB Rx",
            "TB Screened",
            "Talks Participants (Male)",
            "Talks Participants (Female)"
        ]

        existing_service_cols = [c for c in service_cols if c in df.columns]

        id_columns = [
            c for c in [
                "Session Date (Year/Month/Date)",
                "Patient",
                "DOB (Year/Month/Date)",
                "Age",
                "Age Group",
                "Sex",
                "Location"
            ] if c in df.columns
        ]

        long_df = df.melt(
            id_vars=id_columns,
            value_vars=existing_service_cols,
            var_name="Programme",
            value_name="Value"
        )

        long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
        long_df = long_df[long_df["Value"].fillna(0) > 0]

        # Sidebar filters
        st.sidebar.markdown("---")
        st.sidebar.markdown("## 🔍 Filters")
        
        programme_list = sorted(long_df["Programme"].dropna().unique().tolist())
        programme = st.sidebar.selectbox("Programme", programme_list)

        filtered = long_df[long_df["Programme"] == programme].copy()

        if "Location" in filtered.columns:
            locations = ["All"] + sorted(filtered["Location"].dropna().astype(str).unique().tolist())
            selected_location = st.sidebar.selectbox("Location", locations)
            if selected_location != "All":
                filtered = filtered[filtered["Location"].astype(str) == selected_location]
        else:
            selected_location = "All"

        if "Sex" in filtered.columns:
            sexes = ["All"] + sorted(filtered["Sex"].dropna().astype(str).unique().tolist())
            selected_sex = st.sidebar.selectbox("Sex/Gender", sexes)
            if selected_sex != "All":
                filtered = filtered[filtered["Sex"].astype(str) == selected_sex]
        else:
            selected_sex = "All"

        # Display current selection
        st.markdown(f"### 📍 Current View: **{programme}** | {selected_month} | Location: **{selected_location}** | Gender: **{selected_sex}**")

        # Key metrics
        st.markdown("## 📈 Key Metrics")
        
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            st.metric("📊 Total Records", len(filtered), delta=None)
        
        with metric_cols[1]:
            if "Patient" in filtered.columns:
                patient_count = int(filtered["Patient"].notna().sum())
                st.metric("👥 Patients Listed", patient_count, delta=None)
            else:
                st.metric("👥 Patients Listed", "N/A", delta=None)
        
        with metric_cols[2]:
            if "Age" in filtered.columns:
                avg_age = filtered["Age"].mean()
                st.metric("📅 Average Age", f"{avg_age:.1f}" if pd.notna(avg_age) else "N/A", delta=None)
            else:
                st.metric("📅 Average Age", "N/A", delta=None)
        
        with metric_cols[3]:
            total_value = filtered["Value"].sum()
            st.metric("💯 Total Value", int(total_value), delta=None)

        # Trend analysis
        if "Session Date (Year/Month/Date)" in filtered.columns:
            st.markdown("## 📊 Trend Analysis")
            
            filtered_trend = filtered.dropna(subset=["Session Date (Year/Month/Date)"]).copy()
            filtered_trend["Date Only"] = pd.to_datetime(
                filtered_trend["Session Date (Year/Month/Date)"], errors="coerce"
            ).dt.date
            
            trend_data = filtered_trend.groupby("Date Only").size().reset_index(name="Count")
            
            if len(trend_data) > 0:
                trend_data["Date Only"] = pd.to_datetime(trend_data["Date Only"])
                trend_fig = create_trend_chart(
                    trend_data, 
                    x_col="Date Only", 
                    y_col="Count",
                    title=f"📈 Daily Trend - {programme}",
                    color="#1f77b4"
                )
                st.plotly_chart(trend_fig, use_container_width=True)

        # Demographics breakdown
        st.markdown("## 👨‍👩‍👧‍👦 Demographics")
        
        col_demographics = st.columns(2)
        
        # Age breakdown
        if "Age Group" in filtered.columns:
            with col_demographics[0]:
                age_counts = filtered["Age Group"].value_counts().sort_index().reset_index()
                age_counts.columns = ["Age Group", "Count"]
                age_fig = create_bar_chart(
                    age_counts,
                    x_col="Age Group",
                    y_col="Count",
                    title="👶 Age Group Distribution"
                )
                st.plotly_chart(age_fig, use_container_width=True)
        
        # Sex breakdown
        if "Sex" in filtered.columns:
            with col_demographics[1]:
                sex_counts = filtered["Sex"].value_counts().reset_index()
                sex_counts.columns = ["Sex", "Count"]
                sex_fig = create_pie_chart(
                    sex_counts,
                    names_col="Sex",
                    values_col="Count",
                    title="⚧️ Gender Distribution"
                )
                st.plotly_chart(sex_fig, use_container_width=True)

        # Location breakdown
        if "Location" in filtered.columns and selected_location == "All":
            st.markdown("## 📍 Location Breakdown")
            location_counts = filtered["Location"].value_counts().reset_index()
            location_counts.columns = ["Location", "Count"]
            location_fig = create_bar_chart(
                location_counts,
                x_col="Location",
                y_col="Count",
                title="🏥 Performance by Location"
            )
            st.plotly_chart(location_fig, use_container_width=True)

        # Data export section
        st.markdown("## 💾 Data Export")
        
        export_col1, export_col2 = st.columns(2)
        
        with export_col1:
            if st.button("📥 Download Filtered Data (CSV)"):
                csv = filtered.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"hct_data_{selected_month}_{programme}.csv",
                    mime="text/csv"
                )
        
        with export_col2:
            if st.button("📥 Download Summary Statistics (CSV)"):
                summary_data = {
                    "Metric": ["Total Records", "Total Patients", "Average Age"],
                    "Value": [
                        len(filtered),
                        filtered["Patient"].notna().sum() if "Patient" in filtered.columns else "N/A",
                        f"{filtered['Age'].mean():.1f}" if "Age" in filtered.columns and pd.notna(filtered['Age'].mean()) else "N/A"
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                csv = summary_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Summary as CSV",
                    data=csv,
                    file_name=f"hct_summary_{selected_month}_{programme}.csv",
                    mime="text/csv"
                )

        # Detailed data view
        with st.expander("📋 View Detailed Data Table"):
            st.dataframe(filtered, use_container_width=True, height=400)

else:
    st.info("👆 Please upload Excel files to get started with the dashboard")
