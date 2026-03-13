import pickle
import numpy as np
from onemind_node import load_model

# Node lädt das aktuelle globale Modell
model = load_model()

print("One Mind Test-Chat gestartet!")
print("Tippe 'exit', um zu beenden.\n")

while True:
    user_input = input("Du: ")
    if user_input.lower() == "exit":
        break
    
    # Einfaches Mapping: Länge des Textes auf eine Zahl für die Modell-„Antwort“
    X = np.array([[len(user_input) % 10, len(user_input) % 5, len(user_input) % 3]])
    
    # Modellvorhersage
    y_pred = model.predict(X)
    
    # Umwandlung in Text (nur als Simulation)
    response = f"One Mind sagt: {np.round(y_pred[0], 2)} (simulierte Antwort)"
    print(response)