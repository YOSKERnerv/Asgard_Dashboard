"""Debug the sheet processing"""
from data_processor import DataProcessor
import pandas as pd

processor = DataProcessor()

# Load and inspect raw sheets
xls = pd.ExcelFile('ASG Contribution and cp check.xlsx')
print("Raw sheets available:")
for sheet_name in xls.sheet_names:
    print(f"  - {sheet_name}")

# Load duel sheet
duel_raw = pd.read_excel('ASG Contribution and cp check.xlsx', sheet_name='Alliance duel')
print(f"\n\nDuel Sheet Shape: {duel_raw.shape}")
print(f"Duel Sheet Columns:\n{list(duel_raw.columns)}")

# Try to detect week sections
weeks = processor._detect_week_sections(duel_raw, 'duel')
print(f"\n\nDetected weeks in Duel sheet: {weeks}")

# Manually check for Members columns
member_cols = [c for c in duel_raw.columns if 'members' in c.lower()]
print(f"\nMember columns found: {member_cols}")
