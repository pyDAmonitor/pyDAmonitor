import numpy as np
from DAmonitor.base import to_dataframe


def fit_rate(data):
    df = to_dataframe(data)

    # 1. Filter valid data (both 'oman' and 'ombg' are not NaN)
    valid_df = df[df["oman"].notna() & df["ombg"].notna()].copy()
    valid_df = valid_df.dropna(subset=["height"])  # removes any rows in valid_df where height is missing (NaN)

    # 2. Compute overall RMS and fit_rate
    bias_a = valid_df["oman"].mean()
    bias_b = valid_df["ombg"].mean()
    rms_a = np.sqrt((valid_df["oman"]**2).mean())
    rms_b = np.sqrt((valid_df["ombg"]**2).mean())
    fit_rate_overall = (rms_b - rms_a) / rms_b
    print(f"OMA: bias={bias_a:.4f} rms={rms_a:.4f}")
    print(f"OMB: bias={bias_b:.4f} rms={rms_b:.4f}")
    print(f"Overall fit_rate: {fit_rate_overall:.4%}")

    # 3. Bin data by height every dz meters
    dz = 1000
    valid_df["height_bin"] = (valid_df["height"] // dz) * dz  # floor to nearest 1000

    # 4. Group by height_bin and compute RMS and fit_rate
    grouped = valid_df.groupby("height_bin").agg({
        "oman": lambda x: np.sqrt(np.mean(x**2)),
        "ombg": lambda x: np.sqrt(np.mean(x**2))
    }).rename(columns={"oman": "rms_a", "ombg": "rms_b"})

    grouped["fit_rate"] = (grouped["rms_b"] - grouped["rms_a"]) / grouped["rms_b"]
    grouped = grouped.reset_index()  # reset the groupby column "height" from index to normal columns
    for idx, row in grouped.iterrows():
        print(f"{idx}, {row['height_bin']:.0f}, {row['rms_a']:.4f}, {row['rms_b']:.4f}, {row['fit_rate']:.4%}")

    return grouped  # data frame
