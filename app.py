import streamlit as st
import yfinance as yf
import pandas as pd

# Sivun perusasetukset
st.set_page_config(page_title="Sijoittajan Työkalupakki", layout="wide")

# Alustetaan välimuisti seurantalistaa varten
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

st.title("📈 Sijoittajan Työkalupakki")

tab1, tab2 = st.tabs(["📊 Osake-Screener & Riskilista", "💼 Yhdistelmäsalkun Simulaattori"])

# ==========================================
# VÄLILEHTI 1: OSAKE-SCREENER & SEURANTALISTA
# ==========================================
with tab1:
    st.header("Osake-Screener & Riskilista")
    st.write("Analysoi yksittäisiä osakkeita ja kerää niistä itsellesi seurantalista oikealle.")
    
    col_screener, col_list = st.columns([1, 2.2]) 
    
    with col_screener:
        st.subheader("Hae osaketta")
        ticker = st.text_input("Syötä tikkeri (esim. AAPL, KONE.HE, GOOGL):", "MSFT").upper()

        if st.button("Analysoi ja lisää listalle"):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Taseen luvut Z-scorea varten
                balance_sheet = stock.balance_sheet
                if not balance_sheet.empty and 'Total Assets' in balance_sheet.index:
                    total_assets = balance_sheet.loc['Total Assets'].iloc[0]
                    
                    if 'Total Liabilities Net Minority Interest' in balance_sheet.index:
                        total_liabilities = balance_sheet.loc['Total Liabilities Net Minority Interest'].iloc[0]
                    elif 'Total Liabilities' in balance_sheet.index:
                        total_liabilities = balance_sheet.loc['Total Liabilities'].iloc[0]
                    else:
                        total_liabilities = 0
                        
                    working_capital = total_assets - total_liabilities
                    z_score = 1.2 * (working_capital / total_assets)
                else:
                    z_score = None 
                
                # Haetaan tunnusluvut
                beta = info.get('beta', None)
                pe_ratio = info.get('forwardPE', None)
                current_ratio = info.get('currentRatio', None)
                debt_to_equity = info.get('debtToEquity', None)
                
                rev_growth = info.get('revenueGrowth', None)
                profit_margin = info.get('profitMargins', None)
                eps = info.get('trailingEps', None)
                roe = info.get('returnOnEquity', None)
                
                # Lisätään osake listalle UUSILLA otsikoilla
                st.session_state.watchlist.append({
                    "Tikkeri": ticker,
                    "Nimi": info.get('shortName', ticker),
                    "Z-Score (Turva >2.6)": round(z_score, 2) if z_score else "N/A",
                    "Beta (Markkina = 1)": round(beta, 2) if beta else "N/A",
                    "Maksuvalmius (Tavoite >1.5)": round(current_ratio, 2) if current_ratio else "N/A",
                    "Velka/Oma Pääoma (Hyvä <100)": round(debt_to_equity, 2) if debt_to_equity else "N/A",
                    "P/E (Norm. 15-25)": round(pe_ratio, 2) if pe_ratio else "N/A",
                    "Liikevaihdon kasvu % (Hyvä >10)": round(rev_growth * 100, 2) if rev_growth else "N/A",
                    "Voittomarginaali % (Hyvä >15)": round(profit_margin * 100, 2) if profit_margin else "N/A",
                    "ROE % (Hyvä >15)": round(roe * 100, 2) if roe else "N/A",
                    "EPS (Osakekoht. tulos)": round(eps, 2) if eps else "N/A"
                })
                
                st.success(f"{ticker} analysoitu ja lisätty listalle!")
                
            except Exception as e:
                st.error(f"Dataa ei saatu haettua osakkeelle {ticker}. Varmista tikkerin oikeinkirjoitus.")

    with col_list:
        st.subheader("Oma Seurantalista")
        st.write("Vertaile osakkeiden riskiprofiileja. Vihreä = Vahva/Turvallinen, Punainen = Heikko/Riski.")
        
        if len(st.session_state.watchlist) > 0:
            df_watchlist = pd.DataFrame(st.session_state.watchlist)
            df_watchlist = df_watchlist.drop_duplicates(subset=["Tikkeri"], keep="last").reset_index(drop=True)
            
            # --- VÄRIKOODAUS (Päivitetty uusiin otsikoihin) ---
            def color_risk_metrics(val, col_name):
                if pd.isna(val) or val == "N/A":
                    return ""
                try:
                    v = float(val)
                    if col_name == "Z-Score (Turva >2.6)":
                        if v > 2.6: return "color: #10b981; font-weight: bold;" 
                        elif v < 1.8: return "color: #ef4444; font-weight: bold;" 
                    elif col_name == "Beta (Markkina = 1)":
                        if v < 1.0: return "color: #10b981;"
                        elif v > 1.2: return "color: #ef4444; font-weight: bold;"
                    elif col_name == "Maksuvalmius (Tavoite >1.5)":
                        if v > 1.5: return "color: #10b981;"
                        elif v < 1.0: return "color: #ef4444; font-weight: bold;"
                    elif col_name == "Velka/Oma Pääoma (Hyvä <100)":
                        if v < 100: return "color: #10b981;"
                        elif v > 200: return "color: #ef4444; font-weight: bold;"
                    elif col_name == "Liikevaihdon kasvu % (Hyvä >10)":
                        if v > 10.0: return "color: #10b981; font-weight: bold;"
                        elif v < 0: return "color: #ef4444; font-weight: bold;"
                    elif col_name == "Voittomarginaali % (Hyvä >15)":
                        if v > 15.0: return "color: #10b981; font-weight: bold;"
                        elif v < 5.0: return "color: #ef4444; font-weight: bold;"
                    elif col_name == "ROE % (Hyvä >15)":
                        if v > 15.0: return "color: #10b981; font-weight: bold;"
                        elif v < 5.0: return "color: #ef4444; font-weight: bold;"
                    return ""
                except:
                    return ""

            styled_df = df_watchlist.style.map(
                lambda v: "", 
            ).apply(
                lambda col: [color_risk_metrics(v, col.name) for v in col], 
                axis=0
            )
            
            st.dataframe(styled_df, use_container_width=True)
            
            # --- YKSITTÄISEN OSAKKEEN POISTAMINEN ---
            st.markdown("### Hallinnoi listaa")
            col_del1, col_del2, col_del3 = st.columns([2, 1, 1])
            
            tickers_in_list = df_watchlist['Tikkeri'].tolist()
            with col_del1:
                del_ticker = st.selectbox("Valitse poistettava osake:", tickers_in_list, label_visibility="collapsed")
            with col_del2:
                if st.button("🗑️ Poista valittu"):
                    st.session_state.watchlist = [item for item in st.session_state.watchlist if item['Tikkeri'] != del_ticker]
                    st.rerun()
            with col_del3:
                if st.button("Tyhjennä koko lista"):
                    st.session_state.watchlist = []
                    st.rerun()
        else:
            st.info("Listasi on tyhjä. Hae osakkeita vasemmalta lisätäksesi niitä tähän.")


