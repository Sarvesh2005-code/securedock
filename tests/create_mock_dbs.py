import sqlite3
import os
import time

def create_mock_android_db(filepath="tests/mock_mmssms.db"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    conn = sqlite3.connect(filepath)
    c = conn.cursor()
    
    # Create standard Android SMS table
    c.execute('''CREATE TABLE sms
                 (_id INTEGER PRIMARY KEY, address TEXT, date INTEGER, type INTEGER, body TEXT)''')
                 
    java_now = int(time.time() * 1000)
    
    # Active Messages
    c.execute("INSERT INTO sms (address, date, type, body) VALUES ('+15551234567', ?, 1, 'Hello, checking in on the report.')", (java_now - 100000,))
    c.execute("INSERT INTO sms (address, date, type, body) VALUES ('+15551234567', ?, 2, 'I will send the report tonight.')", (java_now - 50000,))
    
    # Message to be deleted
    c.execute("INSERT INTO sms (address, date, type, body) VALUES ('+19996660000', ?, 1, 'Top Secret: Delete this message immediately after reading.')", (java_now,))
    conn.commit()
    
    # Now Delete it so it becomes unallocated/carvable
    c.execute("DELETE FROM sms WHERE address='+19996660000'")
    conn.commit()
    conn.close()
    
def create_mock_ios_db(filepath="tests/mock_sms.db"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    conn = sqlite3.connect(filepath)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE handle (rowid INTEGER PRIMARY KEY, id TEXT)''')
    c.execute('''CREATE TABLE message (rowid INTEGER PRIMARY KEY, text TEXT, is_from_me INTEGER, handle_id INTEGER, date INTEGER, service TEXT)''')
    
    mac_now = int(time.time() - 978307200)
    
    # Insert Handlers
    c.execute("INSERT INTO handle (rowid, id) VALUES (1, '+18885551111')")
    c.execute("INSERT INTO handle (rowid, id) VALUES (2, 'john.doe@apple.com')")
    
    # Active
    c.execute("INSERT INTO message (text, is_from_me, handle_id, date, service) VALUES ('Are we still on for the meeting?', 0, 1, ?, 'SMS')", (mac_now - 5000,))
    c.execute("INSERT INTO message (text, is_from_me, handle_id, date, service) VALUES ('Yes, see you there.', 1, 1, ?, 'SMS')", (mac_now - 4000,))
    
    # To be deleted
    c.execute("INSERT INTO message (text, is_from_me, handle_id, date, service) VALUES ('The briefcase is under the bridge.', 0, 2, ?, 'iMessage')", (mac_now - 1000,))
    conn.commit()
    
    c.execute("DELETE FROM message WHERE handle_id=2")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_mock_android_db()
    create_mock_ios_db()
    print("Mock databases created in tests/")
