"""Debug the full pipeline"""
from data_processor import DataProcessor
import pandas as pd

processor = DataProcessor()

# Load all sheets
xls = pd.ExcelFile('ASG Contribution and cp check.xlsx')
duel_raw = pd.read_excel('ASG Contribution and cp check.xlsx', sheet_name='Alliance duel')
tech_raw = pd.read_excel('ASG Contribution and cp check.xlsx', sheet_name='Tech')
cp_raw = pd.read_excel('ASG Contribution and cp check.xlsx', sheet_name='CP check')

# Process each sheet
print("Processing Alliance Duel sheet...")
duel_df, duel_weeks = processor.process_alliance_duel_sheet(duel_raw)
print(f"  Result: {duel_df.shape}, Errors: {processor.errors}")

print("\nProcessing Tech sheet...")
tech_df, tech_weeks = processor.process_tech_sheet(tech_raw)
print(f"  Result: {tech_df.shape}, Errors: {processor.errors}")

print("\nProcessing CP sheet...")
cp_df = processor.process_cp_sheet(cp_raw)
print(f"  Result: {cp_df.shape}, Errors: {processor.errors}")

print(f"\nBefore merge:")
print(f"  Duel rows: {len(duel_df)}, Tech rows: {len(tech_df)}, CP rows: {len(cp_df)}")

# Test merge
print("\nMerging sheets...")
merged = processor.merge_sheets(duel_df, tech_df, cp_df)
print(f"  Result: {merged.shape}")
print(f"  Columns: {list(merged.columns)}")

print("\nFirst 5 merged rows:")
print(merged.head().to_string())

# Test analytics
print("\nGenerating analytics...")
try:
    analytics = processor.generate_analytics(merged.copy())
    print(f"  Success! Keys: {list(analytics.keys())}")
except Exception as e:
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()
