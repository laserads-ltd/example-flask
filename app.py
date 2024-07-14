from flask import Flask, request, jsonify, render_template
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

def parse_proxy(proxy_str):
    try:
        if '@' in proxy_str:
            parts = proxy_str.split('@')
            credentials, host_port = parts if ':' in parts[0] else parts[::-1]
            login, password = credentials.split(':')
            hostname, port = host_port.split(':')
        elif proxy_str.count(':') == 3:
            login, password, hostname, port = proxy_str.split(':')
        elif proxy_str.count(':') == 1:
            hostname, port = proxy_str.split(':')
            login, password = None, None
        else:
            raise ValueError('Invalid proxy format')
        
        proxy_url = f"http://{hostname}:{port}"
        if login and password:
            proxy_url = f"http://{login}:{password}@{hostname}:{port}"
        
        # Return the proxy string in the desired format
        proxy_string = f"{hostname}:{port}:{login}:{password}" if login and password else f"{hostname}:{port}"
        
        return {
            "proxy_url": {"http": proxy_url, "https": proxy_url},
            "proxy_string": proxy_string
        }
    except Exception as e:
        raise ValueError('Error parsing proxy: ' + str(e))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/proxy', methods=['POST'])
def use_proxy():
    data = request.json
    proxy_str = data.get('proxy')
    
    if not proxy_str:
        return jsonify({"error": "Proxy string is required"}), 400

    try:
        parsed_proxy = parse_proxy(proxy_str)
        proxies = parsed_proxy['proxy_url']
        proxy_string = parsed_proxy['proxy_string']
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        post_response = requests.get('http://geo.anty-proxy-checker.com/ip-info', proxies=proxies)
        post_response.raise_for_status()
        post_response_json = post_response.json()
    except requests.RequestException as e:
        return jsonify({"error": f"Pixelscan API request failed: {str(e)}"}), 500
    except ValueError as e:
        return jsonify({"error": f"Error parsing Pixelscan response: {str(e)}"}), 500

    public_ip = post_response_json.get('ip')
    if not public_ip:
        return jsonify({"error": "Public IP not found in Pixelscan response"}), 500

    try:
        get_response = requests.get('http://ip-api.com/json', proxies=proxies)
        get_response.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": f"IP info request failed: {str(e)}"}), 500

    try:
        ipqs_response = requests.get(f'https://silver-mongoose-793346.hostingersite.com/indexv2.php?ip={public_ip}', proxies=proxies)
        ipqs_response.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": f"IPQS API request failed: {str(e)}"}), 500

    return jsonify({
        "pixelscan_response": post_response_json,
        "ip_api_response": get_response.json(),
        "ipqs_response": ipqs_response.json(),
        "proxies": proxy_string
    })

if __name__ == '__main__':
    app.run()
