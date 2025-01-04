import requests

def send_ntfy_notification(message):
    url = "https://ntfy.sh/picam"  # Nahraď 'tvoje_téma' libovolným názvem
    headers = {
        "Title": "Detekce pohybu",  # Titul notifikace
        "Priority": "high",  # Priorita notifikace
        "Content-Type": "text/plain; charset=utf-8"  # Nastavení UTF-8 kódování
    }
    data = message.encode('utf-8')  # Převedení zprávy na UTF-8

    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 200:
        print("Notifikace byla úspěšně odeslána.")
    else:
        print(f"Chyba při odesílání notifikace: {response.status_code}")

# Odeslání zprávy
send_ntfy_notification("Detekována změna v obraze")  # Testovací zpráva

