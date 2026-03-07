import os
from core.db_parser import auto_detect_and_parse
from core.carver import carve_deleted_messages
from core.analyzer import filter_by_keyword

def verify():
    print("--- Verifying Android DB ---")
    android_db = "tests/mock_mmssms.db"
    active_android = auto_detect_and_parse(android_db)
    print(f"Active Android found: {len(active_android)}")
    assert len(active_android) == 2
    
    deleted_android = carve_deleted_messages(android_db, active_android)
    print(f"Deleted Android carved: {len(deleted_android)}")
    
    # Due to padding or encoding, pure text carving is a heuristic. Let's see if our deleted strings are there.
    all_android = active_android + deleted_android
    found_secret = filter_by_keyword(all_android, ["Top Secret"])
    assert len(found_secret) > 0, "Failed to carve Android deleted message"
    print("Android verification SUCCESS")

    print("\n--- Verifying iOS DB ---")
    ios_db = "tests/mock_sms.db"
    active_ios = auto_detect_and_parse(ios_db)
    print(f"Active iOS found: {len(active_ios)}")
    assert len(active_ios) == 2
    
    deleted_ios = carve_deleted_messages(ios_db, active_ios)
    print(f"Deleted iOS carved: {len(deleted_ios)}")
    
    all_ios = active_ios + deleted_ios
    found_briefcase = filter_by_keyword(all_ios, ["briefcase"])
    assert len(found_briefcase) > 0, "Failed to carve iOS deleted message"
    print("iOS verification SUCCESS")
    
if __name__ == "__main__":
    verify()
