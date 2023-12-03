from flask import Flask, flash, make_response, redirect, request, send_from_directory, abort, jsonify
import os
from pathlib import Path
import re
from werkzeug.utils import secure_filename
from PIL import Image
import json
import math

DATA_DIR = Path("./data")
IMAGES_DIR = Path(DATA_DIR) / "images"

DATA_URL = Path("./data")
IMAGES_URL = DATA_URL / "images"

SETTINGS_PATH = Path("./") / "lightbar_settings.json"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp']
def allowed_image(filename):
    fpath = Path(filename)
    suffixes = fpath.suffixes
    if fpath.stem == 'data':
        return False
    return len(suffixes) == 1 and str.lower(suffixes[0]) in ALLOWED_IMAGE_EXTENSIONS

# remove transparency by overlaying image on black
def remove_transparency(image):
    im_black = Image.new('RGBA', image.size, (0, 0, 0))

    im_combined = Image.alpha_composite(im_black, image.convert("RGBA"))
    return im_combined.convert("RGB")

# crop a centered square from image
def crop_square(image):
    if image.height == image.width:
        return image
    if image.height > image.width:
        mid = image.height / 2
        return image.crop((0, 
                           math.ceil(mid + image.width / 2), 
                           image.width, 
                           math.ceil(mid - image.width / 2)))
    mid = image.width / 2
    return image.crop((math.ceil(mid - image.height / 2), 
                       0, 
                       math.ceil(mid + image.height / 2), 
                       image.height))

app = Flask(__name__, static_folder='web/build')

# Serve React App (static files not beginning in /data)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# Serve Static Files (/data/<path:path>)
@app.route(f'/{str(DATA_DIR).replace('\\', '/')}/<path:path>')
def serve_file(path):
    if path != "" and os.path.exists(DATA_DIR / path):
        return send_from_directory(DATA_DIR, path)
    abort(404)

any_extension = lambda name: fr'{name}\\..+'
original_any_ext = any_extension("original")
thumbnail_any_ext = any_extension("thumbnail")

# Get lightbar settings
@app.route("/lightbar-settings", methods=["GET"])
def get_lightbar_settings():
    settings = None
    with open(SETTINGS_PATH, "r") as settings_file:
        settings = json.load(settings_file)
    return jsonify(settings)


# Get images list
@app.route("/images", methods=["GET"])
def get_images():
    dirs = os.listdir(IMAGES_DIR)

    all_stats = dict()

    for name in dirs:
        path = IMAGES_DIR / name
        with open(path / 'stats.json') as stats_file:
            all_stats[name] = json.load(stats_file)
    
    return jsonify(all_stats)

# Upload image
@app.route('/upload-image', methods=["POST"])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_image(file.filename):
            name = Path(secure_filename(file.filename)).stem
            original = Image.open(file.stream)
            out_dir = IMAGES_DIR / name
            # TODO: conflict existing
            os.makedirs(out_dir, exist_ok=True)
            original = remove_transparency(original)
            thumbnail = crop_square(original)

            original_path = out_dir / 'original.png'
            thumbnail_path = out_dir / 'thumbnail.png'

            original_url = IMAGES_URL / name / 'original.png'
            thumbnail_url = IMAGES_URL / name / 'thumbnail.png'

            thumbnail.save(thumbnail_path, 'png')
            original.save(original_path, 'png')

            stats = json.dumps(
                dict(
                    original=dict(
                        size=dict(
                            width=original.width, 
                            height=original.height
                        ),
                        url=str(original_url).replace('\\', '/')
                    ),
                    thumbnail=dict(
                        size=dict(
                            width=thumbnail.width,
                            height=thumbnail.height
                        ),
                        url=str(thumbnail_url).replace('\\', '/')
                    )
                ), indent=4)
            with open(out_dir / 'stats.json', "w") as statsfile:
                statsfile.write(stats)

            
            return "Upload successful"
        abort(400, 'File not supported')


if __name__ == '__main__':
    app.run(use_reloader=True, host='0.0.0.0', port=5000, threaded=True)
