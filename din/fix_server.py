import os; os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/recommend', methods=['POST','GET','OPTIONS'])
def recommend():
    if request.method == 'OPTIONS':
        resp = app.make_default_options_response()
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = '*'
        return resp

    # Log raw request
    raw = request.get_data(as_text=True)
    ct = request.content_type or ''
    print(f'REQ: ct={ct} body=[{raw[:300]}]', flush=True)

    # Try to get username from anywhere
    username = 'admin'  # default

    # Try JSON body
    try:
        data = request.get_json(silent=True)
        if data and 'username' in data:
            username = data['username']
    except:
        pass

    # Try query param
    if request.args.get('username'):
        username = request.args['username']

    print(f'  -> username={username}', flush=True)

    # Return mock results (no DIN model needed for this test)
    return jsonify({
        'user_id': 98047837,
        'username': username,
        'recommendations': [
            {'item_id': i, 'category': 700+i, 'score': 0.99-0.05*i}
            for i in [317513208, 29857043, 57474847, 253433360, 85720690,
                      50377847, 119217053, 401149090, 225988839, 212743365]
        ]
    })

app.run(host='0.0.0.0', port=5001, debug=False)
