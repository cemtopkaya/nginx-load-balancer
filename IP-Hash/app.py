from flask import Flask, request, session
import socket
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Güvenli bir anahtar kullanın

@app.route('/')
def hello():
    hostname = socket.gethostname()
    if 'user_id' not in session:
        session['user_id'] = random.randint(1000, 9999)
    return f"Hello from {hostname}! Your session ID is {session['user_id']}"

@app.route('/ip')
def show_ip():
    client_ip = request.remote_addr
    return f"Your IP address is: {client_ip}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

