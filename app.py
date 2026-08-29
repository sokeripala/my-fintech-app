import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# Sivun perusasetukset
st.set_page_config(page_title="Sijoittajan Työkalupakki", layout="wide")

# Alustetaan välimuisti seurantalistaa varten
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

st.title("📈 Sijoittajan Työkalupakki")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Osake-Screener & Riskilista", 
    "💼 Yhdistelmäsalkun Simulaattori", 
    "🏡 Nettovarallisuus & Kassavirta",
    "🎯 Talouden Koontinäyttö"
])

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
                
                beta = info.get('beta', None)
                pe_ratio = info.get('forwardPE', None)
                current_ratio = info.get('currentRatio', None)
                debt_to_equity = info.get('debtToEquity', None)
                rev_growth = info.get('revenueGrowth', None)
                profit_margin = info.get('profitMargins', None)
                eps = info.get('trailingEps', None)
                roe = info.get('returnOnEquity', None)
                
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
        
        if len(st.session_state.watchlist) > 0:
            df_watchlist = pd.DataFrame(st.session_state.watchlist)
            df_watchlist = df_watchlist.drop_duplicates(subset=["Tikkeri"], keep="last").reset_index(drop=True)
            
            def color_risk_metrics(val, col_name):
                if pd.isna(val) or val == "N/A": return ""
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
                except: return ""

            styled_df = df_watchlist.style.map(lambda v: "").apply(lambda col: [color_risk_metrics(v, col.name) for v in col], axis=0)
            st.dataframe(styled_df, use_container_width=True)
            
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
                    
            st.markdown("---")
            st.markdown("### 📊 Yksittäisen osakkeen hintakehitys (1 vuosi)")
            valittu_tikkeri = st.selectbox("Valitse osake, jonka kurssia haluat tarkastella:", tickers_in_list)
            if valittu_tikkeri:
                try:
                    graafi_stock = yf.Ticker(valittu_tikkeri)
                    historia = graafi_stock.history(period="1y")
                    st.line_chart(historia['Close'])
                except Exception as e:
                    st.warning("Kurssidataa ei saatu ladattua.")

            # --- UUSI OMINAISUUS: Yhdistetty Salkku vs S&P 500 Graafi ---
            st.markdown("---")
            st.markdown("### 📈 Oma Seurantalista vs. S&P 500 (1 vuosi)")
            st.write("Vertaa tasapainotettua salkkua (jossa jokaiseen listan osakkeeseen on sijoitettu yhtä paljon) yleiseen markkinakehitykseen. Arvot skaalattu alkamaan 100:sta.")
            
            if len(tickers_in_list) > 0:
                portfolio_df = pd.DataFrame()
                with st.spinner("Lasketaan tuottoja ja haetaan vertailuindeksiä..."):
                    # 1. Haetaan omat osakkeet
                    for t in tickers_in_list:
                        try:
                            hist = yf.Ticker(t).history(period="1y")
                            if not hist.empty:
                                portfolio_df[t] = hist['Close']
                        except:
                            pass
                    
                    if not portfolio_df.empty:
                        portfolio_df = portfolio_df.ffill().dropna() 
                        portfolio_norm = (portfolio_df / portfolio_df.iloc[0]) * 100
                        
                        salkku_yhteensa = portfolio_norm.mean(axis=1)
                        salkku_yhteensa.name = "Oma Salkku"
                        
                        # 2. Haetaan S&P 500 indeksi vertailuksi
                        try:
                            sp500_hist = yf.Ticker("^GSPC").history(period="1y")
                            if not sp500_hist.empty:
                                sp500_norm = (sp500_hist['Close'] / sp500_hist['Close'].iloc[0]) * 100
                                sp500_norm.name = "S&P 500"
                                
                                # Yhdistetään taulukot yhteen graafia varten
                                combined_df = pd.concat([salkku_yhteensa, sp500_norm], axis=1).ffill().dropna()
                                st.line_chart(combined_df, color=["#10b981", "#3b82f6"]) # Vihreä salkulle, Sininen S&P500:lle
                            else:
                                st.line_chart(salkku_yhteensa, color="#10b981")
                        except:
                            st.warning("Indeksin datan haku epäonnistui. Näytetään vain oma salkku.")
                            st.line_chart(salkku_yhteensa, color="#10b981")
                    else:
                        st.warning("Hintadataa ei saatu laskentaa varten.")

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
        vuodet_salkku = st.slider("Aika-horisontti (vuosia)", 1, 50, 20, key="vuodet_salkku")
        inflaatio = st.slider("Inflaatio-oletus / v (%)", 0.0, 10.0, 2.0, step=0.5) / 100
        arvonnousu = st.slider("Osakkeiden arvonnousu / v (%)", 0.0, 15.0, 5.0, step=0.5) / 100
        osinko = st.slider("Osakkeiden osinkotuotto / v (%)", 0.0, 10.0, 3.0, step=0.5) / 100
        korko_saasto = st.slider("Säästötilin korko / v (%)", 0.0, 10.0, 3.0, step=0.5) / 100
        st.markdown("---")
        kulut = st.slider("Rahastojen hallinnointi- & kaupankäyntikulut / v (%)", 0.0, 3.0, 0.4, step=0.1) / 100

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
                st.warning("⚠️ **Huomio!** Käteispuskurisi on alle 10 % uusista säästöistä.")

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
        
        for i in range(vuodet_salkku + 1):
            discount = (1 + inflaatio) ** i
            salkun_arvo = bal_aot + bal_ost + bal_sav + bal_kay
            
            data.append({
                "Vuosi": i, 
                "Yhdistelmäsalkku (€)": salkun_arvo / discount,
                "Jos sijoitukset säästötilillä (€)": (vert_sav_bal + vert_kay_bal) / discount,
                "Jos kaikki käyttötilillä (€)": vert_kaikki_kay / discount,
                "Sijoitettu Pääoma (€)": sijoitettu_oma_raha / discount
            })
            
            if i == vuodet_salkku: break
                
            vuosisäästö = kk_saasto * 12
            sijoitettu_oma_raha += vuosisäästö
            
            bal_kay += vuosisäästö * (osuus_kay / 100)
            bal_sav += vuosisäästö * (osuus_sav / 100)
            bal_sav += (bal_sav * korko_saasto) * 0.70
            
            bal_aot += vuosisäästö * (osuus_aot / 100)
            div_aot = bal_aot * osinko
            bal_aot += (div_aot - ((div_aot * 0.85) * 0.30))
            bal_aot += (bal_aot * arvonnousu)
            kulu_aot = bal_aot * kulut
            bal_aot -= kulu_aot
            maksetut_kulut_yhteensa += kulu_aot
            
            in_ost = vuosisäästö * (osuus_ost / 100)
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
            
            vert_kay_bal += vuosisäästö * (osuus_kay / 100)
            vert_sav_bal += vuosisäästö * ((osuus_aot + osuus_ost + osuus_sav) / 100)
            vert_sav_bal += (vert_sav_bal * korko_saasto) * 0.70
            vert_kaikki_kay += vuosisäästö

        df = pd.DataFrame(data).set_index("Vuosi")[["Yhdistelmäsalkku (€)", "Jos sijoitukset säästötilillä (€)", "Jos kaikki käyttötilillä (€)", "Sijoitettu Pääoma (€)"]]
        
        st.write("---")
        st.subheader("Varallisuuden kehitys reaaliarvona")
        st.line_chart(df, color=["#10b981", "#f97316", "#ef4444", "#94a3b8"])
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("Oma säästö (Reaaliarvo)", f'{data[-1]["Sijoitettu Pääoma (€)"]:,.0f} €'.replace(",", " "))
        col_res2.metric("Salkun arvo lopussa", f'{data[-1]["Yhdistelmäsalkku (€)"]:,.0f} €'.replace(",", " "))
        col_res3.metric("Maksetut piilokulut", f'-{maksetut_kulut_yhteensa / ((1 + inflaatio) ** vuodet_salkku):,.0f} €'.replace(",", " "))


