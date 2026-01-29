import pandas as pd
import json
import ospath = r"c:\Users\rob_b\Rota\GV cover and staff absence.xlsx"

def analyze_excel(file_path):
    try:
        xl = pd.ExcelFile(file_path)
        print(f"Sheets: {xl.sheet_names}")
        
        analysis = {}
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            analysis[sheet_name] = {
                "columns": df.columns.tolist(),
                "head": df.head(5).to_dict()
            }
            print(f"Sheet: {sheet_name}")
            print(f"Columns: {df.columns.tolist()}")
            print("-" * 20)
            
        with open("excel_analysis.json", "w") as f:
            json.dump(analysis, f, indent=4, default=str)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_excel(ospath)
