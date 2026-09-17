from src.analysis.load_features import load_feature_range


df = load_feature_range(
    symbol="NVDA",
    start_date="2026-08-17",
    end_date="2026-08-21"
)

print(df.shape)
print(df.head())
print(df["date"].value_counts().sort_index())
