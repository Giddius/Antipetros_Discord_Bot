import os


with open('actions_check_output.txt', 'w') as f:
    for dirname, folderlist, filelist in os.walk(os.getcwd()):
        for file in filelist:
            path = os.path.relpath(os.path.join(dirname, file))
            f.write(f"- '{path}'")
            f.write('\n')
