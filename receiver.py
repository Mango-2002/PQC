import oqs
import paho.mqtt.client as mqtt
import json
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import time
from rich.console import Console
from rich.table import Table

console = Console()

# 🔑 Generate Kyber512 keypair
receiver = oqs.KeyEncapsulation('Kyber512')
receiver_pub = receiver.generate_keypair()

# 📋 Helper to show decrypted details
def show_receiver_data(ciphertext, nonce, encrypted_msg, decrypted_msg, key):
    table = Table(title="🔓 Receiver Decryption Details", show_lines=True)
    table.add_column("Field", style="green", no_wrap=True)
    table.add_column("Value", style="yellow")

    table.add_row("Ciphertext (hex)", ciphertext.hex())
    table.add_row("Nonce", nonce.hex())
    table.add_row("Encrypted Message", encrypted_msg.hex())
    table.add_row("Derived ChaCha20 Key", key.hex())
    table.add_row("Decrypted Message", decrypted_msg)

    console.print(table)

# 📡 MQTT callbacks
def on_connect(client, userdata, flags, rc):
    console.print("📡 [bold green]Receiver connected. Broadcasting public key...[/]")
    client.subscribe("kyber/message")
    time.sleep(1)
    result = client.publish("kyber/key", receiver_pub.hex(), retain=True)
    if result.rc == 0:
        console.print("✅ Public key published to topic [bold]kyber/key[/]")
    else:
        console.print("❌ Failed to publish key. Return code:", result.rc)

def on_message(client, userdata, msg):
    console.print(f"📨 Message received on [bold]{msg.topic}[/]")
    data = json.loads(msg.payload.decode())

    ciphertext = bytes.fromhex(data['ciphertext'])
    nonce = bytes.fromhex(data['nonce'])
    encrypted_msg = bytes.fromhex(data['encrypted_msg'])

    # 🔐 Derive shared secret
    shared_secret = receiver.decap_secret(ciphertext)
    key = shared_secret[:32]

    # 🔓 Decrypt
    chacha = ChaCha20Poly1305(key)
    decrypted = chacha.decrypt(nonce, encrypted_msg, None)

    # 🖥️ Show results
    show_receiver_data(ciphertext, nonce, encrypted_msg, decrypted.decode(), key)

# 🚀 MQTT setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)

console.print("⏳ [italic]Receiver waiting for messages...[/]")
client.loop_forever()