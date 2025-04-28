import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
from datetime import date, datetime, timedelta

st.set_page_config(page_title="Finansowy Dashboard", layout="wide")

st.title("📊 Mój Dashboard Finansowy")

# 📁 Wczytywanie danych
PLIK_OSZCZEDNOSCI = "oszczednosci.json"
PLIK_CELE = "cele.json"
PLIK_RATY = "raty.json"

# ---------- Wczytywanie ---------- #
def wczytaj_json(nazwa):
    if os.path.exists(nazwa):
        with open(nazwa, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

oszczednosci = wczytaj_json(PLIK_OSZCZEDNOSCI)
cele = wczytaj_json(PLIK_CELE)
raty = wczytaj_json(PLIK_RATY)

# ---------- Podstawowe info ---------- #
dzis = date.today()
miesiac_klucz = f"{dzis.year}-{dzis.month:02}"
kwota_miesieczna = oszczednosci.get("miesieczne", {}).get(miesiac_klucz, 0)
suma_rat = 0
raty_miesiac = []

for r in raty:
    start = datetime.fromisoformat(r["start"]).date()
    koniec = datetime.fromisoformat(r["koniec"]).date()
    if start <= dzis <= koniec:
        suma_rat += r["kwota"]
        raty_miesiac.append(r)

suma_cel = sum(cel["kwota_zebrana"] for cel in cele)
suma_docelowa = sum(cel["kwota_docelowa"] for cel in cele)
procent_cel = (suma_cel / suma_docelowa * 100) if suma_docelowa > 0 else 0

# ---------- Nagłówkowe metryki ---------- #
col1, col2, col3 = st.columns(3)
col1.metric("💸 Raty do zapłaty w tym miesiącu", f"{suma_rat:.2f} zł")
col2.metric("💰 Oszczędności dostępne", f"{kwota_miesieczna:.2f} zł")
col3.metric("🎯 Progres oszczędności", f"{procent_cel:.0f}%")

st.divider()

# ---------- Mini tablica ukończonych celów ---------- #
st.subheader("🏆 Ukończone cele")
cele_ukonczone = [c for c in cele if c.get("ukonczony")]
if cele_ukonczone:
    for cel in cele_ukonczone[-3:][::-1]:
        st.success(f"🎉 {cel['emoji']} {cel['cel']} – osiągnięto {cel['kwota_docelowa']} zł!")
else:
    st.info("Brak ukończonych celów. Ale to się zmieni 💪")

# ---------- Pasek postępu ---------- #
st.subheader("📌 Postęp oszczędzania całkowitego")
progress_val = min(suma_cel / suma_docelowa, 1.0) if suma_docelowa > 0 else 0
st.progress(progress_val, text=f"{suma_cel:.0f} / {suma_docelowa:.0f} zł")

# ---------- Historia oszczędności ---------- #
st.subheader("📈 Oszczędności miesięczne")
df_oszcz = pd.DataFrame.from_dict(oszczednosci.get("miesieczne", {}), orient="index", columns=["Kwota"])
df_oszcz.index.name = "Miesiąc"
df_oszcz.sort_index(inplace=True)
st.bar_chart(df_oszcz)

# ---------- Podsumowanie miesiąca ---------- #
st.subheader("🧠 Podsumowanie miesiąca")
if not df_oszcz.empty:
    ostatni = df_oszcz.iloc[-1]["Kwota"]
    poprzedni = df_oszcz.iloc[-2]["Kwota"] if len(df_oszcz) > 1 else 0
    delta = ostatni - poprzedni
    if delta > 0:
        st.success(f"🔼 Udało Ci się oszczędzić więcej niż miesiąc wcześniej o {delta:.2f} zł. Super robota!")
    elif delta < 0:
        st.warning(f"🔻 W tym miesiącu oszczędności były niższe o {abs(delta):.2f} zł. Może w kolejnym pójdzie lepiej ✨")
    else:
        st.info("Oszczędności na tym samym poziomie co poprzednio. Stabilnie!")

# ---------- Cel tygodniowy ---------- #
st.subheader("📅 Cel tygodniowy")
cel_tygodniowy = 150.0
start_tyg = dzis - timedelta(days=dzis.weekday())
konto_hist = oszczednosci.get("wykorzystane", [])
zebrane_tyg = sum(w["kwota"] for w in konto_hist if datetime.fromisoformat(w["data"]).date() >= start_tyg)

st.markdown(f"🎯 Cel: {cel_tygodniowy} zł | Zebrano: {zebrane_tyg:.2f} zł")
postep = min(zebrane_tyg / cel_tygodniowy, 1.0)
st.progress(postep, text=f"{postep*100:.0f}% tygodniowego celu")

# ---------- Kalendarz płatności ---------- #
st.subheader("🗓️ Kalendarz płatności")
raty_data = [(r["nazwa"], datetime.fromisoformat(r["koniec"]).date()) for r in raty if datetime.fromisoformat(r["koniec"]).date().month == dzis.month]

if raty_data:
    df_kalendarz = pd.DataFrame(raty_data, columns=["Rata", "Data"])
    df_kalendarz = df_kalendarz.sort_values("Data")
    st.dataframe(df_kalendarz, use_container_width=True)
else:
    st.info("Brak zaplanowanych rat w tym miesiącu")

# ---------- Alerty / przypomnienia ---------- #
st.subheader("🔔 Powiadomienia")

if suma_rat > 0:
    st.warning(f"📅 Pamiętaj o ratach w tym miesiącu: {suma_rat:.2f} zł")

if kwota_miesieczna > 0:
    st.info(f"💡 Masz dostępne oszczędności do przypisania: {kwota_miesieczna:.2f} zł")

aktywnych_cel = [c for c in cele if not c.get("ukonczony", False)]
deadline_close = [c for c in aktywnych_cel if (datetime.fromisoformat(c["deadline"]) - datetime.today()).days <= 10 and c["kwota_zebrana"] < c["kwota_docelowa"]]

for cel in deadline_close:
    st.error(f"⏰ Zbliża się deadline celu **{cel['cel']}** – pozostało {(datetime.fromisoformat(cel['deadline']) - datetime.today()).days} dni!")
