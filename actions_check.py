import os


with open('actions_check_output.txt', 'w') as f:
    for file in os.scandir(os.getcwd()):
        f.write(file.path)
