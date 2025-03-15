import os
import shutil
import json
import stat
from datetime import datetime

with open("config.json", "r") as f:
    config = json.load(f)

USER_HOME = os.path.expanduser("~")
SOURCE = config["source"].replace("%USER_HOME%", USER_HOME)
DEST = config["destination"]

def create_backup():
    if not os.path.exists(DEST):
        os.makedirs(DEST)

timeTamp = datetime.now().strftime("%Y-%m-%d %H_%M_%S")
print(timeTamp)
backup_folder = os.path.join(DEST, f"backup_{timeTamp}")
os.makedirs(backup_folder)

for root, dirs, files in os.walk(SOURCE):
    relative_path = os.path.relpath(root, SOURCE)
    dest_path = os.path.join(backup_folder, relative_path)
    
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
    for file in files:
      file_source = os.path.join(root, file)
      file_dest = os.path.join(dest_path, file)
      shutil.copy2(file_source, file_dest)
      print(f"Копіюємо файли із {file_source} у {file_dest}")

zip_path = os.path.join(DEST, f"backup_{timeTamp}")
shutil.make_archive(zip_path, "zip", backup_folder)

def remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def safe_remove_folder(folder_path):
    try:
        shutil.rmtree(folder_path, onerror=remove_readonly)
        print(f"Папку {folder_path} успішно видалено")
    except Exception as e:
        print(f"Помилка при видаленні {folder_path}: {e}")


create_backup()
safe_remove_folder(backup_folder)
print("Операція завершена")