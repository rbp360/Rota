import pandas as pd
import os

file_path = r"c:\Users\rob_b\Rota\GV cover and staff absence.xlsx"

def extract_sample():
    try:
        xl = pd.ExcelFile(file_path)
        sheet_names = xl.sheet_names
        print(f"Sheets found: {sheet_names}")
        
        # Take the first teacher sheet (assuming index 1 is a teacher)
        sheet_name = sheet_names[1]
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Save a portion to CSV
        output_path = "sample_sheet.csv"
        df.iloc[:30, :15].to_csv(output_path)
        print(f"Sample saved to {output_path}")
        
        # Also save column names and first few rows as text
        with open("sheet_info.txt", "w") as f:
            f.write(f"Sheet Name: {sheet_name}\n")
            f.write(f"Columns: {df.columns.tolist()}\n")
            f.write("-" * 20 + "\n")
            f.write(df.iloc[:10, :10].to_string())
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    extract_sample()
