import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
import tkinter as tk
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor
from ttkthemes import ThemedStyle

current_version = "1.72"
url = "https://raw.githubusercontent.com/iAmDextricity/Bulk-Downloader/main/version"

try:
    response = requests.get(url)
    response.raise_for_status()
    version = response.text.strip()
    print(f"\n\nLatest Version: {version}\nCurrent Version: {current_version}\n")
    if version != current_version:
        print("(Fucking Loser Alert) Your version is out of date; it is highly recommended to update it here: https://github.com/iAmDextricity/Bulk-Downloader/blob/main/README.md")
    else:
        print("You are currently using the latest version")
except requests.RequestException as e:
    print("Error fetching version:", e)

DEFAULT_MAX_WORKERS = 10
DEFAULT_DOWNLOAD_DIR = "./downloads"

print("Created by @Dextricity\nI recommend waiting till all workers are finished you impatient fucking shit.\nI literally threw this together in 10 minutes; Please hesitate to contact me.")

def download_file(url, destination_folder=DEFAULT_DOWNLOAD_DIR):
    try:
        os.makedirs(destination_folder, exist_ok=True)
        response = requests.get(url, stream=True)
        response.raise_for_status()
        file_name = os.path.join(destination_folder, get_safe_filename(url))
        downloading_file_name = file_name + '.downloading'
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024
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

    except requests.exceptions.RequestException as e:
        print(f"Failed to download file. Error: {e}")
        if os.path.exists(downloading_file_name):
            os.remove(downloading_file_name)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

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
                future.result()
            status_label.config(text="All files downloaded")

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch content from the URL. Error: {e}")

root = tk.Tk()
root.title("Web Scraper Downloader")
root.geometry("620x310")  # Set the window size

style = ThemedStyle(root)
style.set_theme("plastik")  # You can try different themes

url_label = ttk.Label(root, text="Enter URL:")
url_label.pack(pady=10)

url_entry = ttk.Entry(root, width=50)
url_entry.pack(pady=10)

max_workers_label = ttk.Label(root, text="Max Workers (Files to download at a time):")
max_workers_label.pack(pady=5)

max_workers_entry = ttk.Entry(root, width=10)
max_workers_entry.insert(0, DEFAULT_MAX_WORKERS)
max_workers_entry.pack(pady=5)

download_dir_label = ttk.Label(root, text="Download Directory:")
download_dir_label.pack(pady=5)

download_dir_entry = ttk.Entry(root, width=50)
download_dir_entry.insert(0, DEFAULT_DOWNLOAD_DIR)
download_dir_entry.pack(pady=5)

download_button = ttk.Button(root, text="Download Files", command=on_download_click)
download_button.pack(pady=20)

status_label = ttk.Label(root, text="")
status_label.pack()

root.mainloop()
