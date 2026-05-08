"""Seed a test user + knowledge base, then test the ingestion endpoint."""
import uuid
import urllib.request
import json

# Create test data directly in SQLite
import sqlite3
test_user_id = str(uuid.uuid4())
test_kb_id = str(uuid.uuid4())

conn = sqlite3.connect('nexus.db')
conn.execute(
    "INSERT INTO users (id, email, hashed_password, role, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
    (test_user_id, f'test_{test_user_id}@nexus.dev', 'hashed_pw', 'admin', 1)
)
conn.execute(
    "INSERT INTO knowledge_bases (id, name, description, owner_id, created_at, updated_at) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))",
    (test_kb_id, 'Test KB', 'For testing ingestion', test_user_id)
)
conn.commit()
conn.close()

print(f"Created user:  {test_user_id}")
print(f"Created KB:    {test_kb_id}")

# Now test POST /api/v1/ingest/file
import io
import http.client

# Create a simple test PDF-like file
boundary = '----TestBoundary123'
body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="test.pdf"\r\n'
    f'Content-Type: application/pdf\r\n\r\n'
    f'%PDF-1.4 fake pdf content for testing\r\n'
    f'--{boundary}--\r\n'
).encode('utf-8')

conn = http.client.HTTPConnection('127.0.0.1', 8000)
conn.request(
    'POST',
    f'/api/v1/ingest/file?kb_id={test_kb_id}',
    body=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)
resp = conn.getresponse()
data = json.loads(resp.read().decode())
print(f"\nPOST /api/v1/ingest/file => {resp.status}")
print(json.dumps(data, indent=2))

if resp.status == 200:
    job_id = data['job_id']
    # Test GET /api/v1/ingest/jobs/{job_id}
    resp2_data = json.loads(urllib.request.urlopen(f'http://127.0.0.1:8000/api/v1/ingest/jobs/{job_id}').read().decode())
    print(f"\nGET /api/v1/ingest/jobs/{job_id} =>")
    print(json.dumps(resp2_data, indent=2))
    
    import time
    print("\nWaiting 3 seconds for Celery task...")
    time.sleep(3)
    
    resp3_data = json.loads(urllib.request.urlopen(f'http://127.0.0.1:8000/api/v1/ingest/jobs/{job_id}').read().decode())
    print(f"\nGET /api/v1/ingest/jobs/{job_id} (after 3s) =>")
    print(json.dumps(resp3_data, indent=2))

conn.close()
