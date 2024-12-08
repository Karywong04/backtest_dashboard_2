import streamlit as st
from utils.data_handler import load_stock_list

# Configure the page
st.set_page_config(
    page_title="Backtest Dashboard",
    page_icon="📊",
    layout="centered"
)

def main():
    # Display the title
    st.title("Backtest Dashboard")
    st.markdown("""
    Welcome! The page is still unfinished! I am struggling with it a lot!!!
    """)

    st.subheader("1. Single Stock Analysis")

    st.subheader("2. Multiple Stock Analysis")

    st.info("👉 Use the sidebar to navigate to **Single Stock Analysis** or **Multiple Stock Analysis**.")

if __name__ == "__main__":
    main()
