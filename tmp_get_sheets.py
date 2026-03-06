import openpyxl
import json

wb = openpyxl.load_workbook('GV cover and staff absence.xlsx', read_only=True)
sheets = wb.sheetnames

with open('tmp_sheets.json', 'w') as f:
    json.dump(sheets, f)
