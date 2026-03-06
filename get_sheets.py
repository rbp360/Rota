import openpyxl
wb = openpyxl.load_workbook('GV cover and staff absence.xlsx', read_only=True)
with open('sheets.txt', 'w') as f:
    for name in wb.sheetnames:
        f.write(name + '\n')
