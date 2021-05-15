import os


with open('actions_check_output.txt', 'w') as f:
    for file in os.scandir(os.getcwd()):
        f.write(f"- '{file.path}'")
        f.write('\n\n')
