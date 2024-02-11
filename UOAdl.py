import os
import json
from Crypto.Cipher import AES
import base64
import zlib
import httpx
from tqdm import tqdm
import UnityPy
import argparse

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
        block_size = 1024  # 1 KB
        progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)
        with open(destination, 'wb') as file:
            for data in response.iter_bytes():
                progress_bar.update(len(data))
                file.write(data)
        progress_bar.close()
    return True

def load_json(file_path):
    with open(file_path, 'r') as file:
        json_data = json.load(file)
    return json_data["assets_masters"]

def main(resver, groups, members):
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
    for item in json_data:
        for selected_member in selected_members:
            for group, members in member_data.items():
                for member in members:
                    if selected_member == member["unisonair"]:
                        member_folder = os.path.join(save_folder, member["name"])
                        if not os.path.exists(member_folder):
                            os.makedirs(member_folder)
                        if f"content/cards/scene_card_{selected_member}_" in item["code"]:
                            file_url = base_url + item["code"]
                            destination = os.path.join(".temp", item["code"].split("/")[-1])
                            assets_path = os.path.join(member_folder, f"{item['code'].split('/')[-1].replace('.unity3d', '.png')}")
                            if not os.path.exists(assets_path):
                                print(f"Downloading: {assets_path}")
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
                                    os.remove(destination)
                            else:
                                print(f"File already exists: {assets_path}")
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(output_file):
        os.remove(output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download images of selected members from UNI'S ON AIR")
    parser.add_argument("--resver", default=None, help="Specify the resver manually")
    parser.add_argument("--groups", nargs='+', default=[], help="Specify the groups to download members from")
    parser.add_argument("--members", nargs='+', default=[], help="Specify individual members to download")
    parser.add_argument("--list", action="store_true", help="Display available groups and members")
    args = parser.parse_args()
    if args.list:
        with open("member.data.json", "r",encoding="utf-8") as member_file:
            member_data = json.load(member_file)
        print("Available groups:")
        for group_name in member_data.keys():
            print(group_name)
        print("\nAvailable members:")
        for group_name, members in member_data.items():
            print(f"Group: {group_name}")
            for member in members:
                print(f"Name: {member['name']} (Member num: {member['unisonair']})")
    else:
        if args.resver:
            resver = args.resver
        else:
            resver = input("Please input Server Date (default=None): ")
            if not resver:
                resver = '20240208141636'
        main(resver, args.groups, args.members)
