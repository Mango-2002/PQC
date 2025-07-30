from flask import Flask, request
from flask_cors import CORS
import threading
import oqs
import paho.mqtt.client as mqtt
import json
import os
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from rich.console import Console
from rich.table import Table

# ---------------- Flask setup ----------------
app = Flask(__name__)
CORS(app)  # ✅ enable cross-origin requests (React frontend can POST)
console = Console()

# ---------------- Global states ----------------
received_pub_key = None
connected = False
current_message = None  # will store steps from frontend

# ---------------- Utility function ----------------
def show_sender_data(message, pubkey, key, nonce, encrypted_msg):
    table = Table(title="🔐 Sender Encryption Details", show_lines=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    table.add_row("Original Message", message)
    table.add_row("Receiver's Public Key (hex)", pubkey.hex())
    table.add_row("Derived ChaCha20 Key", key.hex())
    table.add_row("Nonce", nonce.hex())
    table.add_row("Encrypted Message", encrypted_msg.hex())
    console.print(table)

def encrypt_and_send(message_text):
    """Helper to encrypt and send over MQTT if we have a public key."""
    if not received_pub_key:
        console.print("[red]⚠️ Cannot encrypt: no public key received yet.[/]")
        return

    message = message_text.encode()
    with oqs.KeyEncapsulation('Kyber512') as sender:
        ciphertext, shared_secret = sender.encap_secret(received_pub_key)

    key = shared_secret[:32]
    nonce = os.urandom(12)
    chacha = ChaCha20Poly1305(key)
    encrypted_msg = chacha.encrypt(nonce, message, None)

    payload = json.dumps({
        'ciphertext': ciphertext.hex(),
        'nonce': nonce.hex(),
        'encrypted_msg': encrypted_msg.hex()
    })

    client.publish("kyber/message", payload)
    console.print("📤 [bold blue]Encrypted message sent![/]")
    show_sender_data(message_text, received_pub_key, key, nonce, encrypted_msg)

# ---------------- MQTT callbacks ----------------
def on_connect(client, userdata, flags, rc):
    global connected
    console.print("🔌 [bold green]Sender connected to broker.[/]")
    connected = True
    client.subscribe("kyber/key")
    console.print("📡 Subscribed to [bold]kyber/key[/] for public key.")

def on_message(client, userdata, msg):
    global received_pub_key, current_message
    console.print("🔑 [bold yellow]Received public key![/]")
    received_pub_key = bytes.fromhex(msg.payload.decode())

    if current_message is None:
        console.print("[red]⚠️ No steps data received yet.[/]")
        return

    # If we already have steps, encrypt immediately
    encrypt_and_send(f"Steps in last 24 hours: {current_message}")

# ---------------- MQTT client setup ----------------
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)  # ✅ broker on same PC

# ---------------- Flask endpoint ----------------
@app.route('/send_steps', methods=['POST'])
def receive_steps():
    global current_message
    data = request.get_json()
    steps = data.get('steps')
    if steps is not None:
        current_message = steps
        console.print(f"✅ [green]Steps received from frontend: {steps}[/]")

        # 🔥 Encrypt and send immediately if key is already known
        encrypt_and_send(f"Steps in last 24 hours: {current_message}")

        return {"status": "ok", "message": f"Steps set to {steps}"}
    else:
        return {"status": "error", "message": "No steps field"}, 400

# ---------------- Run Flask in thread ----------------
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

threading.Thread(target=run_flask, daemon=True).start()

console.print("⏳ [italic]Waiting for connection and public key...[/]")
client.loop_forever()