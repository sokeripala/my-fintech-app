import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Kvantti-Analyysityökalu", layout="wide")

st.title("📊 Osake-Screener & Laatu-Analyysi")

ticker = st.sidebar.text_input("Syötä osakkeen tikkeri (esim. KO, MSFT, AAPL):", "MSFT")

if st.sidebar.button("Suorita analyysi"):
    stock = yf.Ticker(ticker)
    info = stock.info
    
    st.header(f"Analyysi kohteelle: {ticker}")
    
    # Haetaan taseen luvut (vaaditaan Z-scoreen)
    # Huom: yfinance API ei aina anna kaikkia taseen lukuja suoraan, 
    # mutta kokeillaan hakea ne:
    try:
        balance_sheet = stock.balance_sheet
        # Poimitaan tärkeitä lukuja
        total_assets = balance_sheet.loc['Total Assets'].iloc[0]
        total_liabilities = balance_sheet.loc['Total Liabilities Net Minority Interest'].iloc[0]
        working_capital = total_assets - total_liabilities
        
        st.subheader("Taloudelliset tunnusluvut")
        col1, col2, col3 = st.columns(3)
        col1.metric("P/E-luku", info.get('forwardPE', 'N/A'))
        col2.metric("Markkina-arvo", f"{info.get('marketCap', 0)/1e9:.2f} B")
        col3.metric("Käyttöpääoma", f"{working_capital/1e6:.2f} M€")
        
        # Altman Z-scoren laskenta (yksinkertaistettu malli)
        # Z = 1.2 * (Working Capital / Total Assets) + ...
        z_score = 1.2 * (working_capital / total_assets) 
        
        st.subheader("Konkurssiriskin arvio (Altman Z-score)")
        st.write(f"Arvioitu Z-score: **{z_score:.2f}**")
        
        if z_score > 3:
            st.success("Vahva taloudellinen tilanne (Z-score > 3)")
        elif z_score > 1.8:
            st.warning("Harmaa alue")
        else:
            st.error("Kohonnut konkurssiriski (Z-score < 1.8)")
            
    except Exception as e:
        st.error(f"Dataa ei saatu haettua: {e}")

st.sidebar.info("Tämä työkalu käyttää yfinance-rajapintaa live-datan hakemiseen.")
