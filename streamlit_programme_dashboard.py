import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="HCT Dashboard", layout="wide")

st.title("HCT Programme Dashboard")

uploaded_files = st.file_uploader(
    "Upload Excel files for different locations",
    type=["xlsx"],
    accept_multiple_files=True
)

if uploaded_files:
    month_sheet_map = {
        "April": "APR 2025 HCT Captured Data",
        "May": "MAY 2025 HCT Captured Data",
        "June": "JUN 2025 HCT Captured Data"
    }

    selected_month = st.sidebar.selectbox("Choose Month", list(month_sheet_map.keys()))
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
            st.warning(f"Could not read {uploaded_file.name}: {e}")

    if all_data:
        df = pd.concat(all_data, ignore_index=True)

        st.subheader(f"Combined Raw Data - {selected_month}")
        st.write(df)

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

        st.sidebar.header("Filters")

        programme = st.sidebar.selectbox(
            "Choose Programme",
            sorted(long_df["Programme"].dropna().unique())
        )

        filtered = long_df[long_df["Programme"] == programme].copy()

        if "Location" in filtered.columns:
            locations = ["All"] + sorted(filtered["Location"].dropna().astype(str).unique().tolist())
            selected_location = st.sidebar.selectbox("Choose Location", locations)
            if selected_location != "All":
                filtered = filtered[filtered["Location"].astype(str) == selected_location]

        if "Sex" in filtered.columns:
            sexes = ["All"] + sorted(filtered["Sex"].dropna().astype(str).unique().tolist())
            selected_sex = st.sidebar.selectbox("Choose Sex", sexes)
            if selected_sex != "All":
                filtered = filtered[filtered["Sex"].astype(str) == selected_sex]

        st.subheader(f"Records for: {programme} ({selected_month})")
        st.write(filtered)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Records", len(filtered))

        with col2:
            if "Patient" in filtered.columns:
                st.metric("Patients Listed", filtered["Patient"].notna().sum())

        with col3:
            if "Age" in filtered.columns:
                avg_age = filtered["Age"].mean()
                st.metric("Average Age", f"{avg_age:.1f}" if pd.notna(avg_age) else "N/A")

        if "Age Group" in filtered.columns:
            st.subheader("Age Breakdown")
            age_counts = filtered["Age Group"].value_counts().sort_index()
            st.bar_chart(age_counts)
            st.write(age_counts)

        if "Sex" in filtered.columns:
            st.subheader("Sex Breakdown")
            sex_counts = filtered["Sex"].value_counts()
            st.bar_chart(sex_counts)
            st.write(sex_counts)

        if "Location" in filtered.columns:
            st.subheader("Location Breakdown")
            location_counts = filtered["Location"].value_counts()
            st.bar_chart(location_counts)
            st.write(location_counts)

        if "Session Date (Year/Month/Date)" in filtered.columns:
            filtered["Session Date (Year/Month/Date)"] = pd.to_datetime(
                filtered["Session Date (Year/Month/Date)"], errors="coerce"
            )

            trend_df = filtered.dropna(subset=["Session Date (Year/Month/Date)"]).copy()
            trend_df["Date Only"] = trend_df["Session Date (Year/Month/Date)"].dt.date

            trend = trend_df.groupby("Date Only").size()

            if len(trend) > 0:
                st.subheader("Trend Over Time")
                st.line_chart(trend)