# ==========================================
# VÄLILEHTI 2: YHDISTELMÄSALKUN SIMULAATTORI
# ==========================================
with tab2:
    st.header("Yhdistelmäsalkun Simulaattori (Inflaatiokorjattu)")
    st.write("Opi miten allokaatio, inflaatio ja piilokulut vaikuttavat varallisuutesi kehitykseen pitkässä juoksussa.")
    
    col_nyk, col_tuleva = st.columns(2)
    
    with col_nyk:
        st.subheader("1. Nykyinen varallisuus")
        start_aot = st.number_input("Arvo-osuustilin nykyarvo (€)", min_value=0, value=10000, step=1000)
        aot_voitto_pct = st.slider("Josta voittoa AOT:lla (%)", 0, 100, 10)
        
        start_ost = st.number_input("Osakesäästötilin nykyarvo (€)", min_value=0, value=0, step=1000)
        ost_voitto_pct = st.slider("Josta voittoa OST:lla (%)", 0, 100, 0)
        
        start_sav = st.number_input("Säästötilin saldo (€)", min_value=0, value=5000, step=1000)
        start_kay = st.number_input("Käyttötilin saldo (Likvidi raha) (€)", min_value=0, value=2000, step=500)
        
        st.subheader("2. Markkinaoletukset & Kulut")
        vuodet = st.slider("Aika-horisontti (vuosia)", 1, 40, 20)
        inflaatio = st.slider("Inflaatio-oletus / v (%)", 0.0, 10.0, 2.0, step=0.5) / 100
        arvonnousu = st.slider("Osakkeiden arvonnousu / v (%)", 0.0, 15.0, 5.0, step=0.5) / 100
        osinko = st.slider("Osakkeiden osinkotuotto / v (%)", 0.0, 10.0, 3.0, step=0.5) / 100
        korko_saasto = st.slider("Säästötilin korko / v (%)", 0.0, 10.0, 3.0, step=0.5) / 100
        
        st.markdown("---")
        kulut = st.slider("Rahastojen hallinnointi- & kaupankäyntikulut / v (%)", 0.0, 3.0, 0.4, step=0.1) / 100
        st.caption("Esim. halpa indeksirahasto 0,2 %, perinteinen pankkirahasto 1,5 %.")

    with col_tuleva:
        st.subheader("3. Tulevat säästöt & Allokaatio")
        kk_saasto = st.number_input("Uusi kuukausisäästö yhteensä (€)", min_value=0, max_value=10000, value=300, step=50)
        
        st.write("Mihin uudet säästöt jaetaan? (Summan pitää olla 100 %)")
        osuus_aot = st.number_input("AOT Osuus (%)", min_value=0, max_value=100, value=40)
        osuus_ost = st.number_input("OST Osuus (%)", min_value=0, max_value=100, value=40)
        osuus_sav = st.number_input("Säästötilin Osuus (%)", min_value=0, max_value=100, value=15)
        osuus_kay = st.number_input("Käyttötilin Osuus (%)", min_value=0, max_value=100, value=5)
        
        yhteensa = osuus_aot + osuus_ost + osuus_sav + osuus_kay
        
        if yhteensa != 100:
            st.error(f"Allokaatio on nyt {yhteensa} %. Korjaa luvut niin, että summa on tasan 100 %.")
        else:
            st.success("Allokaatio 100 % – Valmis simuloitavaksi!")
            
            if (osuus_sav + osuus_kay) < 10 and kk_saasto > 0:
                st.warning("⚠️ **Huomio!** Käteispuskurisi (säästö- ja käyttötili) osuus uusista säästöistä on alle 10 %. Jos elämässä tulee yllättävä kulu (esim. auton hajoaminen), saatat joutua myymään osakkeita huonoon aikaan mahdollisella tappiolla.")

    # Lasketaan vain, jos prosentit menevät oikein
    if yhteensa == 100:
        
        bal_aot = start_aot
        bal_ost = start_ost
        bal_sav = start_sav
        bal_kay = start_kay
        
        hist_aot_paaoma = start_aot * (1 - (aot_voitto_pct / 100))
        hist_ost_paaoma = start_ost * (1 - (ost_voitto_pct / 100))
        deposited_ost = hist_ost_paaoma
        sijoitettu_oma_raha = hist_aot_paaoma + hist_ost_paaoma + start_sav + start_kay
        
        vert_sav_bal = start_aot + start_ost + start_sav
        vert_kay_bal = start_kay
        vert_kaikki_kay = start_aot + start_ost + start_sav + start_kay
        
        maksetut_kulut_yhteensa = 0
        
        data = []
        
        for i in range(vuodet + 1):
            discount = (1 + inflaatio) ** i
            
            salkun_arvo = bal_aot + bal_ost + bal_sav + bal_kay
            skenaario_saasto = vert_sav_bal + vert_kay_bal
            skenaario_kaytto = vert_kaikki_kay
            
            data.append({
                "Vuosi": str(i), 
                "Yhdistelmäsalkku (€)": salkun_arvo / discount,
                "Jos sijoitukset säästötilillä (€)": skenaario_saasto / discount,
                "Jos kaikki käyttötilillä (€)": skenaario_kaytto / discount,
                "Sijoitettu Pääoma (€)": sijoitettu_oma_raha / discount
            })
            
            if i == vuodet:
                break
                
            vuosisäästö = kk_saasto * 12
            sijoitettu_oma_raha += vuosisäästö
            
            in_aot = vuosisäästö * (osuus_aot / 100)
            in_ost = vuosisäästö * (osuus_ost / 100)
            in_sav = vuosisäästö * (osuus_sav / 100)
            in_kay = vuosisäästö * (osuus_kay / 100)
            
            # KASVU: Varsinainen salkku
            bal_kay += in_kay
            
            bal_sav += in_sav
            bal_sav += (bal_sav * korko_saasto) * 0.70
            
            # AOT
            bal_aot += in_aot
            div_aot = bal_aot * osinko
            tax_aot = (div_aot * 0.85) * 0.30
            bal_aot += (div_aot - tax_aot)
            bal_aot += (bal_aot * arvonnousu)
            kulu_aot = bal_aot * kulut
            bal_aot -= kulu_aot
            maksetut_kulut_yhteensa += kulu_aot
            
            # OST
            talletus = 0
            if deposited_ost < 100000:
                talletus = min(in_ost, 100000 - deposited_ost)
                deposited_ost += talletus
                bal_aot += (in_ost - talletus)
                
            bal_ost += talletus
            bal_ost += (bal_ost * osinko)
            bal_ost += (bal_ost * arvonnousu)
            kulu_ost = bal_ost * kulut
            bal_ost -= kulu_ost
            maksetut_kulut_yhteensa += kulu_ost
            
            # KASVU: Vertailuskenaariot
            vert_kay_bal += in_kay
            vert_sav_bal += (in_aot + in_ost + in_sav)
            vert_sav_bal += (vert_sav_bal * korko_saasto) * 0.70
            
            vert_kaikki_kay += vuosisäästö

        columns_order = ["Yhdistelmäsalkku (€)", "Jos sijoitukset säästötilillä (€)", "Jos kaikki käyttötilillä (€)", "Sijoitettu Pääoma (€)"]
        df = pd.DataFrame(data).set_index("Vuosi")[columns_order]
        
        st.write("---")
        st.subheader("Varallisuuden kehitys reaaliarvona (Inflaatiokorjattu ostovoima)")
        st.line_chart(df, color=["#10b981", "#f97316", "#ef4444", "#94a3b8"])
        
        loppuarvo = data[-1]["Yhdistelmäsalkku (€)"]
        omat_rahat = data[-1]["Sijoitettu Pääoma (€)"]
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("Oma säästö yhteensä (Reaaliarvo)", f"{omat_rahat:,.0f} €".replace(",", " "))
        col_res2.metric("Salkun arvo lopussa (Reaaliarvo)", f"{loppuarvo:,.0f} €".replace(",", " "))
        
        maksetut_kulut_reaali = maksetut_kulut_yhteensa / ((1 + inflaatio) ** vuodet)
        col_res3.metric("Maksetut piilokulut (Reaaliarvo)", f"-{maksetut_kulut_reaali:,.0f} €".replace(",", " "))
