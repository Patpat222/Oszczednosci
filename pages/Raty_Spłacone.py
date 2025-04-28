import streamlit as st
import json
import os
from datetime import datetime, date

PLIK_RATY = "raty.json"

st.title("✅ Raty całkowicie spłacone")

def wczytaj_raty():
    if os.path.exists(PLIK_RATY):
        with open(PLIK_RATY, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

raty = wczytaj_raty()
today = date.today()
raty_splacone = []

for rata in raty:
    data_koniec = datetime.fromisoformat(rata["koniec"]).date()
    if today > data_koniec:
        raty_splacone.append(rata)

if not raty_splacone:
    st.info("Nie masz jeszcze całkowicie spłaconych rat. Ale spokojnie, wszystko w swoim czasie 💪")
else:
    for rata in raty_splacone:
        with st.container():
            st.markdown(f"### 🎉 {rata['nazwa']}")
            st.markdown(f"📅 Okres: `{rata['start']} → {rata['koniec']}`")
            st.markdown(f"💰 Kwota miesięczna: **{rata['kwota']} zł**")
            st.success("✅ Rata została w pełni spłacona!")
