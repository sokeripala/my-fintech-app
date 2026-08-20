import streamlit as st
import yfinance as yf
import pandas as pd

# Sivun perusasetukset
st.set_page_config(page_title="Kvantti-Analyysityökalu", layout="wide")
st.title("📈 Sijoittajan Työkalupakki")

# Luodaan kaksi välilehteä sovellukseen
tab1, tab2 = st.tabs(["📊 Osake-Screener (Z-Score)", "💼 Yhdistelmäsalkun Simulaattori"])

# ==========================================
# VÄLILEHTI 1: OSAKE-SCREENER
# ==========================================
with tab1:
    st.header("Osake-Screener & Laatu-Analyysi")
    st.write("Etsi osakkeita ja arvioi niiden konkurssiriskiä Altman Z-scoren avulla.")
    
    ticker = st.text_input("Syötä osakkeen tikkeri (esim. KO, MSFT, AAPL):", "MSFT")

    if st.button("Suorita analyysi"):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            st.subheader(f"Analyysi kohteelle: {ticker}")
            
            balance_sheet = stock.balance_sheet
            total_assets = balance_sheet.loc['Total Assets'].iloc[0]
            total_liabilities = balance_sheet.loc['Total Liabilities Net Minority Interest'].iloc[0]
            working_capital = total_assets - total_liabilities
            
            st.write("### Taloudelliset tunnusluvut")
            col1, col2, col3 = st.columns(3)
            col1.metric("P/E-luku", info.get('forwardPE', 'N/A'))
            col2.metric("Markkina-arvo", f"{info.get('marketCap', 0)/1e9:.2f} B")
            col3.metric("Käyttöpääoma", f"{working_capital/1e6:.2f} M€")
            
            # Altman Z-score
            z_score = 1.2 * (working_capital / total_assets) 
            
            st.write("### Konkurssiriskin arvio (Altman Z-score)")
            st.write(f"Arvioitu Z-score: **{z_score:.2f}**")
            
            if z_score > 3:
                st.success("Vahva taloudellinen tilanne (Z-score > 3)")
            elif z_score > 1.8:
                st.warning("Harmaa alue")
            else:
                st.error("Kohonnut konkurssiriski (Z-score < 1.8)")
                
        except Exception as e:
            st.error(f"Dataa ei saatu haettua. Varmista tikkerin oikeinkirjoitus. (Virhe: {e})")


