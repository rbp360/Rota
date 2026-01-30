
import openpyxl
import os

EXCEL_PATH = r"c:\Users\rob_b\Rota\temp_rota.xlsx"

def locate_staff():
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    sheet = wb["CCA"]
    staff_targets = ["Rosie", "Jayme", "Amanda", "Jayme", "Rosie"]
    
    print("Searching for staff/clubs...")
    for r_idx, row in enumerate(sheet.iter_rows(values_only=True)):
        for c_idx, val in enumerate(row):
            if not val: continue
            vs = str(val).lower()
            for t in staff_targets:
                if t.lower() in vs:
                    print(f"MATCH '{t}' at R{r_idx+1} C{c_idx+1}: {val}")
            if "eco action" in vs or "rock band" in vs:
                print(f"MATCH CLUB '{val}' at R{r_idx+1} C{c_idx+1}")

if __name__ == "__main__":
    locate_staff()
