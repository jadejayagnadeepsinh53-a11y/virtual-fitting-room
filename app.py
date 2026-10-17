from flask import Flask, request, jsonify, render_template
from gradio_client import Client, handle_file
import shutil
import os
import time

app = Flask(__name__)

# Single, high-accuracy AI inventory focusing on upper-body garments
INVENTORY = {
    "890123": "static/pink_shirt.png",
    "890124": "static/navy_jacket.png",
    "890125": "static/blue_shirt.png"
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/tryon', methods=['POST'])
def try_on():
    barcode = request.form.get('barcode')
    user_image = request.files.get('user_image')

    if barcode not in INVENTORY:
        return jsonify({
                           "error": "Barcode not found in database. Please use a valid top garment code (890123, 890124, or 890125)."}), 404

    garment_path = INVENTORY[barcode]

    # Save the user's uploaded photo temporarily
    user_path = "temp_user_photo.jpg"
    user_image.save(user_path)

    # Reliable Auto-Retry System using the single accurate AI engine
    max_attempts = 15
    for attempt in range(max_attempts):
        try:
            print(f"Attempt {attempt + 1}: Processing with IDM-VTON AI for barcode {barcode}...")

            # Using the single, most accurate open-source VTON model
            client = Client("yisol/IDM-VTON")

            result = client.predict(
                dict({"background": handle_file(user_path), "layers": [], "composite": None}),
                handle_file(garment_path),
                "clothing item",
                True,
                True,
                30,
                42,
                api_name="/tryon"
            )

            generated_image_path = result[0] if isinstance(result, tuple) else result

            # Save the clean, accurate output image
            final_filename = f"live_result_{int(time.time())}.png"
            final_path = os.path.join("static", final_filename)
            shutil.copy(generated_image_path, final_path)

            return jsonify({"result_image_url": f"/static/{final_filename}"})

        except Exception as e:
            print(f"Server busy (Error: {e}). Retrying in 5 seconds... (Attempt {attempt + 1})")
            if attempt < max_attempts - 1:
                time.sleep(5)
            else:
                return jsonify({"error": "The AI server is busy right now. Please try again."}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)