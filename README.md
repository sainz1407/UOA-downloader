## UNI'S ON AIR Image Downloader

This script downloads profile images of UNI'S ON AIR members from the game client assets.

**Requirements:**

* Python 3.x
* `pip install -r requirements.txt`

**Usage:**

```bash
python UOAdl.py [options]
```

**Options:**

* `--resver`: Override the server date (default: None).
* `--groups`: Specify groups to download from (multiple allowed).
* `--members`: Specify individual members to download (multiple allowed).
* `--list`: Display available groups and members.

**Example:**
For specific groups :
```bash
python UOAdl.py --resver 20240208141636 --groups sakurazaka46
```
For specific members :
```bash
python UOAdl.py --resver 20240208141636 --members 129 130
```

This will download images for members in the group and members from asset version "20240208141636" you can leave it blank for default asset version.

**Disclaimer:**

This script is intended for educational purposes only and is not endorsed by UNI'S ON AIR. Please use it responsibly and respect the terms of service of the game.

**Additional Notes:**

* The script currently only downloads card images. Other types of images might be available in the asset files.
* The script relies on private keys and URLs which may change over time.
* Always update the script and dependencies before using it to ensure compatibility.
