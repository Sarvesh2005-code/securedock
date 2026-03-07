import sqlite3
import os
from datetime import datetime, timezone
from .models import RecoveredMessage

def convert_mac_absolute_time(timestamp_val) -> datetime:
    """Converts iOS Mac Absolute Time (seconds since Jan 1, 2001) to UTC datetime."""
    if not timestamp_val:
        return None
    try:
        # Mac Absolute Time epoch: Jan 1, 2001
        # Unix epoch: Jan 1, 1970 (difference is 978307200 seconds)
        # Sometime iOS uses 9 digits (seconds) sometimes 18 digits (nanoseconds)
        ts = float(timestamp_val)
        if ts > 10000000000:
            ts = ts / 1000000000 # convert nano to seconds
        unix_time = ts + 978307200
        return datetime.fromtimestamp(unix_time, timezone.utc)
    except Exception:
        return None

def convert_java_epoch_time(timestamp_val) -> datetime:
    """Converts Android Java Epoch Time (milliseconds since Jan 1, 1970) to UTC datetime."""
    if not timestamp_val:
        return None
    try:
        ts = float(timestamp_val)
        # Convert milliseconds to seconds
        if ts > 10000000000:
            ts = ts / 1000.0
        return datetime.fromtimestamp(ts, timezone.utc)
    except Exception:
        return None

def parse_ios_sms_db(filepath: str) -> list[RecoveredMessage]:
    """Parses an active, allocated iOS sms.db file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    messages = []
    try:
        # Read URI as file: to handle read-only mode so we don't accidentally modify evidence
        conn = sqlite3.connect(f"file:{filepath}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Determine schema (iOS versions change over time, but generally message + handle)
        query = """
            SELECT 
                message.rowid, 
                message.text, 
                message.is_from_me, 
                message.date, 
                handle.id as phone_number,
                message.service
            FROM message
            LEFT JOIN handle ON message.handle_id = handle.rowid
            WHERE message.text IS NOT NULL
        """
        
        cursor.execute(query)
        for row in cursor.fetchall():
            text = row['text']
            is_from_me = row['is_from_me']
            timestamp = convert_mac_absolute_time(row['date'])
            phone_number = row['phone_number'] or "Unknown"
            service = row['service'] or "SMS"
            
            sender = "Me" if is_from_me else phone_number
            receiver = phone_number if is_from_me else "Me"
            
            msg = RecoveredMessage(
                timestamp=timestamp,
                sender=sender,
                receiver=receiver,
                body=text,
                source_file=filepath,
                is_deleted=False,
                service=service
            )
            messages.append(msg)
            
    except sqlite3.Error as e:
        print(f"SQLite error parsing iOS db: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            
    return messages

def parse_android_sms_db(filepath: str) -> list[RecoveredMessage]:
    """Parses an active, allocated Android mmssms.db file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    messages = []
    try:
        conn = sqlite3.connect(f"file:{filepath}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Standard mmssms.db 'sms' table
        query = """
            SELECT 
                _id, 
                address, 
                date, 
                type, 
                body 
            FROM sms
            WHERE body IS NOT NULL
        """
        
        cursor.execute(query)
        for row in cursor.fetchall():
            text = row['body']
            # type 1 = Inbox (received), type 2 = Sent
            msg_type = row['type']
            timestamp = convert_java_epoch_time(row['date'])
            phone_number = row['address'] or "Unknown"
            
            sender = "Me" if msg_type == 2 else phone_number
            receiver = phone_number if msg_type == 2 else "Me"
            
            msg = RecoveredMessage(
                timestamp=timestamp,
                sender=sender,
                receiver=receiver,
                body=text,
                source_file=filepath,
                is_deleted=False,
                service="SMS"
            )
            messages.append(msg)
            
    except sqlite3.Error as e:
        print(f"SQLite error parsing Android db: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            
    return messages

def parse_bugle_db(filepath: str) -> list[RecoveredMessage]:
    """Parses an active, allocated Google Messages bugle_db file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    messages = []
    try:
        conn = sqlite3.connect(f"file:{filepath}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Bugle schema generally has parts.text and messages.timestamp
        query = """
            SELECT 
                messages._id,
                parts.text,
                messages.sender_id,
                messages.received_timestamp
            FROM parts
            INNER JOIN messages ON parts.message_id = messages._id
            WHERE parts.text IS NOT NULL AND parts.text != ''
        """
        
        cursor.execute(query)
        for row in cursor.fetchall():
            text = row['text']
            # Bugle timestamp is also Java Epoch (milliseconds) if received_timestamp > 0
            timestamp = convert_java_epoch_time(row['received_timestamp'])
            sender_id = str(row['sender_id']) if row['sender_id'] is not None else "Unknown"
            
            # Basic logic for sender/receiver in bugle
            # Usually sender_id = -1 or NULL means it's from 'Me'
            if sender_id == "-1" or sender_id == "None":
                sender = "Me"
                receiver = "Unknown recipient"
            else:
                sender = sender_id
                receiver = "Me"
            
            msg = RecoveredMessage(
                timestamp=timestamp,
                sender=sender,
                receiver=receiver,
                body=text,
                source_file=filepath,
                is_deleted=False,
                service="Google Messages"
            )
            messages.append(msg)
            
    except sqlite3.Error as e:
        print(f"SQLite error parsing Bugle db: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            
    return messages

def auto_detect_and_parse(filepath: str) -> list[RecoveredMessage]:
    """Attempts to auto-detect db type based on schema and extracts messages."""
    try:
        conn = sqlite3.connect(f"file:{filepath}?mode=ro", uri=True)
        cursor = conn.cursor()
        
        # Check for iOS standard tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='message';")
        has_message = cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='handle';")
        has_handle = cursor.fetchone() is not None
        
        # Check for Android standard tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sms';")
        has_sms = cursor.fetchone() is not None
        
        # Check for Google Messages Bugle tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parts';")
        has_parts = cursor.fetchone() is not None
        
        conn.close()
        
        if len(filepath) > 0: # Check filename specifically 
            pass # can add logic based on filename later
            
        if has_message and has_handle and not has_parts:
            print("Detected iOS sms.db format.")
            return parse_ios_sms_db(filepath)
        elif has_parts and has_message:
            print("Detected Google Messages bugle_db format.")
            return parse_bugle_db(filepath)
        elif has_sms:
            print("Detected Android mmssms.db format.")
            return parse_android_sms_db(filepath)
        else:
            print("Unsupported or unrecognized database format. (Only active iOS SMS, Android SMS, and Bugle tables are auto-detected so far.)")
            return []
            
    except Exception as e:
        print(f"Failed to auto-detect DB: {e}")
        return []
