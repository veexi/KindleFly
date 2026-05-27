import os
import json
import hashlib
from datetime import datetime

HISTORY_FILE = "sent_books.json"

class HistoryManager:
    def __init__(self, config_dir=None):
        if config_dir:
            self.history_path = os.path.join(config_dir, HISTORY_FILE)
        else:
            self.history_path = os.path.abspath(HISTORY_FILE)
        self.history = self.load_history()

    def load_history(self):
        """Loads sent history from JSON file."""
        if not os.path.exists(self.history_path):
            self.save_history({})
            return {}
        
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading history: {e}")
            return {}

    def save_history(self, history_data=None):
        """Saves history_data to JSON file."""
        if history_data is not None:
            self.history = history_data
        
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving history: {e}")
            return False

    def compute_md5(self, file_path):
        """Computes MD5 hash of a file."""
        if not os.path.exists(file_path):
            return None
        
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                # Read file in 64kb chunks to avoid loading large files fully into memory
                for chunk in iter(lambda: f.read(65536), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"Error computing MD5 for {file_path}: {e}")
            return None

    def is_already_sent(self, file_path, file_hash=None):
        """Checks if a file (by its MD5 hash or file path) was already sent."""
        if not file_hash:
            file_hash = self.compute_md5(file_path)
            if not file_hash:
                return False
        
        return file_hash in self.history

    def mark_as_sent(self, file_path, file_hash=None):
        """Marks a file as sent by saving its MD5 hash, filename, size, and sent timestamp."""
        if not file_hash:
            file_hash = self.compute_md5(file_path)
            if not file_hash:
                return False
        
        file_name = os.path.basename(file_path)
        file_size_bytes = os.path.getsize(file_path)
        
        # Human readable file size
        if file_size_bytes < 1024:
            file_size_str = f"{file_size_bytes} B"
        elif file_size_bytes < 1024 * 1024:
            file_size_str = f"{file_size_bytes / 1024:.1f} KB"
        else:
            file_size_str = f"{file_size_bytes / (1024 * 1024):.1f} MB"
            
        sent_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.history[file_hash] = {
            "file_name": file_name,
            "file_path": os.path.abspath(file_path),
            "file_size": file_size_str,
            "sent_at": sent_time
        }
        
        self.save_history()
        return True

    def clear_history(self):
        """Clears all sent history."""
        self.history = {}
        return self.save_history(self.history)

    def get_all_records(self):
        """Returns list of sent records sorted by sent time descending."""
        records = []
        for file_hash, data in self.history.items():
            record = data.copy()
            record["hash"] = file_hash
            records.append(record)
        
        # Sort by sent_at descending
        try:
            records.sort(key=lambda x: x.get("sent_at", ""), reverse=True)
        except Exception:
            pass
        return records
