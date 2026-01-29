import openpyxl
import os

try:
    print("Opening workbook...")
    wb = openpyxl.load_workbook(r"c:\Users\rob_b\Rota\GV cover and staff absence.xlsx", read_only=True)
    print(f"Sheets: {wb.sheetnames}")
except Exception as e:
    print(f"Error: {e}")
