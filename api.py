from flask import Flask, flash, make_response, redirect, request, send_file, send_from_directory, abort, jsonify
import os
from io import BytesIO
from pathlib import Path
import re
from werkzeug.utils import secure_filename
from PIL import Image
import json
import math
import asyncio

DATA_DIR = Path("./data")
IMAGES_DIR = Path(DATA_DIR) / "images"

DATA_URL = Path("./data")
IMAGES_URL = DATA_URL / "images"

LIGHTBAR_SETTINGS_PATH = Path("./") / "lightbar_settings.json"
DISPLAY_SETTINGS_PATH = Path("./") / "display_settings.json"

ACTIVE_IMAGE_PATH = DATA_DIR / "active.png"
ACTIVE_IMAGE_URL = DATA_URL / "active.png"
ACTIVE_IMAGE_RAW_PATH = DATA_DIR / "active-raw.png"
ACTIVE_IMAGE_RAW_URL = DATA_URL / "active-raw.png"
ACTIVE_IMAGE_STAT_PATH = DATA_DIR / "active-stats.json"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp']
def allowed_image(filename):
    fpath = Path(filename)
    suffixes = fpath.suffixes
    if fpath.stem in ['data', 'images', 'active', 'upload-image', 'lightbar-settings']:
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
                           math.ceil(mid - image.width / 2), 
                           image.width, 
                           math.ceil(mid + image.width / 2)))
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
    r = None
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        r = send_from_directory(app.static_folder, path)
    else:
        r = send_from_directory(app.static_folder, 'index.html')
    if 'ENV' in os.environ and os.environ['ENV'] == 'dev':
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return r

# Serve Static Files (/data/<path:path>)
@app.route('/' + str(DATA_DIR).replace("\\", "/") + '/<path:path>')
def serve_file(path):
    if path != "" and os.path.exists(DATA_DIR / path):
        return send_from_directory(DATA_DIR, path)
    abort(404)

any_extension = lambda name: fr'{name}\\..+'
original_any_ext = any_extension("original")
thumbnail_any_ext = any_extension("thumbnail")

def _get_lightbar_settings():
    settings = None
    with open(LIGHTBAR_SETTINGS_PATH, "r") as settings_file:
        settings = json.load(settings_file)
    return settings

def _get_display_settings():
    settings = None
    if not os.path.exists(DISPLAY_SETTINGS_PATH):
        with open(DISPLAY_SETTINGS_PATH, "w") as settings_file:
            json.dump(dict(
                brightness=.5,
                fps=10
            ), settings_file)
    with open(DISPLAY_SETTINGS_PATH, "r") as settings_file:
        settings = json.load(settings_file)
    return settings

# Get lightbar settings
@app.route("/lightbar-settings", methods=["GET"])
def get_lightbar_settings():
    return jsonify(_get_lightbar_settings())

@app.route("/display", methods=["GET"])
def display_on_ligthbar():
    from lightbar import display_image, create_lightbar
    lightbar_settings = _get_lightbar_settings()
    display_settings = _get_display_settings()
    lightbar = create_lightbar(lightbar_settings)
    image = Image.open(ACTIVE_IMAGE_PATH)
    display_image(lightbar, image, display_settings)
    return "Display started on lightbar"

# Get display settings
@app.route("/display-settings", methods=["GET", "POST"])
def get_display_settings():
    if request.method == "GET":
        return jsonify(_get_display_settings())
    new_settings = dict()
    body = request.json
    new_settings['brightness'] = body['brightness']
    new_settings['fps'] = body['fps']

    with open(DISPLAY_SETTINGS_PATH, "w") as display_settings_file:
        json.dump(new_settings, display_settings_file, indent=4)

    active_image_stats = _get_active_image_stats()
    if active_image_stats is not None:
        _update_active_image(active_image_stats['id'], active_image_stats['resampling'], new_settings['brightness'])
    return "Display settings updated"

def _get_image_stats(id):
    stat_path = IMAGES_DIR / id / 'stats.json'
    with open(stat_path, 'r') as stat_file:
        return json.load(stat_file)

def _get_image_original(id):
    image_path = IMAGES_DIR / id / 'original.png'
    return Image.open(image_path)

def _create_image_stat(image, name, url):
    return dict(
        size=dict(
            width=image.width, 
            height=image.height
        ),
        name=name,
        url=str(url).replace('\\', '/')
    )

# https://github.com/adafruit/Adafruit_CircuitPython_DotStar/issues/21#issue-323774759
GAMMA_CORRECT_FACTOR = 2.5
def _gamma_correct(led_val):
    max_val = (1 << 8) - 1.0
    corrected = pow(led_val / max_val, GAMMA_CORRECT_FACTOR) * max_val
    return int(min(255, max(0, corrected)))

