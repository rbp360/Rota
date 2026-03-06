import pandas as pd
import os
import openpyxl

file_path = r"c:\Users\rob_b\Rota\GV cover and staff absence.xlsx"

def find_alex_and_amanda():
    try:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet_names = wb.sheetnames
        print(f"Sheets: {sheet_names}")
        
        target_names = ["Alex", "Amanda"]
        found_sheets = {}
        
        for name in sheet_names:
            for target in target_names:
                if target.lower() in name.lower():
                    found_sheets[target] = name
        
        # If not found by name, we might need to search content, but let's check names first.
        print(f"Found sheets by mapping: {found_sheets}")
        
        for target, sheet_name in found_sheets.items():
            print(f"\n--- Extracting {target} (Sheet: {sheet_name}) ---")
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Look for Period 1
            print(f"Columns: {df.columns.tolist()[:10]}")
            # Identify first few rows to find where data starts
            info_file = f"info_{target}.txt"
            with open(info_file, "w", encoding='utf-8') as f:
                f.write(f"Sheet: {sheet_name}\n")
                f.write(df.iloc[:40, :15].to_string())
            print(f"Saved to {info_file}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_alex_and_amanda()
