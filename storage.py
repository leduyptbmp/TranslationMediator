import json
import os
from typing import Dict, List, Optional
from config import USER_DATA_FILE, CHANNEL_DATA_FILE

class Storage:
    def __init__(self):
        self.user_data: Dict = self._load_data(USER_DATA_FILE)
        self.channel_data: Dict = self._load_data(CHANNEL_DATA_FILE)

    def _load_data(self, filename: str) -> Dict:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}

    def _save_data(self, data: Dict, filename: str) -> None:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def get_user_preferences(self, user_id: int) -> Dict:
        return self.user_data.get(str(user_id), {
            'target_language': 'en',
            'subscribed_channels': [],
            'notifications_enabled': True
        })

    def set_user_preferences(self, user_id: int, preferences: Dict) -> None:
        self.user_data[str(user_id)] = preferences
        self._save_data(self.user_data, USER_DATA_FILE)

    def add_channel_subscription(self, user_id: int, channel_id: str) -> None:
        if str(user_id) not in self.user_data:
            self.user_data[str(user_id)] = self.get_user_preferences(user_id)
        
        if channel_id not in self.user_data[str(user_id)]['subscribed_channels']:
            self.user_data[str(user_id)]['subscribed_channels'].append(channel_id)
            self._save_data(self.user_data, USER_DATA_FILE)

    def remove_channel_subscription(self, user_id: int, channel_id: str) -> None:
        if str(user_id) in self.user_data:
            if channel_id in self.user_data[str(user_id)]['subscribed_channels']:
                self.user_data[str(user_id)]['subscribed_channels'].remove(channel_id)
                self._save_data(self.user_data, USER_DATA_FILE)

    def get_subscribed_channels(self, user_id: int) -> List[str]:
        return self.get_user_preferences(user_id).get('subscribed_channels', [])
