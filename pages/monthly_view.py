import streamlit as st
import pandas as pd
import os
import subprocess
from datetime import datetime, timedelta

# 📁 Obsługa plików

def pobierz_nazwe_pliku_z_daty(data):
    return f"wydatki-{data.year}-{data.month:02}.json"

def zapisz_wydatki(df):
    if not df.empty:
        data = pd.to_datetime(df['Data'].iloc[-1])
        plik = pobierz_nazwe_pliku_z_daty(data)
        df.to_json(plik, orient="records", indent=2, date_format="iso")
        return plik
    return None

def wczytaj_wszystkie_wydatki():
    wszystkie = []
    for plik in os.listdir():
        if plik.startswith("wydatki-") and plik.endswith(".json"):
            df = pd.read_json(plik)
            wszystkie.append(df)
    if wszystkie:
        return pd.concat(wszystkie, ignore_index=True)
    else:
        return pd.DataFrame(columns=["Data", "Kwota", "Typ", "Opis"])

def wczytaj_ostatnie_miesiace(df, miesiace=3):
    najnowsza_data = df["Data"].max()
    granica = najnowsza_data - pd.DateOffset(months=miesiace)
    return df[df["Data"] >= granica]

def push_do_gita(komentarz="Aktualizacja wydatków"):
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", komentarz], check=True)
        subprocess.run(["git", "push"], check=True)
        st.success("📤 Dane wypchnięte na GitHuba!")
    except subprocess.CalledProcessError as e:
        st.warning("❌ Nie udało się wykonać git push.")
        st.error(str(e))

# 🧠 Inicjalizacja
if "wydatki" not in st.session_state:
    st.session_state["wydatki"] = wczytaj_wszystkie_wydatki()

if "limit_budzetu" not in st.session_state:
    st.session_state["limit_budzetu"] = 3000.0

st.title("📅 Miesięczny przegląd wydatków")

# ➕ Dodawanie wydatku
with st.form("dodaj_wydatek"):
    st.subheader("➕ Dodaj nowy wydatek")
    data = st.date_input("Data", value=datetime.today())
    kwota = st.number_input("Kwota (zł)", min_value=0.0, step=1.0)
    typ = st.selectbox("Typ wydatku", [
        "PayPo", "Allegro Pay", "Studia", "Audi", "Opłaty stałe",
        "Jedzenie", "Paliwo", "Wyjścia", "Kosmetyki", "Ciuchy", "Inne"
    ])
    opis = st.text_input("Opis")
    submitted = st.form_submit_button("Dodaj wydatek")

    if submitted:
        nowy_wydatek = pd.DataFrame([{
            "Data": data,
            "Kwota": kwota,
            "Typ": typ,
            "Opis": opis
        }])
        st.session_state["wydatki"] = pd.concat(
            [st.session_state["wydatki"], nowy_wydatek], ignore_index=True
        )
        plik_json = zapisz_wydatki(st.session_state["wydatki"])
        if plik_json:
            push_do_gita(f"Dodano nowy wydatek do {plik_json}")
        st.success("✅ Dodano wydatek!")

# 🔍 Filtrowanie

df = st.session_state["wydatki"].copy()
df["Data"] = pd.to_datetime(df["Data"])
df["Miesiąc"] = df["Data"].dt.strftime('%Y-%m')
df["Rok"] = df["Data"].dt.year

st.sidebar.header("📆 Filtry daty")
filtr_rok = st.sidebar.selectbox("Rok", sorted(df["Rok"].unique(), reverse=True))
df_rok = df[df["Rok"] == filtr_rok]

miesiace = df_rok["Miesiąc"].unique()
filtr_miesiac = st.sidebar.selectbox("Miesiąc", sorted(miesiace, reverse=True))
df_miesiac = df_rok[df_rok["Miesiąc"] == filtr_miesiac]

dni = df_miesiac["Data"].dt.date.unique()
filtr_dzien = st.sidebar.selectbox("Dzień", sorted(dni, reverse=True))
df_dzien = df_miesiac[df_miesiac["Data"].dt.date == filtr_dzien]

# 🔎 Typ wydatku
st.sidebar.header("🔍 Filtr według typu wydatku")
dostepne_typy = df["Typ"].unique().tolist()
filtr_typ = st.sidebar.selectbox("Typ wydatku", ["Wszystkie"] + dostepne_typy)

if filtr_typ != "Wszystkie":
    df_rok = df_rok[df_rok["Typ"] == filtr_typ]
    df_miesiac = df_miesiac[df_miesiac["Typ"] == filtr_typ]
    df_dzien = df_dzien[df_dzien["Typ"] == filtr_typ]

