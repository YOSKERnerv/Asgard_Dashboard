import pandas as pd

xls = pd.ExcelFile('ASG Contribution and cp check.xlsx')
print("Sheet names:")
for i, name in enumerate(xls.sheet_names):
    print(f"  {i}: {name}")

for i, name in enumerate(xls.sheet_names):
    print(f"\n\n{'='*60}")
    print(f"Sheet {i}: {name}")
    print('='*60)
    df = pd.read_excel('ASG Contribution and cp check.xlsx', sheet_name=name)
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print("\nFirst 10 rows:")
    print(df.head(10).to_string())
