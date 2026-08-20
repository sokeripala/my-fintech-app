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
    st.header("Yhdistelmäsalkun Simulaattori")
    st.write("Määritä nykyinen varallisuutesi, jaa tulevat kuukausisäästösi ja katso, miten kokonaisuus kehittyy.")
    
    col_nyk, col_tuleva = st.columns(2)
    
    with col_nyk:
        st.subheader("1. Nykyinen varallisuus (Alkusalkku)")
        
        # AOT
        start_aot = st.number_input("Arvo-osuustilin nykyarvo (€)", min_value=0, value=50000, step=1000)
        aot_voitto_pct = st.slider("Josta voittoa AOT:lla (%)", 0, 100, 20)
        
        # OST
        start_ost = st.number_input("Osakesäästötilin nykyarvo (€)", min_value=0, value=20000, step=1000)
        ost_voitto_pct = st.slider("Josta voittoa OST:lla (%)", 0, 100, 10)
        
        # Tilit
        start_sav = st.number_input("Säästötilin saldo (€)", min_value=0, value=10000, step=1000)
        start_kay = st.number_input("Käyttötilin saldo (Likvidi raha) (€)", min_value=0, value=3000, step=500)
        
        st.subheader("2. Markkinaoletukset")
        vuodet = st.slider("Aika-horisontti (vuosia)", 1, 40, 20)
        arvonnousu = st.slider("Arvonnousu / v (%)", 0.0, 15.0, 5.0, step=0.5) / 100
        osinko = st.slider("Osinkotuotto / v (%)", 0.0, 10.0, 3.0, step=0.5) / 100
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
        
        # Alustetaan nykyiset saldot
        bal_aot = start_aot
        bal_ost = start_ost
        bal_sav = start_sav
        bal_kay = start_kay
        
        # Lasketaan paljonko omaa rahaa (pääomaa) on sijoitettu historiallisesti
        # Vähennetään nykyarvosta voiton osuus, jotta saadaan alkuperäinen sijoitus
        hist_aot_paaoma = start_aot * (1 - (aot_voitto_pct / 100))
        hist_ost_paaoma = start_ost * (1 - (ost_voitto_pct / 100))
        
        # OST talletusrajan seuranta (paljonko 100k rajasta on jo käytetty)
        deposited_ost = hist_ost_paaoma
        
        # Kokonaisoma raha alussa
        sijoitettu_oma_raha = hist_aot_paaoma + hist_ost_paaoma + start_sav + start_kay
        
        # Datan keräys kuvaajaa varten
        data = []
        
        for i in range(vuodet + 1):
            salkun_arvo = bal_aot + bal_ost + bal_sav + bal_kay
            data.append({"Vuosi": i, "Sijoitettu Pääoma (€)": sijoitettu_oma_raha, "Yhdistelmäsalkun Arvo (€)": salkun_arvo})
            
            if i == vuodet:
                break
                
            # Vuosittaiset säästösummat tileittäin
            vuosisäästö = kk_saasto * 12
            sijoitettu_oma_raha += vuosisäästö
            
            in_aot = vuosisäästö * (osuus_aot / 100)
            in_ost = vuosisäästö * (osuus_ost / 100)
            in_sav = vuosisäästö * (osuus_sav / 100)
            in_kay = vuosisäästö * (osuus_kay / 100)
            
            # Käyttötili (ei kasva korkoa, ei veroteta)
            bal_kay += in_kay
            
            # Säästötili (verotetaan vuosittain lähdeverolla)
            bal_sav += in_sav
            bruttokorko = bal_sav * korko_saasto
            korkovero = bruttokorko * 0.30
            bal_sav += (bruttokorko - korkovero)
            
            # AOT (osinkovero 30% verotettavasta osuudesta)
            bal_aot += in_aot
            div_aot = bal_aot * osinko
            tax_aot = (div_aot * 0.85) * 0.30
            bal_aot += (div_aot - tax_aot)
            bal_aot += (bal_aot * arvonnousu)
            
            # OST (verovapaa kasvu sisällä, seurataan talletusrajaa)
            talletus = 0
            if deposited_ost < 100000:
                talletus = min(in_ost, 100000 - deposited_ost)
                deposited_ost += talletus
                
                # Jos kaikki OST-säästöt eivät mahtuneet tilille, ylimääräinen raha 
                # ohjautuu tässä yksinkertaistetussa mallissa verolliselle AOT:lle.
                yli_jaanyt = in_ost - talletus
                bal_aot += yli_jaanyt
                
            bal_ost += talletus
            bal_ost += (bal_ost * osinko)
            bal_ost += (bal_ost * arvonnousu)

        # Tehdään datasta Pandas-taulukko ja piirretään kuvaaja
        df = pd.DataFrame(data).set_index("Vuosi")
        
        st.write("---")
        st.subheader("Yhdistelmäsalkun kasvu (Kaikki varallisuus)")
        st.line_chart(df)
        
        # Lopputulokset
        loppuarvo = data[-1]["Yhdistelmäsalkun Arvo (€)"]
        omat_rahat = data[-1]["Sijoitettu Pääoma (€)"]
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("Oma säästö yhteensä", f"{omat_rahat:,.0f} €".replace(",", " "))
        col_res2.metric("Salkun arvo lopussa (brutto)", f"{loppuarvo:,.0f} €".replace(",", " "))
        col_res3.metric("Kokonaisvoitto (ennen myyntiveroja)", f"{(loppuarvo - omat_rahat):,.0f} €".replace(",", " "))
