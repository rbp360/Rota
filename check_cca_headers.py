
import openpyxl
import os

EXCEL_PATH = r"c:\Users\rob_b\Rota\temp_rota.xlsx"

def inspect_cca_headers():
    if not os.path.exists(EXCEL_PATH):
        print("File not found.")
        return
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    sheet = wb["CCA"]
    for row in sheet.iter_rows(max_row=5, values_only=True):
        print(row)

if __name__ == "__main__":
    inspect_cca_headers()
