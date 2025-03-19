import os
import shutil
import json
import stat
import zipfile
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, simpledialog

LOG_FILE = "backup.log"

def log_message(message):
    time_stamp = datetime.now().strftime("%Y-%m-%d %H_%M_%S")
    with open(LOG_FILE, "a", encoding = "utf-8") as log:    
        log.write(f"[{time_stamp}] {message}\n")
    log_text.insert(tk.END, f"[{time_stamp}] {message}\n" )
    log_text.see(tk.END)

with open("config.json", "r") as f:
    config = json.load(f)

USER_HOME = os.path.expanduser("~")
SOURCE = config["source"].replace("%USER_HOME%", USER_HOME)
DEST = config["destination"]

def select_source():
    global SOURCE
    SOURCE = filedialog.askdirectory()
    if SOURCE:
        log_message(f"Вибрана директорія: {SOURCE}")

def select_dest():
    global DEST
    DEST = filedialog.askdirectory()
    if DEST:
        log_message(f"Вибрана директорія: {DEST}")


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
        shutil.rmtree(folder_path, onexc=remove_readonly)
        log_message(f"Папку {folder_path} видалено")
    except Exception as e:
        log_message(f"Помилка при видаленні {folder_path}: {e}")

def list_backups():
    backups = sorted(os.listdir(DEST), reverse = True)
    if not backups:
        log_message("Резервні копії відсутні")
        return []
    
    log_message("Список резервних копій: ")
    backups_array = [f"{i + 1}. {backup}" for i, backup in enumerate(backups)]
    log_message("\n".join(backups_array))
    return backups

def restore_backup():
    backups = list_backups()
    if not backups:
        return

    choice = simpledialog.askinteger("Вибір резервної копії", "Введіть номер резервної копії:", minvalue=1, maxvalue=len(backups))

    if choice is None:
        return

    backup_folder = os.path.join(DEST, backups[choice - 1])
    
    if backup_folder.endswith('.zip'):
        temp_extract_dir = os.path.join(DEST, f"temp_restore_{datetime.now().strftime('%Y-%m-%d_%H_%M_%S')}")
        os.makedirs(temp_extract_dir)
        log_message(f"Розпаковка {backup_folder} у {temp_extract_dir}")

        with zipfile.ZipFile(backup_folder, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
        
        log_message(f"Файли успішно розпаковані в {temp_extract_dir}")
        backup_folder = temp_extract_dir
    
    restore_option = messagebox.askyesno("Відновлення", "Відновити всю директорію? (Ні - окремі файли)")

    if restore_option:
        log_message(f"Відновлення всієї директорії з {backup_folder} у {SOURCE}")
        for root, dirs, files in os.walk(backup_folder):
            for file in files:
                src_file = os.path.join(root, file)
                relative_path = os.path.relpath(root, backup_folder)
                dest_folder = os.path.join(SOURCE, relative_path)
                dest_file = os.path.join(dest_folder, file)

                if not os.path.exists(dest_folder):
                    os.makedirs(dest_folder)

                try:
                    shutil.copy2(src_file, dest_file)
                    log_message(f"Відновлено: {file}")
                except PermissionError:
                    log_message(f"Немає доступу: {file}")

        remove_folder(temp_extract_dir)
        log_message("Операція відновлення завершена")
        return

    files_list = []
    for root, dirs, files in os.walk(backup_folder):
        for file in files:
            files_list.append(os.path.relpath(os.path.join(root, file), backup_folder))

    if not files_list:
        log_message("У цій директорії відсутні файли")
        return

    selected_files = simpledialog.askstring("Вибір файлів", "Введіть номери файлів через кому або 'all' для всіх:\n" + "\n".join(f"{i + 1}. {f}" for i, f in enumerate(files_list)))
    
    if selected_files.lower() == "all":
        selected_files = files_list
    else:
        try:
            selected_files = [int(num.strip()) - 1 for num in selected_files.split(",") if num.strip().isdigit()]
            selected_files = [files_list[i] for i in selected_files if 0 <= i < len(files_list)]
        except ValueError:
            log_message("Номера файлів введені некоректно")
            return
            
        if not selected_files:
            log_message("Жоден файл не вибрано")
            return

    log_message(f"Відновлення вибраних файлів з {backup_folder} у {SOURCE}")

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

root = tk.Tk()
root.title("Резервне копіювання")
root.geometry("500x400")

btn_select_source = tk.Button(root, text="Вибрати директорію для копіювання", command=select_source)
btn_select_source.pack(pady=10)

btn_select_dest = tk.Button(root, text="Вибрати директорію для бекапів", command=select_dest)
btn_select_dest.pack(pady=10)

btn_backup= tk.Button(root, text="Створити резервну копію", command=create_backup)
btn_backup.pack(pady = 10)

btn_restore = tk.Button(root, text="Відновити резервну копію", command=restore_backup)
btn_restore.pack(pady=10)

log_text = scrolledtext.ScrolledText(root, width = 60, height = 15)
log_text.pack(pady = 10)

root.mainloop()