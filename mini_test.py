import openpyxl
import sys

try:
    path = r"c:\Users\rob_b\Rota\GV cover and staff absence.xlsx"
    print(f"Loading {path}...")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    print(f"Sheet names: {wb.sheetnames}")
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
