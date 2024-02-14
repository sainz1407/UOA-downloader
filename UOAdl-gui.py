import os
import json
import threading
import io
import zlib
from Crypto.Cipher import AES
import base64
from PIL import Image, ImageTk
import httpx
import UnityPy
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class UniOnAirDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("UNI'S ON AIR Image Downloader")
        self.root.geometry("530x450")

        self.label_resver = ttk.Label(root, text="Server Date (resver):")
        self.label_resver.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.entry_resver = ttk.Entry(root)
        self.entry_resver.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        self.label_groups = ttk.Label(root, text="Groups:")
        self.label_groups.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        self.combobox_groups = ttk.Combobox(root, width=40)
        self.combobox_groups.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        self.label_members = ttk.Label(root, text="Members:")
        self.label_members.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

        self.combobox_members = ttk.Combobox(root, width=40)
        self.combobox_members.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

        self.button_download = ttk.Button(root, text="Download", command=self.start_download_thread)
        self.button_download.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        self.progress_bar = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress_bar.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        self.canvas = tk.Canvas(root, width=200, height=200)
        self.canvas.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

    def start_download_thread(self):
        threading.Thread(target=self.download_images).start()

    def load_member_data(self):
        with open("member.data.json", "r", encoding="utf-8") as member_file:
            member_data = json.load(member_file)
        return member_data

    def populate_comboboxes(self):
        member_data = self.load_member_data()
        groups = []
        members = []
        for group_name, group_members in member_data.items():
            groups.append(group_name)
            for member in group_members:
                members.append(f"{member['name']} ({member['romaji']}) {member['unisonair']}")
        self.combobox_groups['values'] = groups
        self.combobox_members['values'] = members

    def update_canvas_image(self, img_data):
        if img_data:
            img = Image.open(io.BytesIO(img_data))
            max_width = 400
            width, height = img.size
            new_height = int((max_width / width) * height)
            img = img.resize((max_width, new_height), Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            self.canvas.config(width=img_tk.width(), height=img_tk.height())
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
            self.canvas.image = img_tk
            self.canvas.update()
        else:
            self.canvas.delete("all")

    def download_images(self):
        resver = self.entry_resver.get() or None
        selected_group = self.combobox_groups.get()
        selected_member = self.combobox_members.get()
        if selected_group:
            selected_group = [selected_group]
        if selected_member:
            selected_unisonair = selected_member.split()[-1]  
            selected_member = [selected_unisonair]
        self.progress_bar['value'] = 0
        self.root.update_idletasks()
        self.update_canvas_image(b"")  # Clear canvas before downloading new images

        total_assets = 0  # Total number of assets to download
        assets_downloaded = 0  # Number of assets already downloaded
        main(resver, selected_group, selected_member, self.progress_bar, self.update_canvas_image, total_assets, assets_downloaded)

        messagebox.showinfo("Download Complete", "Downloaded successfully.")

def decrypt(file_path, key, iv, output_path):
    if os.path.exists(output_path):
        with open(output_path, 'r') as file:
            return json.load(file)
    with open(file_path, 'rb') as file:
        encrypted_data = file.read()
    cipher = AES.new(base64.b64decode(key), AES.MODE_CBC, base64.b64decode(iv))
    decrypted_data = cipher.decrypt(encrypted_data)
    decrypted_data = decrypted_data[:-decrypted_data[-1]]  # PKCS7 strip
    decompressed_data = zlib.decompress(decrypted_data)
    json_data = json.loads(decompressed_data.decode('utf-8'))
    with open(output_path, 'w') as file:
        json.dump(json_data, file, indent=2)
    return json_data

def download_file(url, destination):
    if os.path.exists(destination):
        return False
    with httpx.stream("GET", url, timeout=None) as response:
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        with open(destination, 'wb') as file:
            downloaded_size = 0
            for data in response.iter_bytes():
                downloaded_size += len(data)
                file.write(data)
                # progress = min(int((downloaded_size / total_size) * 100), 100)
                # app.progress_bar['value'] = progress
                # app.root.update_idletasks()
    return True

def load_json(file_path):
    with open(file_path, 'r') as file:
        json_data = json.load(file)
    return json_data["assets_masters"]

def main(resver, groups, members, progress_bar, update_canvas_image, total_assets, assets_downloaded):
    assets_masters_url = f"https://cdn-masters.unis-on-air.com/production/{resver}/Android/assets_masters"
    file_path = ".temp/assets_masters"
    output_file = f"{file_path}.json"
    if not os.path.exists(".temp"):
        os.makedirs(".temp")
    download_file(assets_masters_url, file_path)
    key = "MgTWfLGCfeFRVyA1WeHcW8mW6yNzVYMFJJBqCBt99DQ="
    iv = "tIEJY1DpzfxTsi85Y1Ug/w=="
    decrypt(file_path, key, iv, output_file)
    json_data = load_json(output_file)
    base_url = f"https://cdn-assets.unis-on-air.com/client_assets/{resver}/Android/"
    save_folder = "images"

    with open("member.data.json","r",encoding="utf-8") as member_file:
        member_data = json.load(member_file)
    selected_members = []
    if groups:
        for group_name in groups:
            selected_members.extend([member["unisonair"] for member in member_data[group_name]])
    if members:
        selected_members.extend(members)
    total_assets = 0
    for item in json_data:
        for selected_member in selected_members:
            for group, members in member_data.items():
                for member in members:
                    if selected_member == member["unisonair"] and f"content/cards/scene_card_{selected_member}_" in item["code"]:
                        total_assets += 1
    assets_downloaded = 0
    for item in json_data:
        for selected_member in selected_members:
            for group, members in member_data.items():
                for member in members:
                    if selected_member == member["unisonair"]:
                        member_folder = os.path.join(save_folder, member["name"])
                        if not os.path.exists(member_folder):
                            os.makedirs(member_folder)
                        if f"content/cards/scene_card_{selected_member}_" in item["code"]:
                            assets_path = os.path.join(member_folder, f"{item['code'].split('/')[-1].replace('.unity3d', '.png')}")
                            if os.path.exists(assets_path):
                                print(f"File already exists: {assets_path}")
                                assets_downloaded += 1
                                progress_bar["value"] = (assets_downloaded / total_assets) * 100
                                progress_bar.update()
                                continue
                            else:
                                print(f"Downloading: {assets_path}")
                                file_url = base_url + item["code"]
                                destination = os.path.join(".temp", item["code"].split("/")[-1])
                                if download_file(file_url, destination):
                                    env = UnityPy.load(destination)
                                    texture_size = 0
                                    assets = None
                                    for obj in env.objects:
                                        if obj.type.name == "Texture2D":
                                            tex = obj.read()
                                            size = tex.image.width * tex.image.height
                                            if size > texture_size:
                                                texture_size = size
                                                assets = tex
                                    if assets is not None:
                                        assets.image.save(assets_path)
                                        with open(assets_path, "rb") as img_file:
                                            img_data = img_file.read()
                                        update_canvas_image(img_data)  # Update canvas with downloaded image
                                    os.remove(destination)
                                    assets_downloaded += 1
                                    progress_bar["value"] = (assets_downloaded / total_assets) * 100
                                    progress_bar.update()
                                else:
                                    print(f"Failed to download: {assets_path}")
                                    update_canvas_image(b"")
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(output_file):
        os.remove(output_file)

if __name__ == "__main__":
    root = tk.Tk()
    app = UniOnAirDownloader(root)
    app.populate_comboboxes()
    root.mainloop()
