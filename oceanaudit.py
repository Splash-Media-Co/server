import json
from datetime import datetime

class OceanAuditLogger:
    def __init__(self, log_file_path='audit.log'):
        self.log_file_path = log_file_path

    def log_action(self, action_type, user, details):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'action_type': action_type,
            'user': user,
            'details': details
        }
        self._write_to_log(log_entry)

    def _write_to_log(self, log_entry):
        with open(self.log_file_path, 'a') as log_file:
            log_file.write(json.dumps(log_entry) + '\n')