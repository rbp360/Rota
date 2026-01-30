
import openpyxl
import os

def check_layout():
    wb = openpyxl.load_workbook(r"c:\Users\rob_b\Rota\temp_rota.xlsx", data_only=True)
    sheet = wb["CCA"]
    with open("cca_final_debug.txt", "w") as f:
        for r_idx, row in enumerate(sheet.iter_rows(max_row=20, values_only=True)):
            f.write(f"R{r_idx+1}: {row}\n")

if __name__ == "__main__":
    check_layout()
