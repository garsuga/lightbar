from flask import Flask, flash, make_response, redirect, request, send_file, send_from_directory, abort, jsonify
import os
from io import BytesIO
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

def _get_lightbar_settings():
    settings = None
    with open(SETTINGS_PATH, "r") as settings_file:
        settings = json.load(settings_file)
    return settings

# Get lightbar settings
@app.route("/lightbar-settings", methods=["GET"])
def get_lightbar_settings():
    return jsonify(_get_lightbar_settings())

def _get_image_stats(name):
    stat_path = IMAGES_DIR / name / 'stats.json'
    with open(stat_path, 'r') as stat_file:
        return json.load(stat_file)

def _get_image_original(name):
    image_path = IMAGES_DIR / name / 'original.png'
    return Image.open(image_path)

def _create_image_stat(image, url):
    return dict(
        size=dict(
            width=image.width, 
            height=image.height
        ),
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

# prepare a saved image for lightbar and set it as active
# {
#    resampling?: 'NEAREST' | 'BOX' | 'BILINEAR' | 'HAMMING' | 'BICUBIC' | 'LANCZOS'
#    imageName: string,
#    brightness: [0 ... 1],
#    fps: [0 ... 30]
# }
@app.route("/active", methods=['GET', 'POST'])
def active_image():
    if request.method == "POST":
        body = request.json
        fps = body['fps'] if 'fps' in body else 30
        if fps > 30 or fps < 0:
            fps = 30
        resampling = body['resampling'] if 'resampling' in body else 'BICUBIC'
        image_name = body['imageName']
        brightness = body['brightness']
        raw, encoded = format_image(image_name, resampling, brightness)
        encoded.save(ACTIVE_IMAGE_PATH)
        raw.save(ACTIVE_IMAGE_RAW_PATH)
        stats = _create_image_stat(encoded, ACTIVE_IMAGE_RAW_URL)
        stats['fps'] = fps
        stats['name'] = image_name
        with open(ACTIVE_IMAGE_STAT_PATH, "w") as statsfile:
            json.dump(stats, statsfile, indent=4)
        return "Image prepared"
    if request.method == "GET":
        if os.path.isfile(ACTIVE_IMAGE_STAT_PATH):
            with open(ACTIVE_IMAGE_STAT_PATH, "r") as statsfile:
                return jsonify(json.load(statsfile))
        return jsonify({})
    
    


def format_image(image_name, resampling, brightness):
    resampling = Image.Resampling[resampling]
    settings = _get_lightbar_settings()
    image = _get_image_original(image_name)

    new_height = settings['numPixels']
    new_width = round((new_height / image.height) * image.width)
    
    image = image.resize((new_width, new_height), resample=resampling)
    encoded = _encode_pixels(image, settings, brightness)

    return image, encoded



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
                original=_create_image_stat(original, original_url),
                thumbnail=_create_image_stat(thumbnail, thumbnail_url)
            ), indent=4)
        with open(out_dir / 'stats.json', "w") as statsfile:
            statsfile.write(stats)

        
        return "Upload successful"
    abort(400, 'File not supported')


if __name__ == '__main__':
    app.run(use_reloader=True, host='0.0.0.0', port=5000, threaded=True)
