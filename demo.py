"""
ASGARD Dashboard - Data Processor Demo
This script demonstrates the data processor with the provided Excel file
"""

from data_processor import DataProcessor
import pandas as pd
import json

print("=" * 70)
print("ASGARD Alliance Dashboard - Data Processor Demo")
print("=" * 70)

# Initialize processor
processor = DataProcessor()

# Process the Excel file
print("\n📂 Processing: ASG Contribution and cp check.xlsx\n")
result = processor.process_excel_file('ASG Contribution and cp check.xlsx')

# Display results
print("✅ Processing Complete!\n")

print("-" * 70)
print("SUMMARY")
print("-" * 70)

print(f"\n📊 Total Members: {len(result.common_sheet)}")
print(f"📑 Raw Sheets Processed: {len(result.raw_sheets)}")
print(f"📈 Week Sections Found: {len(result.week_sheets)}")

if result.errors:
    print(f"\n⚠️  Processing Errors: {len(result.errors)}")
    for err in result.errors:
        print(f"   - {err}")
else:
    print("\n✨ No errors during processing!")

print("\n" + "-" * 70)
print("COMMON SHEET (First 10 Members)")
print("-" * 70)
print(result.common_sheet.head(10).to_string())

print("\n" + "-" * 70)
print("ANALYTICS SUMMARY")
print("-" * 70)
print(f"\n📊 Total Duel Score: {result.analytics.get('total_duel', 0):,.2f}")
print(f"🧪 Total Tech Score: {result.analytics.get('total_tech', 0):,.2f}")
print(f"🚀 Total CP Growth: {result.analytics.get('total_cp_growth', 0):,.2f}")

print("\n" + "-" * 70)
print("BOTTOM 20 PERFORMERS (First 5)")
print("-" * 70)

bottom_20 = result.analytics.get('bottom_20', [])
for i, member in enumerate(bottom_20[:5], 1):
    print(f"\n{i}. {member['Member']}")
    print(f"   Duel: {member.get('TotalDuel', 0):.2f} | Tech: {member.get('TotalTech', 0):.0f} | CP: {member.get('CP_23d_Growth', 0):.2f}")
    print(f"   Combined Score: {member.get('CombinedScore', 0):.0f}")

print("\n" + "-" * 70)
print("TOP 10 DUEL PERFORMERS (First 5)")
print("-" * 70)

top_duel = result.analytics.get('top_duel', [])
for i, member in enumerate(top_duel[:5], 1):
    print(f"{i}. {member['Member']:20s} - {member.get('TotalDuel', 0):10.2f}")

print("\n" + "-" * 70)
print("TOP 10 TECH PERFORMERS (First 5)")
print("-" * 70)

top_tech = result.analytics.get('top_tech', [])
for i, member in enumerate(top_tech[:5], 1):
    print(f"{i}. {member['Member']:20s} - {member.get('TotalTech', 0):10.0f}")

print("\n" + "-" * 70)
print("LOWEST 10 DUEL PERFORMERS (First 5)")
print("-" * 70)

lowest_duel = result.analytics.get('lowest_duel', [])
for i, member in enumerate(lowest_duel[:5], 1):
    print(f"{i}. {member['Member']:20s} - {member.get('TotalDuel', 0):10.2f}")

print("\n" + "-" * 70)
print("LOWEST 10 TECH PERFORMERS (First 5)")
print("-" * 70)

lowest_tech = result.analytics.get('lowest_tech', [])
for i, member in enumerate(lowest_tech[:5], 1):
    print(f"{i}. {member['Member']:20s} - {member.get('TotalTech', 0):10.0f}")

print("\n" + "-" * 70)
print("COMMON SHEET COLUMNS")
print("-" * 70)
print("\n".join(result.common_sheet.columns.tolist()))

print("\n" + "-" * 70)
print("WEEK SHEETS AVAILABLE")
print("-" * 70)
for week_name in result.week_sheets.keys():
    shape = result.week_sheets[week_name].shape
    print(f"  {week_name}: {shape[0]} rows × {shape[1]} columns")

print("\n" + "=" * 70)
print("✅ Data processor demo complete!")
print("=" * 70)
print("\nTo start the dashboard:")
print("  1. Run: python flask_app.py")
print("  2. Open: http://localhost:5000")
print("  3. Upload your Excel file")
print("\n")
