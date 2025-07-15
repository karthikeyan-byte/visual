import streamlit as st
import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt

# Helper functions (same as your code)
def extract_mfg_id(text):
    if isinstance(text, str):
        ids = re.findall(r"([A-Z0-9]{5,})", text.upper())
        return ids[0] if ids else None
    return None

def clean_mfg_code(text):
    if isinstance(text, str):
        cleaned = text.replace("MFG#:", "").replace("#ABA", "").strip()
        return cleaned if cleaned else None
    return None

def parse_price(text):
    if isinstance(text, str):
        m = re.search(r"\$?([\d,]+\.?\d*)", text)
        if m:
            return float(m.group(1).replace(",", ""))
    return np.nan

st.title("Price Comparison Dashboard")

# File upload widgets
rd_file = st.file_uploader("Upload your company's Excel file (rdollors)", type=["xlsx"])
comp_file = st.file_uploader("Upload competitor's Excel file", type=["xlsx"])

if rd_file and comp_file:
    # Load files
    rd = pd.read_excel(rd_file)
    comp = pd.read_excel(comp_file)
    
    st.subheader("Your Data Sample")
    st.dataframe(rd.head())
    st.subheader("Competitor Data Sample")
    st.dataframe(comp.head())

    # Process rdollors data
    rd["price_rd"] = rd["price"].apply(parse_price)

    # Process competitor data
    comp["mfg_code_clean"] = comp["MFG Code"].apply(clean_mfg_code)
    comp["price_comp"] = comp["Discounted Price"].apply(parse_price)

    # Extract or assign mfg_id
    if "mfg_id" in rd.columns:
        rd_mfg_col = "mfg_id"
    elif "mfr_part" in rd.columns:
        rd["mfg_id"] = rd["mfr_part"].apply(extract_mfg_id)
        rd_mfg_col = "mfg_id"
    else:
        st.error("Could not find mfg_id or mfr_part column in your file.")
        st.stop()

    # Merge
    merged = pd.merge(
        rd[[rd_mfg_col, "price_rd"]].groupby(rd_mfg_col).mean().reset_index(),
        comp[["mfg_code_clean", "price_comp"]].groupby("mfg_code_clean").mean().reset_index(),
        left_on=rd_mfg_col,
        right_on="mfg_code_clean",
        how="inner"
    ).dropna()

    merged["price_diff"] = merged["price_rd"] - merged["price_comp"]
    top_items = merged.sort_values("price_diff", key=abs, ascending=False).head(20)

    # Plotting
    x = np.arange(len(top_items))
    width = 0.35

    fig, ax = plt.subplots(figsize=(15, 8))
    bars1 = ax.bar(x - width/2, top_items["price_rd"], width, label="rdollors", color='blue', alpha=0.7)
    bars2 = ax.bar(x + width/2, top_items["price_comp"], width, label="competitor", color='red', alpha=0.7)

    ax.set_xlabel("Manufacturing ID")
    ax.set_ylabel("Price (USD)")
    ax.set_title("Price Comparison by Manufacturing ID")
    ax.set_xticks(x)
    ax.set_xticklabels(top_items[rd_mfg_col], rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # Add labels on bars
    for bar in bars1 + bars2:
        height = bar.get_height()
        ax.annotate(f'${height:.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8)

    st.pyplot(fig)

    # Show table
    st.subheader("Top 20 Manufacturing IDs by Price Difference")
    st.dataframe(top_items[[rd_mfg_col, "price_rd", "price_comp", "price_diff"]])

else:
    st.info("Please upload both files to proceed.")
