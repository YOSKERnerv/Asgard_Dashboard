"""Debug the duel sheet processing"""
from data_processor import DataProcessor
import pandas as pd

processor = DataProcessor()

# Load duel sheet
duel_raw = pd.read_excel('ASG Contribution and cp check.xlsx', sheet_name='Alliance duel')

# Try to process it
duel_df, duel_weeks = processor.process_alliance_duel_sheet(duel_raw)

print("Duel Processing Result:")
print(f"  Errors: {processor.errors}")
print(f"  Duel DF Shape: {duel_df.shape}")
print(f"  Duel DF Columns: {list(duel_df.columns) if len(duel_df) > 0 else 'No columns'}")
print(f"\nFirst 5 rows:")
print(duel_df.head(10).to_string())
