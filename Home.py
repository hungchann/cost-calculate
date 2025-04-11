import streamlit as st
import pandas as pd

# --- App Configuration ---
st.set_page_config(
    layout="wide", 
    page_title="IT Project Profitability Calculator - Home",
    page_icon="📊"
)

st.title("📊 IT Project Profitability Calculator")
st.caption(f"Current Time: {pd.Timestamp.now(tz='Asia/Ho_Chi_Minh').strftime('%Y-%m-%d %H:%M:%S %Z')}")
st.markdown("---")

# App introduction
st.header("Welcome to the IT Project Profitability Calculator")

st.markdown("""
This application helps you calculate the profitability of your IT projects by:

1. **Estimating project revenue** from various sources
2. **Setting target profit margins** for your business
3. **Allocating costs** across different categories
4. **Visualizing the financial breakdown** of your projects

### How to Use This App

Use the navigation sidebar on the left to move between different pages:

- **Cost Calculator**: The main tool for calculating project profitability
- **About**: Information about this application
- **Help**: Detailed usage instructions

### Getting Started

To get started, navigate to the **Cost Calculator** page and input your project details.
""")

# Add a visual element or screenshot of the calculator
st.image("https://via.placeholder.com/800x400.png?text=Project+Profitability+Calculator", 
         caption="IT Project Profitability Calculator Interface", 
         use_column_width=True)

# Footer
st.markdown("---")
st.caption("© 2025 IT Project Profitability Calculator")