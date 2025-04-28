import streamlit as st
import json
import os
import pandas as pd
from datetime import date, datetime
import matplotlib.pyplot as plt

PLIK_RATY = "raty.json"
PLIK_OSZCZEDNOSCI = "oszczednosci.json"

# ---------- Ładowanie danych ---------- #
def wczytaj_raty():
    if os.path.exists(PLIK_RATY):
        with open(PLIK_RATY, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def wczytaj_oszczednosci():
    if os.path.exists(PLIK_OSZCZEDNOSCI):
        with open(PLIK_OSZCZEDNOSCI, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"miesieczne": {}, "wykorzystane": []}

def zapisz_oszczednosci(dane):
    with open(PLIK_OSZCZEDNOSCI, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=2, ensure_ascii=False)

# ---------- UI ---------- #
st.title("📊 Inteligentna prognoza budżetu")

today = date.today()
miesiac_klucz = f"{today.year}-{today.month:02}"

st.subheader("💸 Twoja wypłata")
wplata = st.number_input("Wpisz swoją wypłatę netto", min_value=0.0, step=100.0)

st.subheader("📜 Średnie miesięczne wydatki z historii")
wydatki = pd.DataFrame()
for plik in os.listdir():
    if plik.startswith("wydatki-") and plik.endswith(".json"):
        df = pd.read_json(plik)
        wydatki = pd.concat([wydatki, df], ignore_index=True)

wydatki["Data"] = pd.to_datetime(wydatki["Data"])
gr = wydatki[wydatki["Data"] >= (today - pd.DateOffset(months=3))]

srednie_typy = gr.groupby("Typ")["Kwota"].sum() / 3
suma_srednia = srednie_typy.sum()

st.write("Na podstawie ostatnich 3 miesięcy, oto Twoje średnie miesięczne wydatki:")
st.dataframe(srednie_typy.round(2).reset_index().rename(columns={"Typ": "Typ wydatku", "Kwota": "Średnio mies."}), hide_index=True)

# ---------- Raty ---------- #
raty = wczytaj_raty()
suma_rat = 0.0
for rata in raty:
    start = datetime.fromisoformat(rata["start"]).date()
    koniec = datetime.fromisoformat(rata["koniec"]).date()
    if start <= today <= koniec:
        suma_rat += rata["kwota"]

# ---------- Wyniki ---------- #
if wplata > 0 and (not srednie_typy.empty or suma_rat > 0):
    st.subheader("📊 Podsumowanie")

    zostaje = wplata - suma_srednia - suma_rat
    st.markdown(f"**🔹 Wypłata:** {wplata:.2f} zł")
    st.markdown(f"**🔸 Średnie wydatki miesięczne:** {suma_srednia:.2f} zł")
    st.markdown(f"**🔸 Raty:** {suma_rat:.2f} zł")
    st.markdown(f"**💰 Potencjalne oszczędności:** `{zostaje:.2f} zł`")

    labels = list(srednie_typy.index) + ["Raty", "Oszczędności"]
    values = list(srednie_typy.values) + [suma_rat, max(zostaje, 0)]
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

    # Zapis do puli oszczędności
    if zostaje > 0:
        oszczednosci = wczytaj_oszczednosci()
        oszczednosci["miesieczne"][miesiac_klucz] = round(zostaje, 2)
        zapisz_oszczednosci(oszczednosci)
        st.success(f"📥 Oszczędności ({zostaje:.2f} zł) dodane do puli na {miesiac_klucz}!")
