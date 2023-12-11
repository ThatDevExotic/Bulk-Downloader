import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
import tkinter as tk
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor
from ttkthemes import ThemedStyle
import zipfile
import rarfile
import chard

current_version = "3.0a"
url = "https://raw.githubusercontent.com/iAmDextricity/Bulk-Downloader/main/version"

# Function to create a requests session
def create_session():
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

try:
    # Use the session for fetching the version
    session = create_session()
    response = session.get(url)
    response.raise_for_status()
    version = response.text.strip()
    print(f"\n\nLatest Version: {version}\nCurrent Version: {current_version}\n")
    if version != current_version:
        print("(Fucking Loser Alert) Your version is out of date; it is highly recommended to update it here: https://github.com/iAmDextricity/Bulk-Downloader/blob/main/README.md")
    else:
        print("You are currently using the latest version")
except requests.RequestException as e:
    print("Error fetching version:", e)
finally:
    # Close the session to release resources
    if 'session' in locals():
        session.close()

DEFAULT_MAX_WORKERS = 1
DEFAULT_DOWNLOAD_DIR = "./downloads"

print("Created by @Dextricity\nI recommend waiting till all workers are finished you impatient fucking shit.\nI literally threw this together in 10 minutes; Please hesitate to contact me.")

def download_file(url, destination_folder=DEFAULT_DOWNLOAD_DIR):
    try:
        os.makedirs(destination_folder, exist_ok=True)

        # Use the session for downloading the file
        session = create_session()
        response = session.get(url, stream=True)
        response.raise_for_status()

        file_name = os.path.join(destination_folder, get_safe_filename(url))
        downloading_file_name = file_name + '.downloading'
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192  # Increase block size for potentially better performance
        with open(downloading_file_name, 'wb') as file, tqdm(
                total=total_size,
                unit='iB',
                unit_scale=True,
                position=0,
                leave=True
        ) as progress_bar:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)

        os.rename(downloading_file_name, file_name)
        print(f"File downloaded successfully: {file_name}")

        return file_name  # Return the downloaded file path

    except requests.exceptions.RequestException as e:
        print(f"Failed to download file. Error: {e}")
        if os.path.exists(downloading_file_name):
            os.remove(downloading_file_name)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Close the session to release resources
        if 'session' in locals():
            session.close()

def extract_file(file_path):
    try:
        file_dir = os.path.dirname(file_path)
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(file_dir)
        print(f"File extracted successfully: {file_path}")
    except zipfile.BadZipFile:
        try:
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(file_dir)
            print(f"File extracted successfully: {file_path}")
        except rarfile.Error as rar_error:
            print(f"Failed to extract file. Error: {rar_error}")
    except Exception as e:
        print(f"An unexpected error occurred while extracting: {e}")

def convert_to_chd(file_path):
    try:
        # Check if the file is an ISO or BIN/CUE
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower()

        if file_extension in ['.iso', '.bin']:
            chd_file_path = file_path + '.chd'
            chd.create(file_path, chd_file_path)
            print(f"File converted to CHD successfully: {chd_file_path}")
            os.remove(file_path)  # Delete the source file
        else:
            print(f"File format not supported for CHD conversion: {file_path}")

    except Exception as e:
        print(f"An unexpected error occurred while converting to CHD: {e}")

def get_safe_filename(url):
    return os.path.basename(urlparse(url).path).replace("%20", " ")

def is_file_link(href):
    file_extensions = {'.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.jpg', '.jpeg', '.png', '.gif', '.mp3', '.mp4', '.iso', '.rar', '.3ds', '.gba', '.gb', '.nes', '.sms', '.sfc', '.binq', '.chd'}
    return any(href.endswith(ext) for ext in file_extensions)

def ensure_trailing_slash(url):
    return url if url.endswith('/') else url + '/'

def on_download_click():
    url = url_entry.get()
    url = ensure_trailing_slash(url)
    max_workers = int(max_workers_entry.get())
    download_dir = download_dir_entry.get()
    extract_files = extract_var.get()
    convert_to_chd_files = chd_var.get()

    try:
        page = requests.get(url)
        page.raise_for_status()
        soup = BeautifulSoup(page.content, 'html.parser')
        a_elements = soup.select('a[href]')

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for a_tag in a_elements:
                file_url = urljoin(url, a_tag.get('href'))
                if is_file_link(file_url):
                    status_label.config(text=f"Downloading file: {file_url}")
                    futures.append(executor.submit(download_file, file_url, download_dir))

            for future in tqdm(futures, desc="Downloading files", unit="file", leave=True):
                downloaded_file_path = future.result()
                if downloaded_file_path and extract_files:
                    extract_file(downloaded_file_path)
                if downloaded_file_path and convert_to_chd_files:
                    convert_to_chd(downloaded_file_path)

            if extract_files or convert_to_chd_files:
                status_label.config(text="All files downloaded and processed")
            else:
                status_label.config(text="All files downloaded")

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch content from the URL. Error: {e}")

# GUI
root = tk.Tk()
root.title("Web Scraper Downloader")
root.geometry("330x380")  # Set the window size

style = ThemedStyle(root)
style.set_theme("plastik")  # You can try different themes

# Create a rounded style for buttons
style.configure('Rounded.TButton', borderwidth=5, relief="flat", foreground="white", background="#3E3E3E", font=('Helvetica', 10, 'bold'))

frame = ttk.Frame(root, padding="10")
frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

url_label = ttk.Label(frame, text="Enter URL:")
url_label.grid(column=0, row=0, pady=10, sticky=tk.W)

url_entry = ttk.Entry(frame, width=50)
url_entry.grid(column=0, row=1, pady=10, sticky=tk.W)

max_workers_label = ttk.Label(frame, text="Max Workers (Files to download at a time):")
max_workers_label.grid(column=0, row=2, pady=5, sticky=tk.W)

max_workers_entry = ttk.Entry(frame, width=10)
max_workers_entry.insert(0, DEFAULT_MAX_WORKERS)
max_workers_entry.grid(column=0, row=3, pady=5, sticky=tk.W)

download_dir_label = ttk.Label(frame, text="Download Directory:")
download_dir_label.grid(column=0, row=4, pady=5, sticky=tk.W)

download_dir_entry = ttk.Entry(frame, width=50)
download_dir_entry.insert(0, DEFAULT_DOWNLOAD_DIR)
download_dir_entry.grid(column=0, row=5, pady=5, sticky=tk.W)

# Checkbutton for extraction option
extract_var = tk.BooleanVar()
extract_checkbutton = ttk.Checkbutton(frame, text="Extract Files", variable=extract_var)
extract_checkbutton.grid(column=0, row=6, pady=5, sticky=tk.W)

# Checkbutton for CHD conversion option
chd_var = tk.BooleanVar()
chd_checkbutton = ttk.Checkbutton(frame, text="Convert  iso or bin/cue to CHD", variable=chd_var)
chd_checkbutton.grid(column=0, row=7, pady=5, sticky=tk.W)

# Use the rounded style for the download button
download_button = ttk.Button(frame, text="Download Files", command=on_download_click, style='Rounded.TButton')
download_button.grid(column=0, row=8, pady=20, sticky=tk.W)

status_label = ttk.Label(frame, text="")
status_label.grid(column=0, row=9, sticky=tk.W)

root.mainloop()
