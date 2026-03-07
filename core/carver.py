import os
import re
from datetime import datetime, timezone
from .models import RecoveredMessage

# Regex to match potential phone numbers (e.g., +1234567890, 123-456-7890, etc.)
PHONE_REGEX = re.compile(rb'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')

# Regex to match typical SQLite text payloads containing words
# This looks for sequences of printable characters > 5 chars
PRINTABLE_REGEX = re.compile(rb'[\x20-\x7E]{5,}') 
UTF16_REGEX = re.compile(rb'(?:[\x20-\x7E]\x00){5,}')

def extract_strings_from_binary(data: bytes) -> list[str]:
    """Extracts printable ASCII and UTF-16 strings from a binary blob."""
    strings = []
    
    # Extract ASCII/UTF-8
    for match in PRINTABLE_REGEX.finditer(data):
        try:
            val = match.group().decode('utf-8')
            # Filter out generic sqlite keywords
            if val.lower() not in ["table", "index", "sqlite_master", "create", "insert"]:
                strings.append(val)
        except UnicodeDecodeError:
            pass
            
    # Extract UTF-16 (common in iOS databases)
    for match in UTF16_REGEX.finditer(data):
        try:
            val = match.group().decode('utf-16le')
            if val.lower() not in ["table", "index", "sqlite_master"]:
                strings.append(val)
        except UnicodeDecodeError:
            pass
            
    return strings

def carve_deleted_messages(filepath: str, known_active_messages: list[RecoveredMessage]) -> list[RecoveredMessage]:
    """
    Scans a raw database file (and its WAL if present) for deleted text fragments.
    In a full forensic suite, this parses SQLite Free-pages. For this tool, we 
    carve data blocks and regex them to find strings not in the active set.
    """
    if not os.path.exists(filepath):
        return []
        
    carved_messages = []
    
    # Pluck out bodies from active messages for deduplication
    active_bodies = set([m.body for m in known_active_messages if m.body])
    
    files_to_scan = [filepath]
    
    # Also scan WAL and Journal files if they exist
    wal_path = filepath + "-wal"
    journal_path = filepath + "-journal"
    if os.path.exists(wal_path):
        files_to_scan.append(wal_path)
    if os.path.exists(journal_path):
        files_to_scan.append(journal_path)
        
    for file_to_scan in files_to_scan:
        with open(file_to_scan, "rb") as f:
            data = f.read()
            
            # Simple Text Carving
            found_strings = extract_strings_from_binary(data)
            
            # Simple heuristic: If string is long enough, and not an active message, flag it as a carved/suspicious fragment.
            # In a real rigorous B-Tree parser, we'd link the deleted cell to a timestamp. 
            # Here we present it as an "Orphaned/Deleted Fragment"
            for text_chunk in found_strings:
                if len(text_chunk) > 10 and text_chunk not in active_bodies:
                    
                    # We create a pseudo-message for the carved text
                    msg = RecoveredMessage(
                        timestamp=datetime.now(timezone.utc), # Real time unknown for free-page orphaned text
                        sender="Unknown (Carved)",
                        receiver="Unknown (Carved)",
                        body=f"[DELETED FRAGMENT]: {text_chunk}",
                        source_file=file_to_scan,
                        is_deleted=True,
                        service="Raw Carve"
                    )
                    carved_messages.append(msg)
                    # Add to active_bodies so we don't carve it twice
                    active_bodies.add(text_chunk)
                    
    return carved_messages