# 📌 Opłaty stałe
pokaz_stale = st.sidebar.checkbox("📌 Pokaż tylko opłaty stałe")
if pokaz_stale:
    df_rok = df_rok[df_rok["Typ"] == "Opłaty stałe"]
    df_miesiac = df_miesiac[df_miesiac["Typ"] == "Opłaty stałe"]
    df_dzien = df_dzien[df_dzien["Typ"] == "Opłaty stałe"]

# ⬇️ Eksport do CSV
st.sidebar.header("⬇️ Eksport danych")
if st.sidebar.button("📤 Pobierz miesiąc jako CSV"):
    st.sidebar.download_button(
        label="Pobierz CSV",
        data=df_miesiac.to_csv(index=False).encode("utf-8"),
        file_name=f"wydatki-{filtr_miesiac}.csv",
        mime="text/csv"
    )

# 📋 Lista wpisów z sortowaniem i usuwaniem
tytul_typu = f" ({filtr_typ})" if filtr_typ != "Wszystkie" else ""
st.subheader(f"📋 Wydatki na dzień {filtr_dzien}{tytul_typu}")

sortuj_po = st.selectbox("Sortuj według", ["Data (najnowsze)", "Data (najstarsze)", "Kwota (rosnąco)", "Kwota (malejąco)"])
if sortuj_po == "Data (najnowsze)":
    df_dzien = df_dzien.sort_values(by="Data", ascending=False)
elif sortuj_po == "Data (najstarsze)":
    df_dzien = df_dzien.sort_values(by="Data", ascending=True)
elif sortuj_po == "Kwota (rosnąco)":
    df_dzien = df_dzien.sort_values(by="Kwota", ascending=True)
elif sortuj_po == "Kwota (malejąco)":
    df_dzien = df_dzien.sort_values(by="Kwota", ascending=False)

for idx, row in df_dzien.iterrows():
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 1])
    col1.write(row["Data"].strftime("%Y-%m-%d"))
    col2.write(f"{row['Kwota']} zł")
    col3.write(row["Typ"])
    col4.write(row["Opis"])
    if col5.button("🗑️", key=f"usun_{idx}"):
        st.session_state["wydatki"].drop(index=idx, inplace=True)
        st.session_state["wydatki"].reset_index(drop=True, inplace=True)
        plik = zapisz_wydatki(st.session_state["wydatki"])
        if plik:
            push_do_gita(f"Usunięto wydatek z {plik}")
        st.rerun()

# 📊 Podsumowania
suma_dzien = df_dzien["Kwota"].sum()
suma_miesiac = df_miesiac["Kwota"].sum()
suma_rok = df_rok["Kwota"].sum()

col1, col2, col3 = st.columns(3)
col1.metric(f"🗓️ Dzień{tytul_typu}", f"{suma_dzien:.2f} zł")
col2.metric(f"📆 Miesiąc{tytul_typu}", f"{suma_miesiac:.2f} zł")
col3.metric(f"📅 Rok{tytul_typu}", f"{suma_rok:.2f} zł")

# 📈 Średnie
st.subheader("📈 Statystyki dodatkowe")
srednia_dzienna = df_miesiac.groupby(df_miesiac["Data"].dt.date)["Kwota"].sum().mean()
srednia_typ = df_miesiac[df_miesiac["Typ"] == filtr_typ]["Kwota"].mean() if filtr_typ != "Wszystkie" else None

col_a, col_b = st.columns(2)
col_a.metric("📊 Średnia dzienna (miesiąc)", f"{srednia_dzienna:.2f} zł")
if srednia_typ is not None:
    col_b.metric(f"🎯 Średnia dla typu {filtr_typ}", f"{srednia_typ:.2f} zł")

# 🎯 Limit budżetowy
st.subheader("🎯 Limit budżetowy na miesiąc")
nowy_limit = st.number_input("Ustaw swój miesięczny limit", value=float(st.session_state["limit_budzetu"]), step=100.0)
st.session_state["limit_budzetu"] = nowy_limit

procent_limitu = min(suma_miesiac / nowy_limit, 1.0) if nowy_limit > 0 else 0
st.progress(procent_limitu, text=f"{(procent_limitu*100):.0f}% wykorzystane")

if suma_miesiac > nowy_limit:
    st.error("🚨 Przekroczyłeś swój budżet na ten miesiąc!")
elif suma_miesiac > 0.8 * nowy_limit:
    st.warning("⚠️ Jesteś blisko przekroczenia budżetu.")
else:
    st.success("✅ Mieścisz się w budżecie!")

# 📂 Wykres wg typu
st.subheader("📂 Podział wydatków według typu")
grupy = df_miesiac.groupby("Typ")["Kwota"].sum().sort_values(ascending=False)
st.bar_chart(grupy)
