import os

with open('canary.txt', 'w') as f:
    f.write('Python is alive\n')
    f.write(f'Cwd: {os.getcwd()}\n')
