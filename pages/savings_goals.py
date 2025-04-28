import streamlit as st
import pandas as pd
import json
import os
import subprocess
from datetime import date, datetime

PLIK_CELE = "cele.json"
PLIK_OSZCZEDNOSCI = "oszczednosci.json"

# ------------- Dane i pomocnicze funkcje ------------- #

def wczytaj_cele():
    if os.path.exists(PLIK_CELE):
        with open(PLIK_CELE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def zapisz_cele(cele):
    with open(PLIK_CELE, "w", encoding="utf-8") as f:
        json.dump(cele, f, indent=2, ensure_ascii=False)

def push_do_gita(komentarz="Aktualizacja celów"):
    try:
        subprocess.run(["git", "add", PLIK_CELE], check=True)
        subprocess.run(["git", "commit", "-m", komentarz], check=True)
        subprocess.run(["git", "push"], check=True)
        st.success("📤 Cele wypchnięte na GitHuba!")
    except subprocess.CalledProcessError as e:
        st.warning("❌ Git push nieudany.")
        st.error(str(e))

def oblicz_kolor_progresu(procent):
    if procent < 0.3:
        return "red"
    elif procent < 0.7:
        return "orange"
    else:
        return "green"

def szacuj_potrzebna_kwote(cel):
    deadline = datetime.fromisoformat(cel["deadline"])
    dzis = datetime.today()
    dni_pozostale = (deadline - dzis).days
    kwota_pozostala = cel["kwota_docelowa"] - cel["kwota_zebrana"]
    if dni_pozostale <= 0 or kwota_pozostala <= 0:
        return None
    miesiace = max(dni_pozostale / 30, 1)
    return round(kwota_pozostala / miesiace, 2)

# ------------- Oszczędności ------------- #

def wczytaj_oszczednosci():
    if os.path.exists(PLIK_OSZCZEDNOSCI):
        with open(PLIK_OSZCZEDNOSCI, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"miesieczne": {}, "wykorzystane": []}

def zapisz_oszczednosci(dane):
    with open(PLIK_OSZCZEDNOSCI, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=2, ensure_ascii=False)

def dodaj_wykorzystanie_oszczednosci(dane, cel, kwota):
    wpis = {
        "data": date.today().isoformat(),
        "cel": cel,
        "kwota": kwota
    }
    dane["wykorzystane"].append(wpis)
    dzis = date.today()
    klucz = f"{dzis.year}-{dzis.month:02}"
    if klucz in dane["miesieczne"]:
        dane["miesieczne"][klucz] -= kwota
        if dane["miesieczne"][klucz] < 0:
            dane["miesieczne"][klucz] = 0
    zapisz_oszczednosci(dane)

# ------------- UI Start ------------- #

st.title("🎯 Moje cele oszczędnościowe")

cele = wczytaj_cele()
oszczednosci = wczytaj_oszczednosci()

# 🔝 Pasek oszczędności na ten miesiąc
dzis = date.today()
miesiac_klucz = f"{dzis.year}-{dzis.month:02}"
kwota_miesieczna = oszczednosci["miesieczne"].get(miesiac_klucz, 0)
kwota_ogolna = sum(oszczednosci["miesieczne"].values())

st.subheader("💸 Twoje oszczędności")
col1, col2 = st.columns(2)
col1.metric("📅 Oszczędności na ten miesiąc", f"{kwota_miesieczna:.2f} zł")
col2.metric("📊 Łącznie dostępne oszczędności", f"{kwota_ogolna:.2f} zł")

if kwota_miesieczna > 0:
    with st.expander("📤 Przypisz oszczędności do celu"):
        dostepne_cele = [cel for cel in cele if not cel.get("ukonczony", False)]
        if dostepne_cele:
            cel_wybor = st.selectbox("Wybierz cel", [c["cel"] for c in dostepne_cele])
            kwota_do_dodania = st.number_input("Kwota do dodania", min_value=0.0, max_value=kwota_miesieczna, step=50.0)
            if st.button("💾 Przypisz oszczędność"):
                for cel in cele:
                    if cel["cel"] == cel_wybor:
                        cel["kwota_zebrana"] += kwota_do_dodania
                        cel.setdefault("doplaty", []).append({
                            "data": date.today().isoformat(),
                            "kwota": kwota_do_dodania
                        })
                        dodaj_wykorzystanie_oszczednosci(oszczednosci, cel_wybor, kwota_do_dodania)
                        zapisz_cele(cele)
                        push_do_gita(f"Dodano oszczędności {kwota_do_dodania} zł do celu: {cel_wybor}")
                        st.success("✅ Oszczędność przypisana!")
                        st.rerun()

with st.expander("📜 Historia przypisanych oszczędności"):
    if oszczednosci["wykorzystane"]:
        df_hist = pd.DataFrame(oszczednosci["wykorzystane"])
        df_hist["data"] = pd.to_datetime(df_hist["data"])
        df_hist = df_hist.sort_values("data", ascending=False)
        st.dataframe(df_hist.rename(columns={"data": "Data", "cel": "Cel", "kwota": "Kwota"}), hide_index=True)
    else:
        st.info("Brak historii przypisań.")

# ➕ Dodawanie celu
with st.form("dodaj_cel"):
    st.subheader("➕ Dodaj nowy cel")
    emoji = st.text_input("Emoji celu (np. 💻 ✈️ 🏠)", max_chars=2, value="🎯")
    nazwa = st.text_input("Nazwa celu")
    kwota_docelowa = st.number_input("Kwota docelowa", min_value=1.0, step=100.0)
    kwota_zebrana = st.number_input("Kwota już zebrana", min_value=0.0, step=100.0)
    deadline = st.date_input("Deadline", value=date.today())

    dodaj = st.form_submit_button("Dodaj cel")
    if dodaj and nazwa:
        cel = {
            "emoji": emoji,
            "cel": nazwa,
            "kwota_docelowa": kwota_docelowa,
            "kwota_zebrana": kwota_zebrana,
            "deadline": deadline.isoformat(),
            "doplaty": [{"data": date.today().isoformat(), "kwota": kwota_zebrana}] if kwota_zebrana > 0 else [],
            "ukonczony": False
        }
        cele.append(cel)
        zapisz_cele(cele)
        push_do_gita(f"Dodano cel: {nazwa}")
        st.success("✅ Cel dodany!")
        st.rerun()

# 📋 Lista celów
st.subheader("📦 Twoje cele:")

if not cele:
    st.info("Brak celów. Dodaj coś powyżej!")
else:
    for i, cel in enumerate(cele):
        if cel.get("ukonczony", False):
            continue

        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                procent = min(cel["kwota_zebrana"] / cel["kwota_docelowa"], 1.0)
                kolor = oblicz_kolor_progresu(procent)

                st.markdown(f"### {cel['emoji']} {cel['cel']}")
                st.markdown(f"📅 Deadline: `{cel['deadline']}`")

                dni_do_deadline = (datetime.fromisoformat(cel["deadline"]) - datetime.today()).days
                if dni_do_deadline <= 14 and procent < 1.0:
                    st.warning(f"⚠️ Zostało tylko {dni_do_deadline} dni do celu!")

                potrzebne = szacuj_potrzebna_kwote(cel)
                if potrzebne:
                    st.markdown(f"💡 Musisz odkładać około `{potrzebne} zł/mies.` aby zdążyć.")

                st.markdown(f"💰 Zebrano: **{cel['kwota_zebrana']} / {cel['kwota_docelowa']} zł**")
                st.progress(procent, text=f"{int(procent*100)}%")

                if procent >= 1.0 and not cel.get("ukonczony"):
                    if st.button("🎉 Oznacz jako ukończony", key=f"oznacz_{i}"):
                        cel["ukonczony"] = True
                        zapisz_cele(cele)
                        push_do_gita(f"Oznaczono cel jako ukończony: {cel['cel']}")
                        st.success("🎉 Gratulacje! Cel został ukończony!")
                        st.rerun()

                with st.expander("💰 Dopłać do celu"):
                    doplata = st.number_input("Kwota dopłaty", min_value=0.0, step=50.0, key=f"doplata_{i}")
                    if st.button("✅ Dopłać", key=f"zapisz_doplata_{i}"):
                        cel["kwota_zebrana"] += doplata
                        cel.setdefault("doplaty", []).append({
                            "data": date.today().isoformat(),
                            "kwota": doplata
                        })
                        zapisz_cele(cele)
                        push_do_gita(f"Dopłacono {doplata} zł do celu: {cel['cel']}")
                        st.success("✅ Dopłata zapisana!")
                        st.rerun()

                with st.expander("📜 Historia dopłat"):
                    if "doplaty" in cel and cel["doplaty"]:
                        df_hist = pd.DataFrame(cel["doplaty"])
                        df_hist["data"] = pd.to_datetime(df_hist["data"])
                        df_hist = df_hist.sort_values("data", ascending=False)
                        st.dataframe(df_hist.rename(columns={"data": "Data", "kwota": "Kwota"}), hide_index=True)
                    else:
                        st.info("Brak dopłat.")

                with st.expander("📝 Zmień deadline"):
                    nowy_deadline = st.date_input("Nowy deadline", value=pd.to_datetime(cel["deadline"]), key=f"edit_deadline_{i}")
                    if st.button("💾 Zapisz deadline", key=f"zapisz_deadline_{i}"):
                        cel["deadline"] = nowy_deadline.isoformat()
                        zapisz_cele(cele)
                        push_do_gita(f"Zmieniono deadline: {cel['cel']}")
                        st.success("📅 Deadline zaktualizowany!")
                        st.rerun()

            with col2:
                if st.button("🗑️ Usuń", key=f"usun_{i}"):
                    cele.pop(i)
                    zapisz_cele(cele)
                    push_do_gita(f"Usunięto cel: {cel['cel']}")
                    st.rerun()
