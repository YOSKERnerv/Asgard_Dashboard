"""
ASGARD Dashboard - System Verification Script
Checks all components and dependencies are correctly installed
"""

import sys
import os
import subprocess

print("=" * 70)
print("ASGARD Alliance Dashboard - System Verification")
print("=" * 70)
print()

checks_passed = 0
checks_total = 0

def check(description, test_func):
    global checks_passed, checks_total
    checks_total += 1
    
    try:
        result = test_func()
        if result:
            print(f"✅ {description}")
            checks_passed += 1
            return True
        else:
            print(f"❌ {description}")
            return False
    except Exception as e:
        print(f"❌ {description} - Error: {str(e)}")
        return False

# Check Python version
def check_python():
    return sys.version_info >= (3, 8)

# Check Flask
def check_flask():
    try:
        import flask
        return True
    except:
        return False

# Check pandas
def check_pandas():
    try:
        import pandas
        return True
    except:
        return False

# Check openpyxl
def check_openpyxl():
    try:
        import openpyxl
        return True
    except:
        return False

# Check Flask-CORS
def check_cors():
    try:
        import flask_cors
        return True
    except:
        return False

# Check data processor
def check_processor():
    return os.path.exists('data_processor.py')

# Check Flask app
def check_flask_app():
    return os.path.exists('flask_app.py')

# Check templates
def check_templates():
    return os.path.exists('templates/dashboard.html')

# Check Excel file
def check_excel():
    return os.path.exists('ASG Contribution and cp check.xlsx')

# Check requirements.txt
def check_requirements():
    return os.path.exists('requirements.txt')

# Test data processor
def test_processor():
    try:
        from data_processor import DataProcessor
        processor = DataProcessor()
        result = processor.process_excel_file('ASG Contribution and cp check.xlsx')
        return len(result.common_sheet) > 0
    except:
        return False

# Test Flask app import
def test_flask_import():
    try:
        from flask_app import app
        return True
    except:
        return False

print("📋 PYTHON & DEPENDENCIES")
print("-" * 70)
check(f"Python {sys.version_info.major}.{sys.version_info.minor}+", check_python)
check("Flask installed", check_flask)
check("Pandas installed", check_pandas)
check("OpenPyXL installed", check_openpyxl)
check("Flask-CORS installed", check_cors)

print()
print("📁 PROJECT FILES")
print("-" * 70)
check("data_processor.py exists", check_processor)
check("flask_app.py exists", check_flask_app)
check("templates/dashboard.html exists", check_templates)
check("requirements.txt exists", check_requirements)
check("Excel data file exists", check_excel)

print()
print("🧪 FUNCTIONALITY TESTS")
print("-" * 70)
check("Data processor imports", test_flask_import)
check("Flask app initializes", test_flask_import)
check("Excel file processes", test_processor)

print()
print("=" * 70)
print(f"RESULTS: {checks_passed}/{checks_total} checks passed")
print("=" * 70)

if checks_passed == checks_total:
    print()
    print("✅ ALL CHECKS PASSED!")
    print()
    print("You're ready to start the dashboard:")
    print()
    print("  1. Run:  python flask_app.py")
    print("  2. Open: http://localhost:5000")
    print()
    sys.exit(0)
else:
    missing = checks_total - checks_passed
    print()
    print(f"❌ {missing} check(s) failed!")
    print()
    print("To fix missing dependencies, run:")
    print("  pip install -r requirements.txt")
    print()
    sys.exit(1)
