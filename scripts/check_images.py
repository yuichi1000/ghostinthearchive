import os
import json
import firebase_admin
from firebase_admin import firestore, storage
from pathlib import Path

def check_mysteries_and_storage():
    # Use emulator if host is set
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    os.environ["STORAGE_EMULATOR_HOST"] = "localhost:9199"
    
    project_id = "ghostinthearchive"
    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            options={
                "projectId": project_id,
                "storageBucket": f"{project_id}.appspot.com",
            }
        )
    
    db = firestore.client()
    mysteries = db.collection("mysteries").order_by("createdAt", direction=firestore.Query.DESCENDING).limit(5).get()
    
    print("--- Recent Mysteries ---")
    results = []
    for m in mysteries:
        data = m.to_dict()
        results.append({
            "id": m.id,
            "mystery_id": data.get("mystery_id"),
            "images": data.get("images")
        })
    print(json.dumps(results, indent=2, ensure_ascii=False))

    print("\n--- Storage Check ---")
    try:
        bucket = storage.bucket()
        blobs = list(bucket.list_blobs(max_results=10))
        print(f"Found {len(blobs)} blobs in bucket {bucket.name}")
        for b in blobs:
            print(f" - {b.name} ({b.content_type})")
            
        # Try a test upload
        test_file = Path("test_upload.txt")
        test_file.write_text("hello emulator")
        blob = bucket.blob("test/hello.txt")
        blob.upload_from_filename(str(test_file))
        print(f"Test upload successful: {blob.name}")
        test_file.unlink()
    except Exception as e:
        print(f"Storage Error: {e}")

if __name__ == "__main__":
    check_mysteries_and_storage()
