import requests

API_KEY = "$2a$10$fpt7IlP4nLjCy9mNj6RSoemR0G1bdJ.Mib1Z/VrZ7IODz53m.6gLC"
BIN_ID = "6812c07b8561e97a500b2157"
BASE_URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"

HEADERS = {
    "X-Master-Key": API_KEY,
    "Content-Type": "application/json"
}

def get_leaderboard():
    response = requests.get(BASE_URL, headers=HEADERS)
    if response.status_code == 200:
        return response.json()["record"]
    else:
        print("Error fetching leaderboard:", response.text)
        return []

def submit_score(name, score):
    leaderboard = get_leaderboard()
    name = str(name)[:3].upper()
    leaderboard.append({"name": name, "score": score})
    # Sort by score descending, keep top 10
    leaderboard = sorted(leaderboard, key=lambda x: x["score"], reverse=True)[:10]
    # Update the bin
    response = requests.put(BASE_URL, headers=HEADERS, json=leaderboard)
    if response.status_code == 200:
        print("Score submitted!")
    else:
        print("Error submitting score:", response.text)