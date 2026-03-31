import streamlit as st
import pandas as pd

st.title("Programme Dashboard")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("Raw Data")
    st.write(df)

    if "Program" in df.columns:
        program = st.selectbox("Select Program", df["Program"].unique())
        filtered = df[df["Program"] == program]

        st.subheader("Filtered Data")
        st.write(filtered)

        if "Age" in df.columns:
            st.subheader("Age Distribution")
            st.bar_chart(filtered["Age"])