# TODO
# TODO implement gamma correction
# TODO

# put the pixels in order with brightness so that iterating np.toarray(img) yields dotstar output
def _encode_pixels(image, settings, brightness):
    image = image.convert('RGBA')
    r,g,b,a = image.split()
    new_channels = [None, None, None, None]
    new_channels[0] = Image.new('L', image.size, math.ceil(brightness * 255))
    new_channels[settings['redIndex'] + 1] = r
    new_channels[settings['greenIndex'] + 1] = g
    new_channels[settings['blueIndex'] + 1] = b
    return Image.merge("RGBA", new_channels)

# https://stackoverflow.com/questions/7877282/how-to-send-image-generated-by-pil-to-browser
def serve_pil_image(pil_img):
    img_io = BytesIO()
    pil_img.save(img_io, 'PNG', quality=100)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

def _update_active_image(image_id, resampling, brightness):
    raw, encoded = format_image(image_id, resampling, brightness)
    encoded.save(ACTIVE_IMAGE_PATH)
    raw.save(ACTIVE_IMAGE_RAW_PATH)
    old_stat = _get_image_stats(image_id)
    stats = _create_image_stat(encoded, old_stat['original']['name'], ACTIVE_IMAGE_RAW_URL)
    stats['id'] = image_id
    stats['resampling'] = resampling
    with open(ACTIVE_IMAGE_STAT_PATH, "w") as statsfile:
        json.dump(stats, statsfile, indent=4)


def _get_active_image_stats():
    if os.path.isfile(ACTIVE_IMAGE_STAT_PATH):
        with open(ACTIVE_IMAGE_STAT_PATH, "r") as statsfile:
            return json.load(statsfile)
    return None

# prepare a saved image for lightbar and set it as active
# {
#    resampling?: 'NEAREST' | 'BOX' | 'BILINEAR' | 'HAMMING' | 'BICUBIC' | 'LANCZOS'
#    imageId: string
# }
@app.route("/active", methods=['GET', 'POST'])
def active_image():
    if request.method == "POST":
        body = request.json
        resampling = body['resampling'] if 'resampling' in body else 'BICUBIC'
        image_id = body['imageId']
        display_settings = _get_display_settings()
        _update_active_image(image_id, resampling, display_settings['brightness'])
        return "Image prepared"
    if request.method == "GET":
        active_image_stats = _get_active_image_stats()
        if active_image_stats is not None:
            return jsonify(active_image_stats)
        return jsonify({})
    
    
def format_image(image_id, resampling, brightness):
    try:
        resampling = Image.Resampling[resampling]
    except:
        resampling = Image.__getattribute__(resampling)
    settings = _get_lightbar_settings()
    image = _get_image_original(image_id)

    new_height = settings['numPixels']
    new_width = round((new_height / image.height) * image.width)
    
    if new_height != image.height:
        image = image.resize((new_width, new_height), resample=resampling)
    encoded = _encode_pixels(image, settings, brightness)

    return image, encoded


# Get images list
@app.route("/images", methods=["GET"])
def get_images():
    dirs = os.listdir(IMAGES_DIR)

    all_stats = dict()

    for id in dirs:
        path = IMAGES_DIR / id
        with open(path / 'stats.json') as stats_file:
            all_stats[id] = json.load(stats_file)
    
    return jsonify(all_stats)

# Upload image
@app.route('/upload-image', methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    name = request.form['name']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_image(file.filename):
        id = Path(secure_filename(file.filename)).stem
        original = Image.open(file.stream)
        out_dir = IMAGES_DIR / id
        os.makedirs(out_dir, exist_ok=True)
        original = remove_transparency(original)
        thumbnail = crop_square(original)

        original_path = out_dir / 'original.png'
        thumbnail_path = out_dir / 'thumbnail.png'

        original_url = IMAGES_URL / id / 'original.png'
        thumbnail_url = IMAGES_URL / id / 'thumbnail.png'

        thumbnail.save(thumbnail_path, 'png')
        original.save(original_path, 'png')

        stats = json.dumps(
            dict(
                original=_create_image_stat(original,  name, original_url),
                thumbnail=_create_image_stat(thumbnail, name, thumbnail_url)
            ), indent=4)
        with open(out_dir / 'stats.json', "w") as statsfile:
            statsfile.write(stats)

        
        return "Upload successful"
    abort(400, 'File not supported')


if __name__ == '__main__':
    app.run(use_reloader=True, host='0.0.0.0', port=5000, threaded=True)
