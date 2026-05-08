# -*- coding: utf-8 -*-
"""
Test the full audio pipeline:
 1. Generate a WAV file (sine tone — no speech detected is OK).
 2. Upload it to the ingestion endpoint.
 3. Poll the job until it completes.
 4. Verify transcript endpoint behaviour.
 5. Test query endpoint with exclude_modalities.
 6. Delete the document.
"""

import os
import sys
import json
import time
import uuid
import struct
import math
import http.client
import urllib.request
import sqlite3

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


def generate_tone_wav(filepath, duration=5.0, freq=440.0, sample_rate=16000):
    """Generate a minimal valid WAV file with a sine tone."""
    num_samples = int(sample_rate * duration)
    max_amplitude = 32767

    with open(filepath, 'wb') as f:
        data_size = num_samples * 2
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', sample_rate * 2))
        f.write(struct.pack('<H', 2))
        f.write(struct.pack('<H', 16))
        f.write(b'data')
        f.write(struct.pack('<I', data_size))

        for i in range(num_samples):
            sample = int(max_amplitude * math.sin(2 * math.pi * freq * i / sample_rate))
            f.write(struct.pack('<h', sample))

    print(f"Generated tone WAV: {filepath}  ({os.path.getsize(filepath)} bytes)")


def upload_and_check(filepath, kb_id, wait_seconds=120):
    """Upload a file and poll the ingestion job to completion."""
    filename = os.path.basename(filepath)
    boundary = '----TestBoundary456'

    with open(filepath, 'rb') as f:
        file_data = f.read()

    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f'Content-Type: application/octet-stream\r\n\r\n'.encode('utf-8') +
        file_data +
        f'\r\n--{boundary}--\r\n'.encode('utf-8')
    )

    conn = http.client.HTTPConnection('127.0.0.1', 8000)
    conn.request(
        'POST',
        f'/api/v1/ingest/file?kb_id={kb_id}',
        body=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    print(f"\nPOST {filename} => {resp.status}")
    print(json.dumps(data, indent=2))
    conn.close()

    if resp.status != 200:
        return None, None

    job_id = data['job_id']
    doc_id = data['document_id']

    job_data = None
    for _ in range(wait_seconds // 2):
        time.sleep(2)
        try:
            resp2 = urllib.request.urlopen(f'http://127.0.0.1:8000/api/v1/ingest/jobs/{job_id}')
            job_data = json.loads(resp2.read().decode())
            status = job_data['status']
            if status in ['complete', 'failed']:
                print(f"\nGET /jobs/{job_id} =>")
                print(json.dumps(job_data, indent=2))
                break
            else:
                print(f"Status: {status} (progress: {job_data.get('progress_pct', '?')}%)... waiting")
        except Exception as e:
            print(f"Error checking job: {e}")

    return doc_id, job_data


if __name__ == '__main__':
    wav_file = "test_audio.wav"
    generate_tone_wav(wav_file, duration=5.0)

    # Create test user + KB
    test_user_id = str(uuid.uuid4())
    test_kb_id = str(uuid.uuid4())

    db = sqlite3.connect('nexus.db')
    db.execute(
        "INSERT INTO users (id, email, hashed_password, role, is_active, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
        (test_user_id, f'test_{test_user_id}@nexus.dev', 'hashed_pw', 'admin', 1)
    )
    db.execute(
        "INSERT INTO knowledge_bases (id, name, description, owner_id, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))",
        (test_kb_id, 'Audio Test KB', 'For testing audio ingestion', test_user_id)
    )
    db.commit()

    passed = 0
    total = 5

    # ── TEST 1: Upload WAV ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("TEST 1: Upload WAV file and complete ingestion")
    print("=" * 60)
    doc_id, job_data = upload_and_check(wav_file, test_kb_id, wait_seconds=120)

    if not doc_id or not job_data or job_data.get('status') != 'complete':
        print("\n!! Audio ingestion failed -- aborting remaining tests.")
        db.close()
        exit(1)

    print("  [PASS] Audio ingestion completed successfully")
    passed += 1

    # ── TEST 2: Transcript endpoint ────────────────────────────────────
    print("\n" + "=" * 60)
    print("TEST 2: GET /api/v1/ingest/{doc_id}/transcript")
    print("=" * 60)
    conn = http.client.HTTPConnection('127.0.0.1', 8000)
    conn.request('GET', f'/api/v1/ingest/{doc_id}/transcript')
    resp_tr = conn.getresponse()
    transcript_data = json.loads(resp_tr.read().decode())
    print(f"GET /transcript => {resp_tr.status}")
    conn.close()

    # A sine tone produces no speech, so expect 404 or a transcript with chunks
    if resp_tr.status == 404:
        print("  [PASS] Transcript endpoint correctly returned 404 (no speech in sine tone)")
        passed += 1
    elif resp_tr.status == 200 and "chunks" in transcript_data:
        print(f"  [PASS] Transcript returned with {len(transcript_data['chunks'])} chunks")
        passed += 1
    else:
        print(f"  [FAIL] Unexpected response: {resp_tr.status}")

    # ── TEST 3: Query modality_filter="all" ────────────────────────────
    print("\n" + "=" * 60)
    print('TEST 3: Query with modality_filter="all"')
    print("=" * 60)
    query_body = json.dumps({
        "kb_id": test_kb_id,
        "query": "machine learning and neural networks",
        "top_k": 5,
        "modality_filter": "all"
    })
    conn = http.client.HTTPConnection('127.0.0.1', 8000)
    conn.request('POST', '/api/v1/query/', body=query_body, headers={'Content-Type': 'application/json'})
    resp_q = conn.getresponse()
    query_data = json.loads(resp_q.read().decode())
    print(f"POST /query (all) => {resp_q.status}")
    conn.close()

    if resp_q.status == 200:
        print(f"  [PASS] Query returned {query_data['total_results']} results")
        # Verify audio results have timestamps (if any)
        for r in query_data.get("results", []):
            if r["modality"] == "audio":
                assert r["timestamp_start"] is not None, "audio result missing timestamp_start"
                assert r["timestamp_end"] is not None, "audio result missing timestamp_end"
                print(f"    Audio chunk {r['chunk_id']}: [{r['timestamp_start']}s - {r['timestamp_end']}s]")
        passed += 1
    else:
        print(f"  [FAIL] Query endpoint returned {resp_q.status}")

    # ── TEST 4: Query with exclude_modalities=["audio"] ────────────────
    print("\n" + "=" * 60)
    print('TEST 4: Query with exclude_modalities=["audio"]')
    print("=" * 60)
    query_body_excl = json.dumps({
        "kb_id": test_kb_id,
        "query": "machine learning and neural networks",
        "top_k": 5,
        "modality_filter": "text",
        "exclude_modalities": ["audio"]
    })
    conn = http.client.HTTPConnection('127.0.0.1', 8000)
    conn.request('POST', '/api/v1/query/', body=query_body_excl, headers={'Content-Type': 'application/json'})
    resp_ex = conn.getresponse()
    excl_data = json.loads(resp_ex.read().decode())
    print(f"POST /query (exclude audio) => {resp_ex.status}")
    conn.close()

    audio_results = [r for r in excl_data.get("results", []) if r["modality"] == "audio"]
    if resp_ex.status == 200 and len(audio_results) == 0:
        print("  [PASS] No audio results returned when exclude_modalities=['audio']")
        passed += 1
    else:
        print(f"  [FAIL] Got {len(audio_results)} audio results (expected 0)")

    # ── TEST 5: Delete the audio document ──────────────────────────────
    print("\n" + "=" * 60)
    print("TEST 5: DELETE audio document")
    print("=" * 60)
    conn = http.client.HTTPConnection('127.0.0.1', 8000)
    conn.request('DELETE', f'/api/v1/ingest/{doc_id}')
    resp_del = conn.getresponse()
    del_data = json.loads(resp_del.read().decode())
    print(f"DELETE /{doc_id} => {resp_del.status}")
    conn.close()

    if resp_del.status == 200:
        print("  [PASS] Document deleted successfully")
        passed += 1
    else:
        print(f"  [FAIL] Delete returned {resp_del.status}")

    # ── Summary ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 60)

    db.close()

    if passed == total:
        print("\nALL AUDIO PIPELINE TESTS PASSED!")
        exit(0)
    else:
        print(f"\n{total - passed} test(s) failed.")
        exit(1)
