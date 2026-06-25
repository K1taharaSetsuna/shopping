import os; os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.before_request
def log_all():
    ct = request.content_type
    length = request.content_length
    raw = request.get_data(as_text=True)
    msg = f"[BEFORE] {request.method} {request.path} | ct={ct} | len={length} | body=[{raw[:300]}]"
    sys.stderr.write(msg + '\n')
    sys.stderr.flush()
    sys.stdout.write(msg + '\n')
    sys.stdout.flush()

@app.route('/recommend', methods=['POST','OPTIONS'])
def recommend():
    if request.method == 'OPTIONS':
        return '', 204, {'Access-Control-Allow-Origin':'*'}
    data = request.get_json(silent=True)
    if not data:
        sys.stderr.write(f'[400] get_json returned None\n')
        sys.stderr.flush()
        return jsonify({'error':'no data'}), 400
    return jsonify({'ok':True,'username':data.get('username','?'),'items':[1,2,3]})

app.run(host='0.0.0.0', port=5001, debug=False)
