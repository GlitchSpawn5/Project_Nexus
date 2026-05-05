import os
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, engine, SessionLocal
from app.db.models.user import User

print("=== Starting Authentication and RBAC Tests ===")

# Force DB sync
Base.metadata.create_all(bind=engine)

# Wait for seed_admin_user to have been executed (it's imported in main.py)
# Test client automatically triggers app initialization
client = TestClient(app)

db = SessionLocal()
admin_user = db.query(User).filter(User.email == "admin@nexus.local").first()
assert admin_user is not None, "Admin user should be seeded!"
assert admin_user.role.value == "admin", "Seed user should be admin"
print("✓ Admin user seeded successfully.")

# 1. Register a new user
resp = client.post("/api/v1/auth/register", json={
    "email": "test@viewer.local",
    "password": "password123",
    "full_name": "Test Viewer"
})
assert resp.status_code == 200, f"Register failed: {resp.text}"
viewer_data = resp.json()
print("✓ User registered.")

# 2. Login
resp = client.post("/api/v1/auth/login", data={
    "username": "test@viewer.local",
    "password": "password123"
})
assert resp.status_code == 200, "Login failed"
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✓ User login successful, token retrieved.")

# 3. /me profile
resp = client.get("/api/v1/auth/me", headers=headers)
assert resp.status_code == 200
assert resp.json()["email"] == "test@viewer.local"
print("✓ /me endpoint works correctly.")

# 4. KB Creation & Access Control
resp = client.post("/api/v1/kb/", json={
    "name": "Viewer's KB",
    "description": "A test KB"
}, headers=headers)
assert resp.status_code == 200
kb_id = resp.json()["id"]
print("✓ Created KB as viewer.")

# List KBs (viewer only sees their own)
resp = client.get("/api/v1/kb/", headers=headers)
assert resp.status_code == 200
assert len(resp.json()) == 1, "Viewer should only see their own KB"

# Admin tries to fetch KBs (login as admin)
resp_admin = client.post("/api/v1/auth/login", data={
    "username": "admin@nexus.local",
    "password": "changeme123"
})
admin_token = resp_admin.json()["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}

resp = client.get("/api/v1/kb/", headers=admin_headers)
assert resp.status_code == 200
assert len(resp.json()) >= 1, "Admin should see all KBs"
print("✓ KB Isolation enforced.")

# 5. Accessing Admin Endpoints as Viewer (Should Fail)
resp = client.get("/api/v1/admin/users", headers=headers)
assert resp.status_code == 403, "Viewer should get 403 on admin endpoints"
print("✓ Viewer denied from admin endpoints (403).")

# 6. Accessing Admin Endpoints as Admin
resp = client.get("/api/v1/admin/users", headers=admin_headers)
assert resp.status_code == 200, "Admin should be able to access users list"
print("✓ Admin successfully accessed users list.")

# 7. Unauthenticated Access (Should Fail)
resp = client.get("/api/v1/kb/")
assert resp.status_code == 401, "No token should yield 401"
print("✓ Unauthenticated access denied (401).")

# 8. Public Health Check
resp = client.get("/health")
assert resp.status_code == 200, "Health check should be public"
print("✓ Health check remains public.")

print("\n=== All Tests Passed! ===")
