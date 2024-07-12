import pandas as pd

def save_csv(name: str, data: pd.DataFrame):
    if len(data.index) > 0:
        data.to_csv(f"./output/{name}.csv", index=False, encoding="utf-8-sig")