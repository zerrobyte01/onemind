import threading
import time
import pickle
import socket
import json
import hashlib
import os
import numpy as np
from sklearn.linear_model import SGDRegressor
from sklearn.datasets import make_regression

# -----------------------
# Dateipfade
# -----------------------
BLOCKCHAIN_FILE = "blockchain.pkl"
GLOBAL_MODEL_FILE = "global_model.pkl"
PEERS_FILE = "peers.pkl"

# -----------------------
# Initialisierung
# -----------------------
if not os.path.exists(BLOCKCHAIN_FILE):
    genesis_block = {
        "index": 0,
        "timestamp": time.time(),
        "prev_hash": "0",
        "model_update": None,
        "node_id": "genesis",
        "hash": ""
    }
    genesis_block["hash"] = hashlib.sha256(json.dumps(genesis_block, sort_keys=True).encode()).hexdigest()
    with open(BLOCKCHAIN_FILE, "wb") as f:
        pickle.dump([genesis_block], f)

if not os.path.exists(GLOBAL_MODEL_FILE):
    X, y = make_regression(n_samples=10, n_features=3, noise=0.1)
    model = SGDRegressor(max_iter=1000)
    model.partial_fit(X, y)
    with open(GLOBAL_MODEL_FILE, "wb") as f:
        pickle.dump(model, f)

if not os.path.exists(PEERS_FILE):
    with open(PEERS_FILE, "wb") as f:
        pickle.dump([], f)

# -----------------------
# Hilfsfunktionen
# -----------------------
def load_model():
    with open(GLOBAL_MODEL_FILE, "rb") as f:
        return pickle.load(f)

def save_model(model):
    with open(GLOBAL_MODEL_FILE, "wb") as f:
        pickle.dump(model, f)

def load_blockchain():
    with open(BLOCKCHAIN_FILE, "rb") as f:
        return pickle.load(f)

def save_blockchain(chain):
    with open(BLOCKCHAIN_FILE, "wb") as f:
        pickle.dump(chain, f)

def load_peers():
    with open(PEERS_FILE, "rb") as f:
        return pickle.load(f)

def save_peers(peers):
    with open(PEERS_FILE, "wb") as f:
        pickle.dump(peers, f)

# -----------------------
# Proof-of-Useful-Work
# -----------------------
def proof_of_useful_work(model):
    X, y = make_regression(n_samples=5, n_features=3, noise=0.1)
    model.partial_fit(X, y)
    return model

# -----------------------
# Blockchain-Block erstellen
# -----------------------
def create_block(model, node_id):
    chain = load_blockchain()
    last_block = chain[-1]
    update = {"coef": model.coef_.tolist(), "intercept": model.intercept_.tolist()}
    block = {
        "index": last_block["index"] + 1,
        "timestamp": time.time(),
        "prev_hash": last_block["hash"],
        "model_update": update,
        "node_id": node_id
    }
    block["hash"] = hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()
    chain.append(block)
    save_blockchain(chain)
    return block

# -----------------------
# P2P-Kommunikation
# -----------------------
def send_block(peer_ip, peer_port, block):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((peer_ip, peer_port))
        s.send(json.dumps(block).encode())
        s.close()
    except:
        pass

def p2p_server(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("", port))
    server.listen(5)
    print(f"[P2P] Node lauscht auf Port {port}")
    while True:
        client, addr = server.accept()
        data = client.recv(4096)
        if data:
            try:
                block = json.loads(data.decode())
                chain = load_blockchain()
                last_block = chain[-1]
                if block["prev_hash"] == last_block["hash"]:
                    chain.append(block)
                    save_blockchain(chain)
                    model = load_model()
                    update = block["model_update"]
                    model.coef_ = (model.coef_ + np.array(update["coef"])) / 2
                    model.intercept_ = (model.intercept_ + np.array(update["intercept"])) / 2
                    save_model(model)
                    print(f"[P2P] Neuer Block von {block['node_id']} integriert: Index {block['index']}")
                peers = load_peers()
                if addr[0] not in [p[0] for p in peers]:
                    peers.append((addr[0], addr[1]))
                    save_peers(peers)
            except:
                pass
        client.close()

def broadcast_block(block):
    peers = load_peers()
    for peer in peers:
        send_block(peer[0], peer[1], block)

# -----------------------
# Peer Discovery
# -----------------------
def peer_discovery():
    while True:
        peers = load_peers()
        for peer in peers:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((peer[0], peer[1]))
                s.send(json.dumps({"type": "peer_request"}).encode())
                s.close()
            except:
                continue
        time.sleep(30)

# -----------------------
# Hauptloop
# -----------------------
def main_loop(node_id):
    while True:
        model = load_model()
        model = proof_of_useful_work(model)
        block = create_block(model, node_id)
        broadcast_block(block)
        time.sleep(5)

# -----------------------
# Node Start
# -----------------------
if __name__ == "__main__":
    node_id = input("Gib deine Node-ID ein (wird automatisch generiert, falls leer): ")
    if not node_id:
        node_id = "node_" + str(int(time.time()))
    bootstrap_peers = input("Bootstrap-Peers ip:port, Komma getrennt: ")
    if not bootstrap_peers:
        bootstrap_peers = "45.77.10.101:5001,172.105.56.200:5001"
    node_port = input("Port für diesen Node (Standard 5001): ")
    node_port = int(node_port) if node_port else 5001

    peers = []
    for p in bootstrap_peers.split(","):
        ip, port = p.split(":")
        peers.append((ip.strip(), int(port.strip())))
    save_peers(peers)

    threading.Thread(target=p2p_server, args=(node_port,), daemon=True).start()
    threading.Thread(target=peer_discovery, daemon=True).start()
    main_loop(node_id)