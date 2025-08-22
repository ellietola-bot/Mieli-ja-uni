import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path

# Tiedoston polku
DATA_PATH = Path("data.csv")

# Sarakkeet joita halutaan pitää
COLUMNS = ["Päivä", "Uni_h", "Mieliala", "Stressi", "Huomiot"]

def load_data():
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH)

        # Lisää puuttuvat sarakkeet
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None

        # Muunna vanhat sarakkeet jos löytyy
        if "Mieliala_0_10" in df.columns and df["Mieliala"].isna().all():
            df["Mieliala"] = (pd.to_numeric(df["Mieliala_0_10"], errors="coerce")/2).round().clip(1,5)

        if "Stressi_0_10" in df.columns and df["Stressi"].isna().all():
            df["Stressi"] = pd.to_numeric(df["Stressi_0_10"], errors="coerce").clip(0,10)

        # Päivä päivämääräksi ja palautetaan siisti DataFrame
        df["Päivä"] = pd.to_datetime(df["Päivä"], errors="coerce").dt.date
        df = df[COLUMNS]
        return df.dropna(subset=["Päivä"])
    else:
        return pd.DataFrame(columns=COLUMNS)

# ---------- UI: Syöttölomake ----------
st.title("Uni ja mieliala")
st.caption("Seuraa unta, mielialaa ja stressiä. Data pysyy vain tällä koneella (data.csv).")

with st.form("entry"):
    col1, col2 = st.columns(2)
    with col1:
        paiva = st.date_input("Päivä", value=date.today(), format="DD.MM.YYYY")
        uni = st.slider("Uni (tuntia)", min_value=0.0, max_value=12.0, value=7.5, step=0.5)
        # Tyylimuutos: mieliala-napit väljemmäksi
st.markdown(
    """
    <style>
    div.row-widget.stRadio > div{flex-direction:row; justify-content: space-around;}
    </style>
    """,
    unsafe_allow_html=True,
)

        # Mieliala emojit radiopainikkeina
moods = ["😞", "😕", "😐", "🙂", "🤩"]
mieliala = st.radio("Mieliala", moods, index=2, horizontal=True)

# Muunna emoji numeroksi
mood_map = {"😞": 1, "😕": 2, "😐": 3, "🙂": 4, "🤩": 5}
mieliala_num = mood_map[mieliala]

st.write("Valitsit:", mieliala, "→ arvo", mieliala_num)


with col2:
        stressi = st.slider("Stressi (0–10)", 0, 10, 5)
        huomiot = st.text_area("Huomiot", placeholder="esim. flunssa, lääkitys, painajaisia…")
        submitted = st.form_submit_button("💾 Tallenna")

if submitted:
    # (…kentät…)= st.form_submit_button("💾 Tallenna")

    save_row({
        "Päivä": paiva,
        "Uni_h": float(uni),
        "Mieliala": int(mieliala_num),  # 1–5
        "Stressi": int(stressi),        # 0–10
        "Huomiot": huomiot.strip()})
    st.success("Tallennettu!")


# Näytä kaikki tallennetut rivit
st.subheader(f"📈 Uni, Mieliala & Stressi ({month:02d}/{year})")
recent = filter_month(load_data(), year, month)
if recent.empty:
    st.info("Ei merkintöjä valitulle kuukaudelle.")
else:
    x = pd.to_datetime(recent["Päivä"])
    fig, ax1 = plt.subplots(figsize=(8,4))

    # Uni vasen akseli
    ax1.set_xlabel("Päivä")
    ax1.set_ylabel("Uni (h)")
    ax1.plot(x, recent["Uni_h"], marker="o", label="Uni (h)")
    ax1.set_ylim(0, 12)

    # Oikea akseli: mieliala & stressi
    ax2 = ax1.twinx()
    ax2.set_ylabel("Mieliala (1–5) / Stressi (0–10)")
    ax2.plot(x, recent["Mieliala"]*2, marker="s", label="Mieliala (×2)")  # skaalaa 1–5 → 0–10
    ax2.plot(x, recent["Stressi"], marker="^", label="Stressi")
    ax2.set_ylim(0, 10)

    # Yhteinen legenda
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    fig.legend(lines1 + lines2, labels1 + labels2, loc="upper left", bbox_to_anchor=(0.08, 1.0))
    plt.xticks(rotation=45)

    st.pyplot(fig)


