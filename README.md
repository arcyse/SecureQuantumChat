 <p align="left">
  <a href="https://sqc.prnv.cc">
    <img src="https://raw.githubusercontent.com/arcyse/SecureQuantumChat/main/static/images/sqc-logo.png" width="100" alt="SecureQuantumChat Logo" />
  </a>
</p>

**SecureQuantumChat** is an open-source web application that demonstrates **quantum key distribution (QKD)** in action by enabling real-time encrypted chatrooms where keys are generated using the **BB84 quantum protocol** and messages are encrypted with a one-time pad derived from that key.

📍 Live demo: [https://sqc.prnv.cc](https://sqc.prnv.cc)

> [!WARNING]
> Do not expose your private keys, secrets, or any sensitive data anywhere — this demo uses [Qiskit](https://www.ibm.com/quantum/qiskit)'s simulated quantum channels for security concepts and proof of concept demo only.

## What Is It ?¿

SecureQuantumChat lets users create or join chat rooms where messages are encrypted using a **quantum-derived secret key** generated in the browser and server using the **BB84 QKD protocol** -  _a physics-based key exchange scheme that’s provably secure against eavesdroppers because measuring quantum information disturbs it._

This project is designed as a **proof of concept** showing how quantum key exchange and perfect secrecy can be used to protect real-time chat, even in the face of powerful attackers.


## Core Features

* **Quantum-generated keys:** Uses the BB84 protocol to create shared secret keys between client and server.
* **Encrypted chat:** Messages are encrypted with a one-time pad using keys derived from QKD.
* **Web-based:** Accessible directly from the browser via WebSocket with a Python/Flask backend.
* **Real-time communication:** Fast, interactive messaging once keys are established.


##  How It Works

1. **Create or Join a Room** – A user enters a name and room code; the browser establishes a WebSocket with the server.
2. **Quantum Key Exchange (BB84)** – Qubits are prepared and measured in random bases, sifted, error-checked, corrected, and privacy-amplified into a shared secret key (~256 bits).
3. **Secure Messaging** – Each message is encrypted with the quantum-derived key using XOR (one-time pad), ensuring perfect secrecy.


## Why This Matters

Unlike traditional symmetric key exchange (e.g. Diffie–Hellman) quantum key distribution doesn’t rely on computational hardness, it relies on physical laws. Eavesdropping on a quantum channel alters quantum states and can be **detected**, hence offering *information-theoretic security*.

This makes SecureQuantumChat a **tangible demonstration** of next-generation secure messaging.


## Quick Start (Local) 

Make sure you have Python and dependencies installed:

```bash
git clone https://github.com/arcyse/SecureQuantumChat.git
cd SecureQuantumChat
```

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the app:

```bash
python main.py
```

Then open your browser to the local server (`http://localhost:5000`).


## Tech Stack

| Component | Technology                              |
| --------- | ----------------------------------------|
| Backend   | Python + Flask                          |
| Realtime  | WebSockets (Flask-SocketIO)             |
| Quantum   | QKD (BB84 protocol) simulated by Qiskit |
| Frontend  | HTML/CSS/JS                             |


## License

This project is released under the GNU GENERAL PUBLIC LICENSE Version 3 - 29 June 2007.
