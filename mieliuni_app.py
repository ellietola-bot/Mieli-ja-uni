import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from pathlib import Path

st.set_page_config(page_title="Mieli & Uni", page_icon="😴", layout="centered")

DATA_PATH = Path("data.csv")
COLUMNS = ["Päivä","Uni_h","Mieliala_0_10","Stressi_0_10","Huomiot"]

# ---------- Helpers ----------
def load_data():
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None
        df = df[COLUMNS]
        df["Päivä"] = pd.to_datetime(df["Päivä"]).dt.date
        return df.dropna(subset=["Päivä"])
    return pd.DataFrame(columns=COLUMNS)

def save_row(row):
    df = load_data()
    mask = df["Päivä"] == row["Päivä"]
    if mask.any():
        df.loc[mask, :] = list(row.values())
    else:
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)

def filter_month(df, year, month):
    if df.empty:
        return df
    return df[(pd.to_datetime(df["Päivä"]).dt.year == year) &
              (pd.to_datetime(df["Päivä"]).dt.month == month)].sort_values("Päivä")

# ---------- UI: Syöttölomake ----------
st.title("😴 Mieli & Uni – oma seuranta")
st.caption("Seuraa unta, mielialaa ja stressiä. Data pysyy vain tällä koneella (data.csv).")

with st.form("entry"):
    col1, col2 = st.columns(2)
    with col1:
        paiva = st.date_input("Päivä", value=date.today(), format="DD.MM.YYYY")
        uni = st.slider("Uni (tuntia)", min_value=0.0, max_value=12.0, value=7.5, step=0.5)
        mieliala = st.slider("Mieliala (0–10)", 0, 10, 5)
    with col2:
        stressi = st.slider("Stressi (0–10)", 0, 10, 5)
        huomiot = st.text_area("Huomiot", placeholder="esim. flunssa, lääkitys, painajaisia…")
    submitted = st.form_submit_button("💾 Tallenna")

if submitted:
    save_row({
        "Päivä": paiva,
        "Uni_h": float(uni),
        "Mieliala_0_10": int(mieliala),
        "Stressi_0_10": int(stressi),
        "Huomiot": huomiot.strip(),
    })
    st.success("Tallennettu!")

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

    # Keskiarvot
    st.subheader("📊 Kuukauden keskiarvot")
    st.write({
        "Merkintöjä": len(recent),
        "Uni (h)": round(recent["Uni_h"].mean(),2),
        "Mieliala": round(recent["Mieliala_0_10"].mean(),2),
        "Stressi": round(recent["Stressi_0_10"].mean(),2),
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
chart_data = data[["Päivä", "Mieliala", "Stressi"]]

# Tehdään Päivä-sarakkeesta index (näyttää nätimmin x-akselilla)
chart_data = chart_data.set_index("Päivä")

# Näytetään kaavio
st.line_chart(chart_data)


