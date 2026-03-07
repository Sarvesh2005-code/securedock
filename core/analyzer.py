from typing import List
from .models import RecoveredMessage

def deduplicate_messages(messages: List[RecoveredMessage]) -> List[RecoveredMessage]:
    """Removes duplicate message bodies (e.g., carved from both free pages and WAL)."""
    seen_bodies = set()
    deduped = []
    
    for msg in messages:
        if msg.body and msg.body not in seen_bodies:
            deduped.append(msg)
            seen_bodies.add(msg.body)
            
    return deduped

def sort_by_timestamp(messages: List[RecoveredMessage]) -> List[RecoveredMessage]:
    """Sorts messages chronologically. Messages with None timestamp go to the end."""
    # Ensure datetime parsing won't fail
    import datetime
    max_time = datetime.datetime.max
    # Timezone aware max_time
    max_time = max_time.replace(tzinfo=datetime.timezone.utc)
    
    return sorted(messages, key=lambda x: x.timestamp if x.timestamp else max_time)

def filter_by_keyword(messages: List[RecoveredMessage], keywords: List[str]) -> List[RecoveredMessage]:
    """Returns only messages that contain ANY of the given keywords (case-insensitive)."""
    if not keywords:
        return messages
        
    keyword_lower = [k.lower() for k in keywords]
    filtered = []
    
    for msg in messages:
        if not msg.body:
            continue
        body_lower = msg.body.lower()
        if any(k in body_lower for k in keyword_lower):
            filtered.append(msg)
            
    return filtered
