import requests
import pandas as pd
import time
import os

BOT_TOKEN = os.getenv("AAEqWTrMPmQP2XaT60_iYVg4Zl_GVajGbUc")
CHAT_ID = os.getenv("8562049589")

URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}

def send_telegram(msg):
    api = f"https://api.telegram.org/bot{AAEqWTrMPmQP2XaT60_iYVg4Zl_GVajGbUc}/sendMessage"
    requests.post(api, data={"chat_id": 8562049589, "text": msg})

def get_data():
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)
    res = session.get(URL, headers=headers)
    data = res.json()
    return data["records"]["data"], data["records"]["underlyingValue"]

try:
    prev_df = pd.read_csv("prev_oi.csv")
except:
    prev_df = pd.DataFrame(columns=["strike", "CE_OI", "PE_OI"])

while True:
    try:
        option_data, spot = get_data()
        alerts = []
        current = []

        for row in option_data:
            strike = row["strikePrice"]

            # Only ATM ±500 strikes
            if abs(strike - spot) > 500:
                continue

            ce_oi = row.get("CE", {}).get("openInterest", 0)
            pe_oi = row.get("PE", {}).get("openInterest", 0)

            current.append([strike, ce_oi, pe_oi])

            prev = prev_df[prev_df["strike"] == strike]
            if not prev.empty:
                prev_ce = prev["CE_OI"].values[0]
                prev_pe = prev["PE_OI"].values[0]

                if prev_ce > 0:
                    ce_change = ((ce_oi - prev_ce) / prev_ce) * 100
                    if ce_change > 400:
                        alerts.append(f"🚨 CE OI Spike >400% | Strike {strike} | {ce_change:.1f}%")

                if prev_pe > 0:
                    pe_change = ((pe_oi - prev_pe) / prev_pe) * 100
                    if pe_change > 400:
                        alerts.append(f"🚨 PE OI Spike >400% | Strike {strike} | {pe_change:.1f}%")

        if alerts:
            send_telegram("\n".join(alerts))

        pd.DataFrame(current, columns=["strike", "CE_OI", "PE_OI"]).to_csv("prev_oi.csv", index=False)

        time.sleep(60)

    except Exception as e:
        print(e)
        time.sleep(30)