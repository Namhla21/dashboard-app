from pathlib import Path

app_code = r'''
import re
from typing import Optional, List

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Programme Dashboard", layout="wide")


# -----------------------------
# Helpers
# -----------------------------
def normalize(col: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(col).strip().lower())


def find_first_match(columns: List[str], keywords: List[str]) -> Optional[str]:
    normalized = {c: normalize(c) for c in columns}
    for key in keywords:
        nkey = normalize(key)
        for original, normed in normalized.items():
            if nkey == normed or nkey in normed:
                return original
    return None


def try_load_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")

    # Try convert common date columns
    for col in df.columns:
        if any(word in normalize(col) for word in ["date", "month", "year", "visit", "test"]):
            try:
                converted = pd.to_datetime(df[col], errors="coerce")
                if converted.notna().sum() > 0:
                    df[col] = converted
            except Exception:
                pass

    # Try convert numeric-looking columns
    for col in df.columns:
        if df[col].dtype == object:
            maybe_num = pd.to_numeric(df[col], errors="coerce")
            if maybe_num.notna().sum() >= max(3, int(len(df) * 0.5)):
                df[col] = maybe_num

    return df


def build_age_group(age):
    if pd.isna(age):
        return "Unknown"
    try:
        age = float(age)
    except Exception:
        return "Unknown"

    if age < 0:
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
    elif age <= 59:
        return "50-59"
    else:
        return "60+"


def detect_columns(df: pd.DataFrame):
    columns = list(df.columns)

    program_col = find_first_match(columns, [
        "program", "programme", "service", "project"
    ])
    name_col = find_first_match(columns, [
        "name", "full name", "fullname", "client", "beneficiary", "participant"
    ])
    age_col = find_first_match(columns, [
        "age", "years"
    ])
    branch_col = find_first_match(columns, [
        "branch", "site", "location", "office", "facility"
    ])
    date_col = find_first_match(columns, [
        "date", "visit date", "service date", "month", "report date", "test date"
    ])
    gender_col = find_first_match(columns, [
        "gender", "sex"
    ])
    outcome_col = find_first_match(columns, [
        "result", "status", "outcome", "test result", "hiv result"
    ])

    return {
        "program_col": program_col,
        "name_col": name_col,
        "age_col": age_col,
        "branch_col": branch_col,
        "date_col": date_col,
        "gender_col": gender_col,
        "outcome_col": outcome_col,
    }


def standardize_outcome(series: pd.Series) -> pd.Series:
    def fix(v):
        if pd.isna(v):
            return "Unknown"
        s = str(v).strip().lower()
        if s in {"positive", "pos", "+", "1", "reactive"}:
            return "Positive"
        if s in {"negative", "neg", "-", "0", "non-reactive", "non reactive"}:
            return "Negative"
        return str(v).strip()

    return series.apply(fix)


# -----------------------------
# UI
# -----------------------------
st.title("Programme Trends Dashboard")
st.caption("Upload an Excel or CSV file, then filter by programme, branch, age group, and more.")

uploaded_file = st.file_uploader("Upload your data file", type=["xlsx", "xls", "csv"])

with st.expander("Expected helpful columns"):
    st.write(
        """
        This app works best if your file contains columns like:
        - Program / Programme
        - Name / Beneficiary
        - Age
        - Branch / Site
        - Date
        - Result / Outcome
        - Gender
        
        It can still work even if some columns are missing.
        """
    )

if not uploaded_file:
    st.info("Please upload your data file to start.")
    st.stop()

try:
    raw_df = try_load_file(uploaded_file)
    df = clean_dataframe(raw_df)
except Exception as e:
    st.error(f"Could not read the file: {e}")
    st.stop()

detected = detect_columns(df)

st.sidebar.header("Column mapping")
program_col = st.sidebar.selectbox("Programme column", ["None"] + list(df.columns), index=(["None"] + list(df.columns)).index(detected["program_col"]) if detected["program_col"] else 0)
name_col = st.sidebar.selectbox("Name column", ["None"] + list(df.columns), index=(["None"] + list(df.columns)).index(detected["name_col"]) if detected["name_col"] else 0)
age_col = st.sidebar.selectbox("Age column", ["None"] + list(df.columns), index=(["None"] + list(df.columns)).index(detected["age_col"]) if detected["age_col"] else 0)
branch_col = st.sidebar.selectbox("Branch column", ["None"] + list(df.columns), index=(["None"] + list(df.columns)).index(detected["branch_col"]) if detected["branch_col"] else 0)
date_col = st.sidebar.selectbox("Date column", ["None"] + list(df.columns), index=(["None"] + list(df.columns)).index(detected["date_col"]) if detected["date_col"] else 0)
gender_col = st.sidebar.selectbox("Gender column", ["None"] + list(df.columns), index=(["None"] + list(df.columns)).index(detected["gender_col"]) if detected["gender_col"] else 0)
outcome_col = st.sidebar.selectbox("Result/Outcome column", ["None"] + list(df.columns), index=(["None"] + list(df.columns)).index(detected["outcome_col"]) if detected["outcome_col"] else 0)

program_col = None if program_col == "None" else program_col
name_col = None if name_col == "None" else name_col
age_col = None if age_col == "None" else age_col
branch_col = None if branch_col == "None" else branch_col
date_col = None if date_col == "None" else date_col
gender_col = None if gender_col == "None" else gender_col
outcome_col = None if outcome_col == "None" else outcome_col

work_df = df.copy()

if age_col:
    work_df["Age Group"] = work_df[age_col].apply(build_age_group)

if outcome_col:
    work_df["Outcome Clean"] = standardize_outcome(work_df[outcome_col])

st.sidebar.header("Filters")

if program_col:
    program_options = ["All"] + sorted(work_df[program_col].dropna().astype(str).unique().tolist())
    selected_program = st.sidebar.selectbox("Choose programme", program_options)
else:
    selected_program = "All"

if branch_col:
    branch_options = ["All"] + sorted(work_df[branch_col].dropna().astype(str).unique().tolist())
    selected_branch = st.sidebar.selectbox("Choose branch", branch_options)
else:
    selected_branch = "All"

if gender_col:
    gender_options = ["All"] + sorted(work_df[gender_col].dropna().astype(str).unique().tolist())
    selected_gender = st.sidebar.selectbox("Choose gender", gender_options)
else:
    selected_gender = "All"

if "Age Group" in work_df.columns:
    age_options = ["All"] + sorted(work_df["Age Group"].dropna().astype(str).unique().tolist())
    selected_age_group = st.sidebar.selectbox("Choose age group", age_options)
else:
    selected_age_group = "All"

filtered = work_df.copy()

if program_col and selected_program != "All":
    filtered = filtered[filtered[program_col].astype(str) == selected_program]

if branch_col and selected_branch != "All":
    filtered = filtered[filtered[branch_col].astype(str) == selected_branch]

if gender_col and selected_gender != "All":
    filtered = filtered[filtered[gender_col].astype(str) == selected_gender]

if "Age Group" in filtered.columns and selected_age_group != "All":
    filtered = filtered[filtered["Age Group"].astype(str) == selected_age_group]

# -----------------------------
# KPI cards
# -----------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total records", len(filtered))

if program_col:
    k2.metric("Programmes", filtered[program_col].nunique())
elif branch_col:
    k2.metric("Branches", filtered[branch_col].nunique())
else:
    k2.metric("Columns", len(filtered.columns))

if outcome_col and "Outcome Clean" in filtered.columns:
    pos_count = (filtered["Outcome Clean"] == "Positive").sum()
    neg_count = (filtered["Outcome Clean"] == "Negative").sum()
    k3.metric("Positive", int(pos_count))
    k4.metric("Negative", int(neg_count))
else:
    if age_col:
        avg_age = pd.to_numeric(filtered[age_col], errors="coerce").mean()
        k3.metric("Average age", f"{avg_age:.1f}" if pd.notna(avg_age) else "N/A")
    else:
        k3.metric("Average age", "N/A")

    if name_col:
        k4.metric("Unique names", filtered[name_col].nunique())
    else:
        k4.metric("Unique names", "N/A")

st.divider()

# -----------------------------
# Dashboard charts
# -----------------------------
left, right = st.columns(2)

with left:
    st.subheader("Age breakdown")
    if "Age Group" in filtered.columns:
        age_breakdown = filtered["Age Group"].value_counts().sort_index()
        st.bar_chart(age_breakdown)
        st.dataframe(
            age_breakdown.rename_axis("Age Group").reset_index(name="Count"),
            use_container_width=True
        )
    else:
        st.info("No age column mapped.")

with right:
    st.subheader("Programme breakdown")
    if program_col:
        prog_breakdown = filtered[program_col].astype(str).value_counts()
        st.bar_chart(prog_breakdown)
        st.dataframe(
            prog_breakdown.rename_axis("Programme").reset_index(name="Count"),
            use_container_width=True
        )
    else:
        st.info("No programme column mapped.")

left2, right2 = st.columns(2)

with left2:
    st.subheader("Branch breakdown")
    if branch_col:
        branch_breakdown = filtered[branch_col].astype(str).value_counts()
        st.bar_chart(branch_breakdown)
        st.dataframe(
            branch_breakdown.rename_axis("Branch").reset_index(name="Count"),
            use_container_width=True
        )
    else:
        st.info("No branch column mapped.")

with right2:
    st.subheader("Result breakdown")
    if outcome_col and "Outcome Clean" in filtered.columns:
        result_breakdown = filtered["Outcome Clean"].astype(str).value_counts()
        st.bar_chart(result_breakdown)
        st.dataframe(
            result_breakdown.rename_axis("Result").reset_index(name="Count"),
            use_container_width=True
        )
    else:
        st.info("No outcome/result column mapped.")

st.subheader("Trend over time")
if date_col:
    temp = filtered.copy()
    temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
    temp = temp.dropna(subset=[date_col])
    if len(temp) > 0:
        temp["Month"] = temp[date_col].dt.to_period("M").astype(str)
        trend = temp.groupby("Month").size()
        st.line_chart(trend)
        st.dataframe(
            trend.rename_axis("Month").reset_index(name="Count"),
            use_container_width=True
        )
    else:
        st.info("The selected date column could not be converted into dates.")
else:
    st.info("No date column mapped.")

st.divider()

# -----------------------------
# Detail views
# -----------------------------
tab1, tab2, tab3 = st.tabs(["Names list", "Age table", "Filtered data"])

with tab1:
    st.subheader("List of names")
    if name_col:
        show_cols = [c for c in [name_col, program_col, age_col, "Age Group", branch_col, gender_col, outcome_col, date_col] if c and c in filtered.columns]
        if "Age Group" in filtered.columns and "Age Group" not in show_cols:
            show_cols.append("Age Group")
        names_df = filtered[show_cols].copy() if show_cols else filtered.copy()
        st.dataframe(names_df, use_container_width=True)
    else:
        st.info("No name column mapped.")

with tab2:
    st.subheader("Age breakdown table by programme")
    if program_col and "Age Group" in filtered.columns:
        age_table = pd.crosstab(filtered[program_col], filtered["Age Group"])
        st.dataframe(age_table, use_container_width=True)
    elif "Age Group" in filtered.columns:
        age_table = filtered["Age Group"].value_counts().sort_index()
        st.dataframe(age_table.rename_axis("Age Group").reset_index(name="Count"), use_container_width=True)
    else:
        st.info("No age data available.")

with tab3:
    st.subheader("Filtered dataset")
    st.dataframe(filtered, use_container_width=True)

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered data as CSV",
    data=csv,
    file_name="filtered_programme_data.csv",
    mime="text/csv"
)

st.caption("Tip: upload your latest Excel report and map the columns in the sidebar if the app does not detect them correctly.")
'''


Open terminal in the folder and run:

```bash
pip install -r requirements.txt
