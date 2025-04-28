import streamlit as st
import pandas as pd
import json
import os
from datetime import date, timedelta, datetime
import calendar
import subprocess

PLIK_RATY = "raty.json"
STATUS_PLIK = "raty_status.json"

def wczytaj_raty():
    if os.path.exists(PLIK_RATY):
        with open(PLIK_RATY, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def zapisz_raty(raty):
    with open(PLIK_RATY, "w", encoding="utf-8") as f:
        json.dump(raty, f, indent=2, ensure_ascii=False)

def push_do_gita(komentarz="Aktualizacja rat"):
    try:
        subprocess.run(["git", "add", PLIK_RATY], check=True)
        subprocess.run(["git", "commit", "-m", komentarz], check=True)
        subprocess.run(["git", "push"], check=True)
        st.success("📤 Zmiany wypchnięte na GitHuba!")
    except subprocess.CalledProcessError as e:
        st.warning("❌ Git push nieudany.")
        st.error(str(e))

def dodaj_miesiace(data, miesiace):
    rok = data.year + ((data.month + miesiace - 1) // 12)
    miesiac = ((data.month + miesiace - 1) % 12) + 1
    dzien = min(data.day, calendar.monthrange(rok, miesiac)[1])
    return date(rok, miesiac, dzien)

def wczytaj_status():
    if os.path.exists(STATUS_PLIK):
        with open(STATUS_PLIK, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def zapisz_status(status):
    with open(STATUS_PLIK, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

def push_status():
    try:
        subprocess.run(["git", "add", STATUS_PLIK], check=True)
        subprocess.run(["git", "commit", "-m", "Aktualizacja statusu rat"], check=True)
        subprocess.run(["git", "push"], check=True)
        st.success("📤 Status rat wypchnięty na GitHuba!")
    except subprocess.CalledProcessError as e:
        st.warning("❌ Git push nieudany.")
        st.error(str(e))

st.title("💳 Moje raty")

raty = wczytaj_raty()
today = date.today()

# Dodawanie raty
with st.form("dodaj_rate"):
    st.subheader("➕ Dodaj nową ratę")
    nazwa = st.text_input("Nazwa (np. Audi, Laptop, Allegro Pay)")
    kwota = st.number_input("Kwota miesięczna", min_value=0.0, step=50.0)
    liczba_rat = st.number_input("Liczba rat", min_value=1, step=1)
    data_start = st.date_input("Data rozpoczęcia", value=today)

    dodaj = st.form_submit_button("Dodaj ratę")
    if dodaj and nazwa:
        data_koniec = dodaj_miesiace(data_start, liczba_rat)
        rata = {
            "nazwa": nazwa,
            "kwota": kwota,
            "liczba_rat": liczba_rat,
            "start": data_start.isoformat(),
            "koniec": data_koniec.isoformat()
        }
        raty.append(rata)
        zapisz_raty(raty)
        push_do_gita(f"Dodano ratę: {nazwa}")
        st.success("✅ Rata dodana!")
        st.rerun()

# Lista rat
st.subheader("📄 Aktywne raty")

for i, rata in enumerate(raty):
    data_start = datetime.fromisoformat(rata["start"]).date()
    data_koniec = datetime.fromisoformat(rata["koniec"]).date()
    miesiace_minelo = max(0, min((today.year - data_start.year) * 12 + (today.month - data_start.month), rata["liczba_rat"]))
    pozostalo = rata["liczba_rat"] - miesiace_minelo
    procent = miesiace_minelo / rata["liczba_rat"]

    with st.container():
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"### 💳 {rata['nazwa']}")
            st.markdown(f"📅 Okres: `{rata['start']} → {rata['koniec']}`")
            st.markdown(f"💰 Kwota miesięczna: **{rata['kwota']} zł**")
            st.markdown(f"📆 Raty zapłacone: `{miesiace_minelo}` z `{rata['liczba_rat']}`")
            st.progress(procent, text=f"{int(procent*100)}% spłacone")

        with col2:
            if st.button("🗑️ Usuń", key=f"usun_{i}"):
                raty.pop(i)
                zapisz_raty(raty)
                push_do_gita(f"Usunięto ratę: {rata['nazwa']}")
                st.rerun()

# Raty do zapłaty w tym miesiącu
st.subheader("📅 Raty do zapłaty w tym miesiącu")

status = wczytaj_status()
miesiac_klucz = f"{today.year}-{today.month:02}"
status_miesiaca = status.get(miesiac_klucz, [])

raty_do_zaplaty = []
for rata in raty:
    start = datetime.fromisoformat(rata["start"]).date()
    koniec = datetime.fromisoformat(rata["koniec"]).date()
    if start <= today <= koniec:
        raty_do_zaplaty.append(rata)

if not raty_do_zaplaty:
    st.success("✅ Wszystkie raty zapłacone lub brak rat w tym miesiącu.")
else:
    suma_miesiaca = sum([r["kwota"] for r in raty_do_zaplaty])
    st.markdown(f"💸 Do zapłaty w **{miesiac_klucz}**: **{suma_miesiaca:.2f} zł**")
    for rata in raty_do_zaplaty:
        nazwa = rata["nazwa"]
        opłacona = nazwa in status_miesiaca

        if st.checkbox(f"{nazwa} – {rata['kwota']} zł", value=opłacona, key=f"check_{nazwa}"):
            if nazwa not in status_miesiaca:
                status_miesiaca.append(nazwa)
                status[miesiac_klucz] = status_miesiaca
                zapisz_status(status)
                push_status()
        else:
            if nazwa in status_miesiaca:
                status_miesiaca.remove(nazwa)
                status[miesiac_klucz] = status_miesiaca
                zapisz_status(status)
                push_status()

# Historia spłat
st.subheader("📜 Historia spłat rat")

if not status:
    st.info("Brak zapisanych spłat z poprzednich miesięcy.")
else:
    for miesiac, raty_lista in sorted(status.items(), reverse=True):
        with st.expander(f"📆 {miesiac} – {len(raty_lista)} rat zapłaconych"):
            for r in raty_lista:
                st.markdown(f"✅ {r}")
