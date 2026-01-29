import openpyxl
import os

file_path = r"c:\Users\rob_b\Rota\GV cover and staff absence.xlsx"

def list_sheets(path):
    try:
        wb = openpyxl.load_workbook(path, read_only=True)
        print(f"Sheet names: {wb.sheetnames}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_sheets(file_path)
