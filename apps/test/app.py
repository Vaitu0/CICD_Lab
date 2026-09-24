from flask import Flask, jsonife

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, World! This is a test app."

@app.route('/health')
def health():
    return jsonife({"status": "ok"})

@app.route('/<name>')
def user(name):
    return f"Hello, {name}! This is a test app."


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)