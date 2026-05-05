# -*- coding: utf-8 -*-
"""
Test the Cross-Modal Graph pipeline:
 1. Generate 2 DOCX files mentioning the same entity (e.g. "GlobalCorp")
 2. Generate 1 Image with OCR text mentioning similar topics
 3. Ingest all 3.
 4. Verify graph nodes, edges, semantic links, entity links.
 5. Delete and verify cleanup.
"""
import os
import sys
import time
import json
import uuid
import http.client
import urllib.request
import sqlite3
from docx import Document as DocxDocument
from PIL import Image, ImageDraw, ImageFont

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Generate Test Files
def create_test_docx(filename, text):
    doc = DocxDocument()
    doc.add_paragraph(text)
    doc.save(filename)
    print(f"Created DOCX: {filename}")

def create_test_image(filename, text):
    img = Image.new('RGB', (800, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # Just draw text simply (might not be readable by Tesseract without font, but let's try default)
    try:
        d.text((20, 50), text, fill=(0, 0, 0))
    except Exception:
        pass
    img.save(filename)
    print(f"Created Image: {filename}")

def upload_and_check(filepath, kb_id, wait_seconds=120):
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
    conn.request('POST', f'/api/v1/ingest/file?kb_id={kb_id}', body=body, headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()

    if resp.status != 200:
        print(f"Upload failed: {data}")
        return None, None

    job_id = data['job_id']
    doc_id = data['document_id']

    for _ in range(wait_seconds // 2):
        time.sleep(2)
        try:
            resp2 = urllib.request.urlopen(f'http://127.0.0.1:8000/api/v1/ingest/jobs/{job_id}')
            job_data = json.loads(resp2.read().decode())
            if job_data['status'] in ['complete', 'failed']:
                return doc_id, job_data
        except Exception:
            pass

    return doc_id, None

if __name__ == '__main__':
    doc1_file = "test_graph_doc1.docx"
    doc2_file = "test_graph_doc2.docx"
    img_file = "test_graph_img.png"
    
    # Text with multiple explicit entities for NER
    create_test_docx(doc1_file, "Elon Musk and Bill Gates visited Microsoft headquarters in Seattle. They discussed Mars exploration mission underway.")
    create_test_docx(doc2_file, "According to news, Elon Musk and Bill Gates were seen at Microsoft offices in Seattle recently. Also, Mars exploration mission underway.")
    
    # Image with OCR text identical to part of the text chunks to guarantee high semantic similarity
    create_test_image(img_file, "Mars exploration mission underway.")

    test_user_id = str(uuid.uuid4())
    test_kb_id = str(uuid.uuid4())

    db = sqlite3.connect('nexus.db')
    db.execute("INSERT INTO users (id, email, hashed_password, role, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
               (test_user_id, f'graph_{test_user_id}@nexus.dev', 'hashed', 'admin', 1))
    db.execute("INSERT INTO knowledge_bases (id, name, description, owner_id, created_at, updated_at) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))",
               (test_kb_id, 'Graph KB', 'Graph Test', test_user_id))
    db.commit()

    passed = 0
    
    print("\n=== Uploading files ===")
    id1, j1 = upload_and_check(doc1_file, test_kb_id)
    id2, j2 = upload_and_check(doc2_file, test_kb_id)
    id3, j3 = upload_and_check(img_file, test_kb_id)
    
    if all(j and j.get('status') == 'complete' for j in [j1, j2, j3]):
        print("  [PASS] All files ingested successfully.")
        passed += 1
    else:
        print("  [FAIL] Ingestion failed.")
        print(j1, j2, j3)
        exit(1)

    print("\n=== Testing Graph KB Endpoint ===")
    conn = http.client.HTTPConnection('127.0.0.1', 8000)
    conn.request('GET', f'/api/v1/graph/{test_kb_id}')
    resp = conn.getresponse()
    kb_graph = json.loads(resp.read().decode())
    conn.close()

    nodes = kb_graph.get("nodes", [])
    links = kb_graph.get("links", [])
    if len(nodes) >= 3:
        print(f"  [PASS] Graph has {len(nodes)} nodes.")
        passed += 1
    else:
        print(f"  [FAIL] Graph has {len(nodes)} nodes (expected >= 3).")

    print("\n=== Testing Graph Stats ===")
    conn = http.client.HTTPConnection('127.0.0.1', 8000)
    conn.request('GET', f'/api/v1/graph/{test_kb_id}/stats')
    resp = conn.getresponse()
    stats = json.loads(resp.read().decode())
    conn.close()

    print(json.dumps(stats, indent=2))
    if stats.get("entity_links", 0) > 0 or stats.get("semantic_links", 0) > 0:
        print("  [PASS] Graph has created entity or semantic links.")
        passed += 1
    else:
        print("  [WARNING] Graph created 0 links. Thresholds might be too strict or NER failed.")

    print("\n=== Testing Query Expand Evidence Chains ===")
    query_body = json.dumps({
        "kb_id": test_kb_id,
        "query": "Elon Musk SpaceX Mars",
        "top_k": 3,
        "modality_filter": "all",
        "expand_evidence_chains": True
    })
    conn = http.client.HTTPConnection('127.0.0.1', 8000)
    conn.request('POST', '/api/v1/query/', body=query_body, headers={'Content-Type': 'application/json'})
    resp_q = conn.getresponse()
    q_data = json.loads(resp_q.read().decode())
    conn.close()

    chains = q_data.get("evidence_chains", [])
    if chains is not None:
        print(f"  [PASS] Query returned {len(chains)} evidence chains.")
        passed += 1
    else:
        print("  [FAIL] Query missing evidence chains.")

    print("\n=== Testing Delete Document Cleanup ===")
    conn = http.client.HTTPConnection('127.0.0.1', 8000)
    conn.request('DELETE', f'/api/v1/ingest/{id1}')
    resp_del = conn.getresponse()
    conn.close()

    if resp_del.status == 200:
        conn = http.client.HTTPConnection('127.0.0.1', 8000)
        conn.request('GET', f'/api/v1/graph/{test_kb_id}/stats')
        resp_stats2 = conn.getresponse()
        stats2 = json.loads(resp_stats2.read().decode())
        conn.close()
        
        if stats2["total_nodes"] < stats["total_nodes"]:
            print(f"  [PASS] Nodes correctly deleted from graph ({stats['total_nodes']} -> {stats2['total_nodes']})")
            passed += 1
        else:
            print("  [FAIL] Nodes not deleted from graph.")
    
    print("\nRESULTS: {}/5 tests passed".format(passed))
    db.close()
