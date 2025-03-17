import os
import shutil
import json
import stat
import zipfile
from datetime import datetime

LOG_FILE = "backup.log"

def log_message(message):
    time_stamp = datetime.now().strftime("%Y-%m-%d %H_%M_%S")
    with open(LOG_FILE, "a", encoding = "utf-8") as log:
        log.write(f"[{time_stamp}] {message}\n")
    print(message)

with open("config.json", "r") as f:
    config = json.load(f)

USER_HOME = os.path.expanduser("~")
SOURCE = config["source"].replace("%USER_HOME%", USER_HOME)
DEST = config["destination"]

def create_backup():
    if not os.path.exists(DEST):
        os.makedirs(DEST)
        
    timeTamp = datetime.now().strftime("%Y-%m-%d %H_%M_%S")
    backup_folder = os.path.join(DEST, f"backup_{timeTamp}")
    os.makedirs(backup_folder)
    log_message(f"Створення резервної копії у {backup_folder}")

    for root, dirs, files in os.walk(SOURCE):
        relative_path = os.path.relpath(root, SOURCE)
        dest_path = os.path.join(backup_folder, relative_path)
    
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)

        for file in files:
            file_source = os.path.join(root, file)
            file_dest = os.path.join(dest_path, file)
            shutil.copy2(file_source, file_dest)
            log_message(f"Копіювання: {file_source} у {file_dest}")

    zip_path = os.path.join(DEST, f"backup_{timeTamp}")
    log_message("Архівація файлів")
    shutil.make_archive(zip_path, "zip", backup_folder)
    log_message("Архівація файлів завершена")
    remove_folder(backup_folder)

def remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def remove_folder(folder_path):
    try:
        shutil.rmtree(folder_path, onerror=remove_readonly)
        log_message(f"Архів {folder_path} видалено")
    except Exception as e:
        log_message(f"Помилка при видаленні {folder_path}: {e}")

def list_backups():
    backups = sorted(os.listdir(DEST), reverse = True)
    if not backups:
        log_message("Резервні копії відсутні")
        return[]
    
    log_message("Список резервних копій: ")
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
            log_message("Такої копії не існує")
            return
    except ValueError:
        log_message("Введіть число!")
        return
        
    backup_folder = os.path.join(DEST, backups[choice])
    
    if backup_folder.endswith('.zip'):
        temp_extract_dir = os.path.join(DEST, f"temp_restore_{datetime.now().strftime('%Y-%m-%d_%H_%M_%S')}")
        os.makedirs(temp_extract_dir)
        log_message(f"Розпаковка {backup_folder} у {temp_extract_dir}")

        with zipfile.ZipFile(backup_folder, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
        
        log_message(f"Файли успішно розпаковані в {temp_extract_dir}")
        extracted_files = os.listdir(temp_extract_dir)
        if not extracted_files:
            log_message("Помилка: після розпаковки файли не знайдено!")
            return
        else:
            log_message(f"Знайдено файли: {extracted_files}")

        backup_folder = temp_extract_dir
    
    log_message(f"Відновлення файлів з {backup_folder} у {SOURCE}")

    files_list = []

    for root, dirs, files in os.walk(backup_folder):
        for file in files:
            files_list.append(os.path.relpath(os.path.join(root, file), backup_folder))
        
    if not files_list:
        log_message("У цій директорії відсутні файли")
        return
        
    print("\nСписок файлів:")
    for i, file in enumerate(files_list, 1):
        print(f"{i}. {file}")
        
    selected_files = input("\nВведіть номери файлів для відновлення через кому, або напишіть all якщо хочете, щоб відновилася вся директорія\n")
    
    if selected_files.lower() == "all":
        selected_files = files_list

    else:
        try:
            selected_files = [int(num.strip()) for num in selected_files.split(",") if num.strip().isdigit()]
            selected_files = [files_list[i - 1] for i in selected_files if 0 < i <= len(files_list)]
        except ValueError:
            log_message("Номера файлів введені некоректно")
            return
            
        if not selected_files:
            log_message("Жоден файл не вибрано")
            return

    for file in selected_files:
        src_file = os.path.join(backup_folder, file)
        dest_file = os.path.join(SOURCE, file)

        dest_folder = os.path.dirname(dest_file)
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)

        try:
            shutil.copy2(src_file, dest_file)
            log_message(f"Відновлено: {file}")
        except PermissionError:
            log_message(f"Немає доступу: {file}")


    remove_folder(temp_extract_dir)

    log_message("Операція відновлення завершена")

def main():
    print("Вітаю у програмі резервного копіювання файлів! Для початку виберіть дію:\n1. Створення резервної копії\n2. Відновлення файлів із уже існуючої резервної копії")

    try:
        choice = int(input("Введіть 1 або 2: "))
        if choice == 1:
            create_backup()
        elif choice == 2:
            restore_backup()
        else:
            log_message("Введено неправильно число")
    except ValueError:
        log_message("Введіть число!")
main()