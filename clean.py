import shutil
import os

if os.path.exists("./dest"):
    shutil.rmtree("./dest")
    print("Task: Cache folder cleaned!")
else:
    print("Error: Folder doesn't exist.")