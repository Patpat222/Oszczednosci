import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

PLIK_CELE = "cele.json"

def wczytaj_cele():
    if os.path.exists(PLIK_CELE):
        with open(PLIK_CELE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

st.title("🏆 Cele ukończone")

cele = wczytaj_cele()
cele_ukonczone = [cel for cel in cele if cel.get("ukonczony", False)]

if not cele_ukonczone:
    st.info("Jeszcze nie masz ukończonych celów. Ale spokojnie, wszystko przed Tobą! ✨")
else:
    for cel in cele_ukonczone:
        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                emoji = cel.get("emoji", "🎯")
                st.markdown(f"## {emoji} {cel['cel']}")
                st.markdown(f"📅 Deadline: `{cel['deadline']}`")
                st.markdown(f"✅ Udało się zebrać: **{cel['kwota_zebrana']} / {cel['kwota_docelowa']} zł**")
                st.success("🎉 Gratulacje! Cel został osiągnięty!")

                if "doplaty" in cel and cel["doplaty"]:
                    with st.expander("📜 Zobacz historię dopłat"):
                        df_hist = pd.DataFrame(cel["doplaty"])
                        df_hist["data"] = pd.to_datetime(df_hist["data"])
                        df_hist = df_hist.sort_values("data", ascending=False)
                        st.dataframe(df_hist.rename(columns={"data": "Data", "kwota": "Kwota"}), hide_index=True)

            with col2:
                st.markdown("### 🏅")
                st.markdown("**Cel zrealizowany!**")
