import argparse
import json
from pathlib import Path

import pandas as pd


def load_and_clean_data(file_path: str) -> pd.DataFrame:
    path = Path(file_path)

    if path.suffix.lower() == ".xlsx":
        df = pd.read_excel(path)
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError("Supported file types: .xlsx, .csv")

    df = df.loc[:, ~df.columns.astype(str).str.contains(r"^Unnamed")]

    required = ["Location", "Sequence Number", "SSID", "MAC Address", "RSSI value"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df[required].copy()
    df["Location"] = df["Location"].astype(str).str.strip()
    df["MAC Address"] = df["MAC Address"].astype(str).str.strip().str.upper()
    df["RSSI value"] = pd.to_numeric(df["RSSI value"], errors="coerce")
    df["Sequence Number"] = pd.to_numeric(df["Sequence Number"], errors="coerce")

    df = df.dropna(subset=["Location", "MAC Address", "RSSI value", "Sequence Number"])
    df["Sequence Number"] = df["Sequence Number"].astype(int)

    return df


def build_reference(df: pd.DataFrame):
    reference = []

    grouped = df.groupby(["Location", "Sequence Number"])
    for (location, sequence_number), group in grouped:
        signals = (
            group.groupby("MAC Address")["RSSI value"]
            .mean()
            .to_dict()
        )

        reference.append({
            "location": location,
            "sequence_number": int(sequence_number),
            "signals": {str(k): float(v) for k, v in signals.items()},
        })

    return reference


def main():
    parser = argparse.ArgumentParser(description="Build sequence-based fingerprint reference")
    parser.add_argument("--input", required=True, help="Input dataset path")
    parser.add_argument("--output", default="backend/artifacts/reference_fingerprints.json", help="Output JSON path")
    args = parser.parse_args()

    df = load_and_clean_data(args.input)
    reference = build_reference(df)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(reference, f, indent=2)

    print(f"Saved {len(reference)} reference fingerprints to {output_path}")


if __name__ == "__main__":
    main()