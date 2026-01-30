
import openpyxl
import os
import sys

EXCEL_PATH = r"c:\Users\rob_b\Rota\temp_rota.xlsx"

def inspect():
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    sheet = wb["CCA"]
    for r in range(1, 11):
        row_vals = []
        for c in range(1, 15):
            row_vals.append(str(sheet.cell(row=r, column=c).value))
        print(f"R{r}: {' | '.join(row_vals)}")
    sys.stdout.flush()

if __name__ == "__main__":
    inspect()