st.dataframe(load_data())

# Tarjoa latausmahdollisuus CSV:nä
csv = load_data().to_csv(index=False).encode("utf-8")
st.download_button("Lataa CSV", csv, "mieliuni_data.csv", "text/csv")

st.divider()

# ---------- Data & näkymät ----------
df = load_data()

# Kuukausivalinta
today = date.today()
col1, col2 = st.columns(2)
with col1:
    year = st.number_input("Vuosi", min_value=2000, max_value=2100, value=today.year, step=1)
with col2:
    month = st.selectbox("Kuukausi", list(range(1,13)), index=today.month-1)

recent = filter_month(df, year, month)

st.subheader(f"📈 Uni, Mieliala & Stressi ({month:02d}/{year})")
if recent.empty:
    st.info("Ei merkintöjä valitulle kuukaudelle.")
else:
    x = pd.to_datetime(recent["Päivä"])
    fig, ax1 = plt.subplots(figsize=(8,4))

    # Uni vasen akseli
    ax1.set_xlabel("Päivä")
    ax1.set_ylabel("Uni (h)", color="blue")
    ax1.plot(x, recent["Uni_h"], marker="o", color="blue", label="Uni (h)")
    ax1.tick_params(axis="y", labelcolor="blue")

    # Oikea akseli: mieliala & stressi
    ax2 = ax1.twinx()
    ax2.set_ylabel("Mieliala/Stressi (0–10)", color="black")
    ax2.plot(x, recent["Mieliala_0_10"], marker="s", color="green", label="Mieliala")
    ax2.plot(x, recent["Stressi_0_10"], marker="^", color="red", label="Stressi")
    ax2.set_ylim(0, 10)
    ax2.tick_params(axis="y", labelcolor="black")

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    fig.legend(lines + lines2, labels + labels2, loc="upper left", bbox_to_anchor=(0.08,0.95))
    plt.xticks(rotation=45)
    plt.title(f"Uni, Mieliala & Stressi ({month:02d}/{year})")
    st.pyplot(fig)

    df = load_data()
kuukauden = filter_month(df, year, month)

st.subheader("📊 Kuukauden keskiarvot")
if kuukauden.empty:
    st.info("Ei merkintöjä valitulle kuukaudelle.")
else:
    st.json({
        "Merkintöjä": int(len(kuukauden)),
        "Uni (h)": round(kuukauden["Uni_h"].mean(), 2),
        "Mieliala": round(kuukauden["Mieliala"].mean(), 2),  # 1–5
        "Stressi": round(kuukauden["Stressi"].mean(), 2),    # 0–10
    })

    })

# Huomiot
st.subheader("📝 Huomiot")
if recent.empty:
    st.write("Ei merkintöjä.")
else:
    for _, row in recent.iterrows():
        with st.expander(f"{row['Päivä']} — Uni {row['Uni_h']} h | Mieliala {row['Mieliala_0_10']} | Stressi {row['Stressi_0_10']}"):
            st.write(row["Huomiot"] if row["Huomiot"] else "_(ei merkintää)_")

# Taulukko ja CSV-lataus
st.subheader("📋 Kaikki merkinnät")
if df.empty:
    st.write("—")
else:
    dff = df.sort_values("Päivä", ascending=False).reset_index(drop=True)
    st.dataframe(dff, use_container_width=True)
    csv = dff.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Lataa CSV", csv, "mieli_uni_data.csv", "text/csv")# Piirretään graafit
st.subheader("📈 Mieliala ja stressi ajan mittaan")

# Valitaan vain halutut sarakkeet
st.subheader("📈 Mieliala ja stressi ajan mittaan")
df = load_data()
if df.empty:
    st.info("Ei vielä dataa kuvaajaan.")
else:
    dff = df.copy()
    dff["Päivä"] = pd.to_datetime(dff["Päivä"])
    dff = dff.sort_values("Päivä")

    # Näytetään viivakaaviona Uni, Mieliala ja Stressi
    st.line_chart(dff.set_index("Päivä")[["Uni_h", "Mieliala", "Stressi"]])
