# ==========================================
# VÄLILEHTI 3: NETTOVARALLISUUS & KASSAVIRTA
# ==========================================
with tab3:
    st.header("🏡 Kokonaisvaltainen Talouden Simulaattori")
    st.write("Miten asunnon osto, autolaina ja elämisen kulut vaikuttavat kykyysi vaurastua?")
    
    sim_vuodet = st.slider("Simulaation kesto (vuosia)", 5, 50, 20, step=5)
    
    col_kassa, col_asunto, col_auto = st.columns(3)
    
    with col_kassa:
        st.subheader("Kassavirta & Sijoitukset")
        tulot = st.number_input("Nettotulot yhteensä (€ / kk)", min_value=0, value=3000, step=100)
        elinkulut = st.number_input("Muut elinkulut (ruoka, laskut, huvit) (€ / kk)", min_value=0, value=1200, step=50)
        
        st.markdown("---")
        sijoitukset_alku = start_aot + start_ost + start_sav
        salkun_kokonaistuotto = arvonnousu + osinko
        
        st.metric("Sijoitukset ostohetkellä (Haettu sivulta 2)", f"{sijoitukset_alku:,.0f} €".replace(",", " "))
        st.metric("Salkun tuotto-oletus", f"{salkun_kokonaistuotto * 100:.1f} %")
        st.caption("Yli jäävä raha (Tulot - Menot) ohjataan salkkuun kasvamaan korkoa.")

    with col_asunto:
        st.subheader("Asunnon Osto & Asuminen")
        osto_vuosi = st.slider("Asunnon oston ajankohta (vuosi)", 0, sim_vuodet, 0)
        st.caption("Aseta 0, jos omistat asunnon jo nyt.")
        vuokra = st.number_input("Vuokra ennen ostoa (€/kk)", min_value=0, value=800, step=50)
        
        st.markdown("---")
        asunto_hinta = st.number_input("Asunnon ostohinta / Nykyarvo (€)", min_value=0, value=200000, step=5000)
        asuntolaina_maara = st.number_input("Haettava lainasumma (€)", min_value=0, max_value=asunto_hinta, value=170000, step=5000)
        st.info(f"Käsiraha / Oma rahoitusosuus: **{asunto_hinta - asuntolaina_maara:,.0f} €** (Vähennetään salkusta ostohetkellä)")
        
        as_korko = st.slider("Asuntolainan korko (%)", 0.0, 10.0, 3.5, step=0.1)
        as_maksuaika = st.slider("Lainan maksuaika (vuosia)", 5, 35, 25)
        vastike = st.number_input("Hoitovastike / Kiinteistövero (€ / kk)", min_value=0, value=250, step=10)

    with col_auto:
        st.subheader("Auto")
        auto_arvo_alku = st.number_input("Auton nykyarvo (€)", min_value=0, value=25000, step=1000)
        autolaina_alku = st.number_input("Autolainaa jäljellä (€)", min_value=0, value=20000, step=1000)
        auto_lyhennys = st.number_input("Autolainan lyhennys (€ / kk)", min_value=0, value=300, step=50)
        auto_korko = st.slider("Autolainan korko (%)", 0.0, 15.0, 6.0, step=0.1)
        autokulut = st.number_input("Auton kulut (vakuutus, bensa, huollot) (€ / kk)", min_value=0, value=200, step=10)

    # --- SIMULAATIO LOGIIKKA ---
    asunto_arvo = 0
    asuntolaina = 0
    auto_arvo = auto_arvo_alku
    autolaina = autolaina_alku
    salkku = sijoitukset_alku
    
    # Laske asuntolainan kuukausilyhennys (tasalyhennys)
    as_lyhennys = (asuntolaina_maara / (as_maksuaika * 12)) if as_maksuaika > 0 else 0
    
    maksetut_korot_yht = 0
    nw_data = []
    
    for vuosi in range(sim_vuodet + 1):
        
        # Oston hetki: asunnon arvo ilmestyy, laina astuu voimaan ja salkusta vähennetään käsiraha
        if vuosi == osto_vuosi:
            asunto_arvo = asunto_hinta
            asuntolaina = asuntolaina_maara
            kasiraha = asunto_hinta - asuntolaina_maara
            salkku -= kasiraha

        kokonaisvelka = asuntolaina + autolaina
        omaisuus = asunto_arvo + auto_arvo + salkku
        nettovarallisuus = omaisuus - kokonaisvelka
        
        nw_data.append({
            "Vuosi": vuosi,
            "Nettovarallisuus (€)": nettovarallisuus,
            "Sijoitukset (€)": salkku,
            "Velat yhteensä (€)": -kokonaisvelka 
        })
        
        if vuosi == sim_vuodet: break
            
        for kk in range(12):
            kk_auto_korko = autolaina * (auto_korko / 100 / 12)
            todellinen_auto_lyhennys = min(autolaina, auto_lyhennys)
            autolaina -= todellinen_auto_lyhennys
            maksetut_korot_yht += kk_auto_korko
            
            asumiskulu = 0
            if vuosi >= osto_vuosi:
                # Maksetaan asuntolainaa ja vastiketta
                kk_as_korko = asuntolaina * (as_korko / 100 / 12)
                todellinen_as_lyhennys = min(asuntolaina, as_lyhennys)
                asuntolaina -= todellinen_as_lyhennys
                maksetut_korot_yht += kk_as_korko
                
                asumiskulu = vastike + kk_as_korko + todellinen_as_lyhennys
            else:
                # Asutaan vielä vuokralla
                asumiskulu = vuokra
            
            menot = elinkulut + asumiskulu + autokulut + kk_auto_korko + todellinen_auto_lyhennys
            jaannos = tulot - menot
            
            salkku += jaannos
            if salkku > 0:
                salkku *= (1 + (salkun_kokonaistuotto / 12)) 
                
        # Vuosittainen arvonnousu ja -lasku
        if vuosi >= osto_vuosi:
            asunto_arvo *= 1.01  
        auto_arvo *= 0.90    

    st.write("---")
    st.subheader("Nettovarallisuutesi Kehitys")
    df_nw = pd.DataFrame(nw_data).set_index("Vuosi")
    st.line_chart(df_nw, color=["#10b981", "#3b82f6", "#ef4444"])
    
    st.markdown(f"### {sim_vuodet} Vuoden Yhteenveto")
    res1, res2, res3 = st.columns(3)
    res1.metric(f"Nettovarallisuus {sim_vuodet}v päästä", f"{nw_data[-1]['Nettovarallisuus (€)']:,.0f} €".replace(",", " "))
    res2.metric("Sijoitusten arvo lopussa", f"{nw_data[-1]['Sijoitukset (€)']:,.0f} €".replace(",", " "))
    res3.metric("Pankille maksetut lainakorot", f"-{maksetut_korot_yht:,.0f} €".replace(",", " "))


