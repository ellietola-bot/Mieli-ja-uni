import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import date

# ------------------ ASETUKSET ------------------
DATA_PATH = Path("data.csv")
COLUMNS = ["Päivä", "Uni_h", "Mieliala", "Stressi", "Huomiot"]

# ------------------ DATA-APUT ------------------
def load_data() -> pd.DataFrame:
    """Lataa CSV:n, varmistaa sarakkeet ja muuntaa tyypit."""
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH)

        # Luo puuttuvat sarakkeet
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None

        # Migraatiot vanhoista sarakkeista (jos löytyvät)
        if "Mieliala_0_10" in df.columns and df["Mieliala"].isna().all():
            df["Mieliala"] = (
                pd.to_numeric(df["Mieliala_0_10"], errors="coerce") / 2
            ).round().clip(1, 5)

        if "Stressi_0_10" in df.columns and df["Stressi"].isna().all():
            df["Stressi"] = pd.to_numeric(df["Stressi_0_10"], errors="coerce").clip(0, 10)

        # Päivä päivämääräksi, palauta vain halutut sarakkeet
        df["Päivä"] = pd.to_datetime(df["Päivä"], errors="coerce").dt.date
        df = df[COLUMNS]
        return df.dropna(subset=["Päivä"]).reset_index(drop=True)

    return pd.DataFrame(columns=COLUMNS)


def filter_month(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    """Suodata kuukauden rivit."""
    if df.empty:
        return df
    s = pd.to_datetime(df["Päivä"], errors="coerce")
    out = df[(s.dt.year == year) & (s.dt.month == month)].copy()
    return out.sort_values("Päivä").reset_index(drop=True)


def save_row(row: dict) -> pd.DataFrame:
    """Lisää tai korvaa rivin saman Päivä-arvon perusteella ja tallenna CSV."""
    df = load_data()
    mask = df["Päivä"] == row["Päivä"]
    if mask.any():
        df.loc[mask, COLUMNS] = [row.get(c) for c in COLUMNS]
    else:
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)
    return df

# ------------------ UI: SYÖTTÖLOMAKE ------------------
st.title("Uni ja mieliala")
st.caption("Seuraa unta, mielialaa ja stressiä. Data pysyy vain tällä koneella (data.csv).")

with st.form("entry"):
    col1, col2 = st.columns(2)

    with col1:
        paiva = st.date_input("Päivä", value=date.today(), format="DD.MM.YYYY")
        uni = st.slider("Uni (tuntia)", min_value=0.0, max_value=12.0, value=7.5, step=0.5)

        # Mieliala emojit (tehdään napit ilmaviksi)
        st.markdown(
            """
            <style>
            div.row-widget.stRadio > div { flex-direction: row; justify-content: space-around; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        moods = ["😞", "😕", "😐", "🙂", "🤩"]
        mieliala = st.radio("Mieliala", moods, index=2, horizontal=True)
        mood_map = {"😞": 1, "😕": 2, "😐": 3, "🙂": 4, "🤩": 5}
        mieliala_num = mood_map[mieliala]
        st.write("Valitsit:", mieliala, "→ arvo", mieliala_num)

    with col2:
        stressi = st.slider("Stressi (0–10)", 0, 10, 5)
        huomiot = st.text_area("Huomiot", placeholder="esim. flunssa, lääkitys, painajaisia…")
        submitted = st.form_submit_button("💾 Tallenna")

if submitted:
    save_row({
        "Päivä": paiva,
        "Uni_h": float(uni),
        "Mieliala": int(mieliala_num),  # 1–5
        "Stressi": int(stressi),        # 0–10
        "Huomiot": huomiot.strip(),
    })
    st.success("Tallennettu!")

st.divider()

# ------------------ DATA & NÄKYMÄT ------------------
df = load_data()

# Kuukausivalinta kaavioita/tilastoja varten
today = date.today()
cc1, cc2 = st.columns(2)
with cc1:
    year = st.number_input("Vuosi", min_value=2000, max_value=2100, value=today.year, step=1)
with cc2:
    month = st.selectbox("Kuukausi", list(range(1, 13)), index=today.month - 1)

recent = filter_month(df, year, month)

# C) Kaavio: Uni vasen, Mieliala×2 & Stressi oikea
st.subheader(f"📈 Uni, Mieliala & Stressi ({month:02d}/{year})")
if recent.empty:
    st.info("Ei merkintöjä valitulle kuukaudelle.")
else:
    x = pd.to_datetime(recent["Päivä"])
    fig, ax1 = plt.subplots(figsize=(8, 4))

    # Uni vasen akseli
    ax1.set_xlabel("Päivä")
    ax1.set_ylabel("Uni (h)")
    ax1.plot(x, recent["Uni_h"], marker="o", label="Uni (h)")
    ax1.set_ylim(0, 12)

    # Oikea akseli: mieliala & stressi
    ax2 = ax1.twinx()
    ax2.set_ylabel("Mieliala (1–5) / Stressi (0–10)")
    ax2.plot(x, recent["Mieliala"] * 2, marker="s", label="Mieliala (×2)")  # skaalaa 1–5 → 0–10
    ax2.plot(x, recent["Stressi"], marker="^", label="Stressi")
    ax2.set_ylim(0, 10)

    # Yhteinen legenda
    l1, lab1 = ax1.get_legend_handles_labels()
    l2, lab2 = ax2.get_legend_handles_labels()
    fig.legend(l1 + l2, lab1 + lab2, loc="upper left", bbox_to_anchor=(0.08, 1.0))
    plt.xticks(rotation=45)

    st.pyplot(fig)

# Kuukauden keskiarvot
st.subheader("📊 Kuukauden keskiarvot")
if recent.empty:
    st.info("Ei merkintöjä valitulle kuukaudelle.")
else:
    st.json({
        "Merkintöjä": int(len(recent)),
        "Uni (h)": round(recent["Uni_h"].mean(), 2),
        "Mieliala": round(recent["Mieliala"].mean(), 2),  # 1–5
        "Stressi": round(recent["Stressi"].mean(), 2),    # 0–10
    })

# Huomiot
st.subheader("📝 Huomiot")
if recent.empty:
    st.write("Ei merkintöjä.")
else:
    for _, row in recent.iterrows():
        with st.expander(f"{row['Päivä']} — Uni {row['Uni_h']} h | Mieliala {row['Mieliala']} | Stressi {row['Stressi']}"):
            st.write(row["Huomiot"] if row["Huomiot"] else "_(ei merkintää)_")

# Kaikki merkinnät & CSV
st.subheader("📋 Kaikki merkinnät")
if df.empty:
    st.write("—")
else:
    dff = df.sort_values("Päivä", ascending=False).reset_index(drop=True)
    st.dataframe(dff, use_container_width=True)
    csv = dff.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Lataa CSV", csv, "mieli_uni_data.csv", "text/csv")
