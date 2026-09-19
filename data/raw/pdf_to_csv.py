"""
Convert the assignment's Google-Sheets PDF export ("Consumption Dataset") into data/raw/bar_inventory_data.csv.

Why the repair step exists: the PDF prints some balance cells in rounded scientific notation
(3 significant digits, e.g. 2.30E+03) and floating-point residuals (e.g. 5.68E-14 = 0). Purchase and Consumed are
always printed exactly and the balances satisfy  Closing = Opening + Purchase - Consumed  and  Opening = previous Closing,
so every rounded balance is reconstructed EXACTLY from the exact cells of the same bar-brand chain.

Requires poppler's `pdftotext`  (macOS: brew install poppler).
Usage:  python pdf_to_csv.py "Consumption_Dataset_-_Dataset.pdf" bar_inventory_data.csv
"""
import re, subprocess, sys
import numpy as np
import pandas as pd

NUM = r"-?\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?"
ROW = re.compile(rf"^\s*(\d{{1,2}}/\d{{1,2}}/\d{{4}}\s+\d{{1,2}}:\d{{2}})\s+([A-Za-z]+'s Bar)\s+([A-Za-z]+)\s+(.+?)\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})\s*$")

def parse(pdf):
    text = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout
    rows = []
    for line in text.split("\n"):
        m = ROW.match(line)
        if m:
            rows.append([m.group(1), m.group(2), m.group(3), re.sub(r"\s+", " ", m.group(4)).strip()] + [m.group(i) for i in range(5, 9)])
    df = pd.DataFrame(rows, columns=["ts", "bar", "type", "brand", "open_s", "purch_s", "cons_s", "close_s"])
    for c in ["open", "purch", "cons", "close"]:
        df[c] = df[c + "_s"].astype(float)
    tiny_o, tiny_c = df.open.abs() < 1e-6, df.close.abs() < 1e-6                     # floating-point residuals = 0
    df["rnd_o"] = df.open_s.str.contains("E", case=False) & ~tiny_o                  # rounded to 3 significant digits
    df["rnd_c"] = df.close_s.str.contains("E", case=False) & ~tiny_c
    df["zero_o"], df["zero_c"] = tiny_o, tiny_c
    df["dt"] = pd.to_datetime(df.ts, format="%m/%d/%Y %H:%M")
    return df.sort_values(["bar", "brand", "dt"]).reset_index(drop=True)

def repair(df):
    out, fixed = [], 0
    for _, g in df.groupby(["bar", "brand"], sort=False):
        g = g.reset_index(drop=True); n = len(g)
        cum = np.concatenate([[0.0], np.cumsum((g.purch - g.cons).values)])          # b_i - b_0, boundary balances b_0..b_n
        est = []                                                                      # every exact cell gives an estimate of b_0
        for i in range(n):
            if g.zero_o[i]: est.append(0.0 - cum[i])
            elif not g.rnd_o[i]: est.append(g.open[i] - cum[i])
            if g.zero_c[i]: est.append(0.0 - cum[i + 1])
            elif not g.rnd_c[i]: est.append(g.close[i] - cum[i + 1])
        assert est, "no exact anchor in a series"
        b = np.median(est) + cum; b[np.abs(b) < 1e-6] = 0.0
        fixed += int(g.rnd_o.sum() + g.rnd_c.sum())
        g["open_fix"], g["close_fix"] = np.round(b[:-1], 2), np.round(b[1:], 2)
        out.append(g)
    print(f"reconstructed {fixed} rounded balance cells from exact flows")
    return pd.concat(out).sort_values(["dt", "bar", "brand"]).reset_index(drop=True)

if __name__ == "__main__":
    pdf, out_csv = sys.argv[1], sys.argv[2]
    r = repair(parse(pdf))
    final = pd.DataFrame({"Date Time Served": r.dt.dt.strftime("%Y-%m-%d %H:%M:%S"), "Bar Name": r.bar, "Alcohol Type": r.type, "Brand Name": r.brand,
                          "Opening Balance (ml)": r.open_fix, "Purchase (ml)": r.purch, "Consumed (ml)": r.cons, "Closing Balance (ml)": r.close_fix})
    resid = (final["Closing Balance (ml)"] - (final["Opening Balance (ml)"] + final["Purchase (ml)"] - final["Consumed (ml)"])).abs().max()
    print(f"{len(final):,} rows | conservation residual max {resid:.2e}")
    final.to_csv(out_csv, index=False)