# ==========================================
# VÄLILEHTI 2: YHDISTELMÄSALKUN SIMULAATTORI
# ==========================================
with tab2:
    st.header("Yhdistelmäsalkun Simulaattori (Inflaatiokorjattu)")
    st.write("Määritä nykyinen varallisuutesi, jaa tulevat kuukausisäästösi ja vertaile tuottoa suhteessa säästötiliin tai käteiseen.")
    
    col_nyk, col_tuleva = st.columns(2)
    
    with col_nyk:
        st.subheader("1. Nykyinen varallisuus")
        start_aot = st.number_input("Arvo-osuustilin nykyarvo (€)", min_value=0, value=50000, step=1000)
        aot_voitto_pct = st.slider("Josta voittoa AOT:lla (%)", 0, 100, 20)
        
        start_ost = st.number_input("Osakesäästötilin nykyarvo (€)", min_value=0, value=20000, step=1000)
        ost_voitto_pct = st.slider("Josta voittoa OST:lla (%)", 0, 100, 10)
        
        start_sav = st.number_input("Säästötilin saldo (€)", min_value=0, value=10000, step=1000)
        start_kay = st.number_input("Käyttötilin saldo (Likvidi raha) (€)", min_value=0, value=3000, step=500)
        
        st.subheader("2. Markkinaoletukset")
        vuodet = st.slider("Aika-horisontti (vuosia)", 1, 40, 20)
        inflaatio = st.slider("Inflaatio-oletus / v (%)", 0.0, 10.0, 2.0, step=0.5) / 100
        arvonnousu = st.slider("Osakkeiden arvonnousu / v (%)", 0.0, 15.0, 5.0, step=0.5) / 100
        osinko = st.slider("Osakkeiden osinkotuotto / v (%)", 0.0, 10.0, 3.0, step=0.5) / 100
        korko_saasto = st.slider("Säästötilin korko / v (%)", 0.0, 10.0, 3.0, step=0.5) / 100

    with col_tuleva:
        st.subheader("3. Tulevat säästöt & Allokaatio")
        kk_saasto = st.number_input("Uusi kuukausisäästö yhteensä (€)", min_value=0, max_value=10000, value=500, step=50)
        
        st.write("Mihin uudet säästöt jaetaan? (Summan pitää olla tasan 100 %)")
        osuus_aot = st.number_input("AOT Osuus (%)", min_value=0, max_value=100, value=30)
        osuus_ost = st.number_input("OST Osuus (%)", min_value=0, max_value=100, value=30)
        osuus_sav = st.number_input("Säästötilin Osuus (%)", min_value=0, max_value=100, value=30)
        osuus_kay = st.number_input("Käyttötilin Osuus (%)", min_value=0, max_value=100, value=10)
        
        yhteensa = osuus_aot + osuus_ost + osuus_sav + osuus_kay
        
        if yhteensa != 100:
            st.error(f"Allokaatio on nyt {yhteensa} %. Korjaa luvut niin, että summa on tasan 100 %.")
        else:
            st.success("Allokaatio 100 % – Valmis simuloitavaksi!")

    # Lasketaan vain, jos prosentit menevät oikein
    if yhteensa == 100:
        
        # 1. Alustetaan varsinaisen yhdistelmäsalkun saldot
        bal_aot = start_aot
        bal_ost = start_ost
        bal_sav = start_sav
        bal_kay = start_kay
        
        # Pääoman laskenta ja OST-rajan seuranta
        hist_aot_paaoma = start_aot * (1 - (aot_voitto_pct / 100))
        hist_ost_paaoma = start_ost * (1 - (ost_voitto_pct / 100))
        deposited_ost = hist_ost_paaoma
        sijoitettu_oma_raha = hist_aot_paaoma + hist_ost_paaoma + start_sav + start_kay
        
        # 2. Alustetaan VERTAILUSKENAARIOT
        # Skenaario A (Oranssi): Sijoitukset laitetaan säästötilille, käyttötili pidetään ennallaan
        vert_sav_bal = start_aot + start_ost + start_sav
        vert_kay_bal = start_kay
        
        # Skenaario B (Punainen): Kaikki rahat pidetään täysin tuottamattomana käyttötilillä
        vert_kaikki_kay = start_aot + start_ost + start_sav + start_kay
        
        # Datan keräys
        data = []
        
        for i in range(vuodet + 1):
            # Inflaatiokorjauksen kerroin nykyvuodelle
            discount = (1 + inflaatio) ** i
            
            salkun_arvo = bal_aot + bal_ost + bal_sav + bal_kay
            skenaario_saasto = vert_sav_bal + vert_kay_bal
            skenaario_kaytto = vert_kaikki_kay
            
            # Lisätään dataan, X-akseli tekstinä (str), jotta graafi ei veny miinukselle
            data.append({
                "Vuosi": str(i), 
                "Yhdistelmäsalkku (€)": salkun_arvo / discount,
                "Jos sijoitukset säästötilillä (€)": skenaario_saasto / discount,
                "Jos kaikki käyttötilillä (€)": skenaario_kaytto / discount,
                "Sijoitettu Pääoma (€)": sijoitettu_oma_raha / discount
            })
            
            if i == vuodet:
                break
                
            # Vuosittaiset lisäykset
            vuosisäästö = kk_saasto * 12
            sijoitettu_oma_raha += vuosisäästö
            
            in_aot = vuosisäästö * (osuus_aot / 100)
            in_ost = vuosisäästö * (osuus_ost / 100)
            in_sav = vuosisäästö * (osuus_sav / 100)
            in_kay = vuosisäästö * (osuus_kay / 100)
            
            # ==============================
            # KASVU: Varsinainen salkku
            # ==============================
            bal_kay += in_kay
            bal_sav += in_sav
            bal_sav += (bal_sav * korko_saasto) * 0.70 # Säästötilin korko - 30% lähdevero
            
            bal_aot += in_aot
            div_aot = bal_aot * osinko
            tax_aot = (div_aot * 0.85) * 0.30
            bal_aot += (div_aot - tax_aot)
            bal_aot += (bal_aot * arvonnousu)
            
            talletus = 0
            if deposited_ost < 100000:
                talletus = min(in_ost, 100000 - deposited_ost)
                deposited_ost += talletus
                bal_aot += (in_ost - talletus) # Ylivuoto AOT:lle
                
            bal_ost += talletus
            bal_ost += (bal_ost * osinko)
            bal_ost += (bal_ost * arvonnousu)
            
            # ==============================
            # KASVU: Vertailuskenaariot
            # ==============================
            # A. Säästötili-skenaario (käyttötiliin lisätään sille kuuluva osa, muut menevät säästöön)
            vert_kay_bal += in_kay
            vert_sav_bal += (in_aot + in_ost + in_sav)
            vert_sav_bal += (vert_sav_bal * korko_saasto) * 0.70
            
            # B. Patjanalus-skenaario (Kaikki menee tilille ilman tuottoa)
            vert_kaikki_kay += vuosisäästö

        # Luodaan Pandas Dataframe ja järjestetään sarakkeet haluttuun järjestykseen värejä varten
        columns_order = [
            "Yhdistelmäsalkku (€)", 
            "Jos sijoitukset säästötilillä (€)", 
            "Jos kaikki käyttötilillä (€)", 
            "Sijoitettu Pääoma (€)"
        ]
        df = pd.DataFrame(data).set_index("Vuosi")[columns_order]
        
        st.write("---")
        st.subheader("Varallisuuden kehitys reaaliarvona (Inflaatiokorjattu ostovoima)")
        
        # Piirretään graafi ja pakotetaan pyydetyt värit
        # Vihreä (#10b981), Oranssi (#f97316), Punainen (#ef4444), Harmaa (#94a3b8)
        st.line_chart(df, color=["#10b981", "#f97316", "#ef4444", "#94a3b8"])
        
        # Lopputulokset 
        loppuarvo = data[-1]["Yhdistelmäsalkun Arvo (€)"]
        omat_rahat = data[-1]["Sijoitettu Pääoma (€)"]
        
        st.write("*(Kaikki yllä olevan graafin luvut ovat nykyrahassa, eli inflaation syömä ostovoima on jo vähennetty tuotoista)*")
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("Oma säästö yhteensä (Reaaliarvo)", f"{omat_rahat:,.0f} €".replace(",", " "))
        col_res2.metric("Salkun arvo lopussa (Reaaliarvo)", f"{loppuarvo:,.0f} €".replace(",", " "))
        col_res3.metric("Todellinen ostovoiman kasvu", f"{(loppuarvo - omat_rahat):,.0f} €".replace(",", " "))
