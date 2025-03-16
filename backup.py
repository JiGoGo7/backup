import os
import shutil
import json
import stat
import zipfile
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
    safe_remove_folder(backup_folder)

def remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def safe_remove_folder(folder_path):
    try:
        shutil.rmtree(folder_path, onerror=remove_readonly)
        print(f"Папку {folder_path} успішно видалено")
    except Exception as e:
        print(f"Помилка при видаленні {folder_path}: {e}")

def list_backups():
    backups = sorted(os.listdir(DEST), reverse = True)
    if not backups:
        print("Резервні копії відсутні")
        return[]
    
    for i, backup in enumerate(backups, 1):
        print(f"{i}. {backup}")

    return backups

def restore_backup():
    backups = list_backups()
    if not backups:
        return

    try:
        choice = int(input("Введіть номер резервної копії: ")) - 1
        if choice < 0 or choice >= len(backups):
            print("Такої копії не існує")
            return
    except ValueError:
        print("Введіть число!")
        return
        
    backup_folder = os.path.join(DEST, backups[choice])

    if backup_folder.endswith('.zip'):
        temp_extract_dir = os.path.join(DEST, f"temp_restore_{datetime.now().strftime('%Y-%m-%d_%H_%M_%S')}")
        os.makedirs(temp_extract_dir)
        
        with zipfile.ZipFile(backup_folder, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
        
        backup_folder = temp_extract_dir
    
    print(f"Відновлення файлів з {backup_folder} у {SOURCE}")

    for root, dirs, files in os.walk(backup_folder):
        relative_path = os.path.relpath(root, backup_folder)
        restore_path = os.path.join(SOURCE, relative_path)

        if not os.path.exists(restore_path):
            os.makedirs(restore_path)
        
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(restore_path, file)

            shutil.copy2(src_file, dest_file)
    safe_remove_folder(temp_extract_dir)
    print("Операція відновлення файлів завершена")

def main():
    print("Вітаю у програмі резервного копіювання файлів! Для початку виберіть дію:\n1. Створення резервної копії\n2. Відновлення файлів із уже існуючої резервної копії")

    try:
        choice = int(input("Введіть 1 або 2: "))
        if choice == 1:
            create_backup()
        elif choice == 2:
            restore_backup()
        else:
            print("Введено неправильно число")
    except ValueError:
        print("Введіть число!")
main()