# ==========================================
# VÄLILEHTI 4: TALOUDEN KOONTINÄYTTÖ (DASHBOARD)
# ==========================================
with tab4:
    st.header("🎯 Talouden Koontinäyttö (Dashboard)")
    st.write("Visuaalinen yhteenveto taloutesi nykytilasta ja menojen jakautumisesta.")

    col_pie1, col_pie2 = st.columns(2)
    
    # Nykytilanteen määritys osto_vuoden perusteella
    nykyinen_asunto_arvo = asunto_hinta if osto_vuosi == 0 else 0
    nykyinen_asuntolaina = asuntolaina_maara if osto_vuosi == 0 else 0
    
    with col_pie1:
        st.subheader("Kokonaisvarat vs. Velat (Nykytilanne)")
        varat_yhteensa = nykyinen_asunto_arvo + auto_arvo_alku + sijoitukset_alku
        velat_yhteensa = nykyinen_asuntolaina + autolaina_alku
        
        df_varatvelat = pd.DataFrame({
            "Kategoria": ["Kokonaisvarat", "Velat"],
            "Summa (€)": [varat_yhteensa, velat_yhteensa]
        })
        
        chart_vv = alt.Chart(df_varatvelat).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Summa (€)", type="quantitative"),
            color=alt.Color(field="Kategoria", type="nominal", scale=alt.Scale(range=['#10b981', '#ef4444'])),
            tooltip=["Kategoria", "Summa (€)"]
        ).properties(height=300)
        st.altair_chart(chart_vv, use_container_width=True)

    with col_pie2:
        st.subheader("Lainojen jakautuminen")
        if velat_yhteensa > 0:
            df_lainat = pd.DataFrame({
                "Laina": ["Asuntolaina", "Autolaina"],
                "Summa (€)": [nykyinen_asuntolaina, autolaina_alku]
            })
            
            chart_lainat = alt.Chart(df_lainat).mark_arc(innerRadius=0).encode( 
                theta=alt.Theta(field="Summa (€)", type="quantitative"),
                color=alt.Color(field="Laina", type="nominal", scale=alt.Scale(range=['#3b82f6', '#f97316'])),
                tooltip=["Laina", "Summa (€)"]
            ).properties(height=300)
            st.altair_chart(chart_lainat, use_container_width=True)
        else:
            st.success("Mahtavaa, sinulla ei ole lainkaan velkaa!")

    st.markdown("---")
    
    st.subheader("Menojesi jakautuminen (Kuukaudessa - Nykytilanne)")
    
    # Selvitetään ensimmäisen kuukauden todelliset menot
    eka_kk_auto_korko = autolaina_alku * (auto_korko / 100 / 12)
    eka_kk_as_korko = asuntolaina_maara * (as_korko / 100 / 12) if osto_vuosi == 0 else 0
    nykyinen_asumiskulu = (vastike + as_lyhennys + eka_kk_as_korko) if osto_vuosi == 0 else vuokra
    
    nykyinen_saasto = tulot - (elinkulut + nykyinen_asumiskulu + autokulut + auto_lyhennys + eka_kk_auto_korko)
    
    df_menot = pd.DataFrame({
        "Menoerä": [
            "Elinkulut", 
            "Asuminen (Vuokra tai Laina+Vastike)", 
            "Autolaina (lyh+korko)", 
            "Auton kulut", 
            "Säästöön jäävä raha"
        ],
        "Summa (€/kk)": [
            elinkulut,
            nykyinen_asumiskulu,
            auto_lyhennys + eka_kk_auto_korko,
            autokulut,
            nykyinen_saasto
        ]
    })
    
    st.bar_chart(df_menot.set_index("Menoerä"))
    
    st.markdown("---")
    st.subheader("Nettovarallisuuden Kehitys (Kopio simulaatiosta)")
    st.line_chart(df_nw, color=["#10b981", "#3b82f6", "#ef4444"])
