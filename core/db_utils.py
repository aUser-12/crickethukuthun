import json
import os
import threading
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / 'db.json'
_lock = threading.Lock()

def get_initial_data():
    return {
        "users": [],
        "venues": [
            {
                "id": 1,
                "name": "Downtown Sports Arena",
                "location": "123 Main Street, Downtown",
                "description": "A state-of-the-art sports arena featuring basketball courts, volleyball nets, and indoor soccer fields. Perfect for team sports and recreational activities."
            },
            {
                "id": 2,
                "name": "Riverside Tennis Club",
                "location": "456 River Road, Westside",
                "description": "Premium tennis facility with 8 outdoor courts and 4 indoor courts. Offers lessons for all skill levels and hosts regular tournaments."
            },
            {
                "id": 3,
                "name": "Mountain View Golf Course",
                "location": "789 Highland Drive, North Hills",
                "description": "An 18-hole championship golf course with stunning mountain views. Features a pro shop, driving range, and clubhouse restaurant."
            },
            {
                "id": 4,
                "name": "Aquatic Sports Center",
                "location": "321 Ocean Boulevard, Beachfront",
                "description": "Olympic-sized swimming pool with diving boards, water polo facilities, and a separate kids pool. Open year-round with heated pools."
            },
            {
                "id": 5,
                "name": "City Fitness Stadium",
                "location": "555 Athletic Way, Midtown",
                "description": "Multi-purpose stadium with track and field facilities, gym equipment, and outdoor workout areas. Hosts marathons and community sports events."
            }
        ],
        "reviews": [
            {
                "id": 1,
                "user_id": 1,
                "venue_id": 1,
                "rating": 5,
                "text": "Amazing facility! The basketball courts are top-notch and well-maintained.",
                "timestamp": "2025-01-15T10:30:00Z"
            },
            {
                "id": 2,
                "user_id": 2,
                "venue_id": 1,
                "rating": 4,
                "text": "Great place for team sports. Sometimes gets crowded on weekends.",
                "timestamp": "2025-01-16T14:20:00Z"
            },
            {
                "id": 3,
                "user_id": 1,
                "venue_id": 2,
                "rating": 5,
                "text": "Best tennis courts in the city! The instructors are fantastic.",
                "timestamp": "2025-01-17T09:15:00Z"
            }
        ]
    }

def load_db():
    with _lock:
        if not DB_PATH.exists():
            data = get_initial_data()
            save_db(data)
            return data
        try:
            with open(DB_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            data = get_initial_data()
            save_db(data)
            return data

def save_db(data):
    with _lock:
        with open(DB_PATH, 'w') as f:
            json.dump(data, f, indent=2)

def get_next_id(collection):
    if not collection:
        return 1
    return max(item['id'] for item in collection) + 1

def find_by_id(collection, item_id):
    for item in collection:
        if item['id'] == item_id:
            return item
    return None

def find_user_by_username(username):
    data = load_db()
    for user in data['users']:
        if user['username'].lower() == username.lower():
            return user
    return None
