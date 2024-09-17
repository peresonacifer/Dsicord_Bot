from flask import Flask, request, jsonify, send_file
import bing_image_search

app = Flask(__name__)

@app.route('/search_image', methods=['GET'])
def search_image():
    keywords = request.args.get('keywords', '')
    face_only = request.args.get('face_only', 'false').lower() == 'true'
    max_images = int(request.args.get('max_images', 50))
    proxy = request.args.get('proxy')
    proxy_type = request.args.get('proxy_type')

    image_bytes = bing_image_search.search_original_image(keywords, max_images=max_images, face_only=face_only, proxy=proxy, proxy_type=proxy_type)
    if image_bytes:
        return send_file(image_bytes, mimetype='image/jpeg', as_attachment=True, download_name='image.jpg')
    else:
        return jsonify({'error': 'No image found or an error occurred'}), 404

if __name__ == '__main__':
    app.run(port=5000, debug=True)
