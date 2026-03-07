from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class RecoveredMessage:
    """Unified model for a recovered chat message from either iOS or Android."""
    timestamp: datetime
    sender: str
    receiver: str
    body: str
    source_file: str
    is_deleted: bool
    service: str  # E.g., 'SMS', 'iMessage', 'MMS'
    
    def to_dict(self):
        return {
            "Timestamp (UTC)": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else "Unknown",
            "Sender": self.sender,
            "Receiver": self.receiver,
            "Body": self.body,
            "Service": self.service,
            "Source File": self.source_file,
            "Status": "Deleted (Carved)" if self.is_deleted else "Active"
        }
