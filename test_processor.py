"""Quick test of the data processor"""
from data_processor import DataProcessor
import json

processor = DataProcessor()
result = processor.process_excel_file('ASG Contribution and cp check.xlsx')

print("=" * 60)
print("PROCESSING RESULTS")
print("=" * 60)

print(f"\nErrors: {result.errors}")
print(f"Common Sheet Shape: {result.common_sheet.shape}")
print(f"Common Sheet Columns: {list(result.common_sheet.columns)}")
print(f"\nFirst 5 members:")
print(result.common_sheet.head(5).to_string())

print(f"\n\nWeek Sheets: {list(result.week_sheets.keys())}")
for week_name, df in result.week_sheets.items():
    print(f"\n{week_name}: {df.shape}")

print(f"\n\nAnalytics Keys: {list(result.analytics.keys())}")
print(f"\nBottom 20 Performers:")
print(json.dumps(result.analytics.get('bottom_20', [])[:5], indent=2))

print(f"\nLowest Duel Contributors:")
print(json.dumps(result.analytics.get('lowest_duel', [])[:5], indent=2))
