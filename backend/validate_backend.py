"""
Comprehensive Backend Validation Script
Tests all modules, imports, endpoints, and configurations.
"""
import sys
import os
import importlib
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("EPC-INTEL BACKEND - COMPREHENSIVE VALIDATION")
print("=" * 60)

errors = []
warnings = []
passes = []

# ========== 1. MODULE IMPORT CHECKS ==========
print("\n[1] MODULE IMPORT CHECKS")
print("-" * 40)

modules_to_check = [
    "app.core.config",
    "app.core.security",
    "app.db.base",
    "app.modules.auth.models",
    "app.modules.auth.schemas",
    "app.modules.auth.router",
    "app.modules.projects.models",
    "app.modules.documents.models",
    "app.modules.documents.schemas",
    "app.modules.documents.router",
    "app.modules.compliance.models",
    "app.modules.compliance.service",
    "app.modules.rfi.models",
    "app.modules.rfi.schemas",
    "app.modules.rfi.router",
    "app.modules.rfi.service",
    "app.shared.storage.s3_client",
    "app.shared.ai.embedding_client",
    "app.main",
]

for mod_name in modules_to_check:
    try:
        importlib.import_module(mod_name)
        passes.append(f"Import: {mod_name}")
        print(f"  ✅ {mod_name}")
    except Exception as e:
        errors.append(f"Import: {mod_name} -> {e}")
        print(f"  ❌ {mod_name} -> {e}")

# ========== 2. CONFIG CHECKS ==========
print("\n[2] CONFIGURATION CHECKS")
print("-" * 40)

from app.core.config import settings

config_checks = {
    "PROJECT_NAME": settings.PROJECT_NAME,
    "API_V1_STR": settings.API_V1_STR,
    "DATABASE_URL": settings.DATABASE_URL,
    "JWT_SECRET": settings.JWT_SECRET,
    "S3_ENDPOINT": settings.S3_ENDPOINT,
    "S3_BUCKET": settings.S3_BUCKET,
    "REDIS_URL": settings.REDIS_URL,
    "GEMINI_API_KEY": "***" + settings.GEMINI_API_KEY[-6:] if settings.GEMINI_API_KEY else "(EMPTY)",
    "EMBEDDING_MODEL": settings.EMBEDDING_MODEL,
}

for key, val in config_checks.items():
    if val:
        passes.append(f"Config: {key}")
        print(f"  ✅ {key} = {val}")
    else:
        warnings.append(f"Config: {key} is empty/None")
        print(f"  ⚠️  {key} = (empty)")

# ========== 3. ROUTE REGISTRATION CHECKS ==========
print("\n[3] ROUTE REGISTRATION CHECKS")
print("-" * 40)

from app.main import app

expected_routes = [
    ("GET", "/health"),
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/logout"),
    ("POST", "/api/v1/documents"),
    ("GET", "/api/v1/documents/{document_id}"),
    ("GET", "/api/v1/documents/{document_id}/status"),
    ("POST", "/api/v1/rfi/chat"),
]

registered = set()
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        for method in route.methods:
            registered.add((method, route.path))

for method, path in expected_routes:
    if (method, path) in registered:
        passes.append(f"Route: {method} {path}")
        print(f"  ✅ {method} {path}")
    else:
        errors.append(f"Route: {method} {path} NOT REGISTERED")
        print(f"  ❌ {method} {path} NOT REGISTERED")

# ========== 4. MODEL / SCHEMA CHECKS ==========
print("\n[4] MODEL & SCHEMA VALIDATION")
print("-" * 40)

# Check all SQLAlchemy models have __tablename__
from app.modules.auth.models import User
from app.modules.projects.models import Project
from app.modules.documents.models import Document, DocumentChunk
from app.modules.compliance.models import Vendor, Specification, Submittal, Deviation
from app.modules.rfi.models import Rfi, ChatSession, ChatMessage

models = [User, Project, Document, DocumentChunk, Vendor, Specification, Submittal, Deviation, Rfi, ChatSession, ChatMessage]

for model in models:
    name = model.__name__
    table = getattr(model, '__tablename__', None)
    if table:
        passes.append(f"Model: {name} -> {table}")
        print(f"  ✅ {name} -> table '{table}'")
    else:
        errors.append(f"Model: {name} has no __tablename__")
        print(f"  ❌ {name} has no __tablename__")

# Check Pydantic schemas
from app.modules.auth.schemas import UserCreate, UserLogin, UserResponse, Token, TokenPayload
from app.modules.documents.schemas import DocumentResponse, DocumentStatusResponse
from app.modules.rfi.schemas import ChatRequest, ChatResponse

schemas = [UserCreate, UserLogin, UserResponse, Token, TokenPayload, DocumentResponse, DocumentStatusResponse, ChatRequest, ChatResponse]

for schema in schemas:
    name = schema.__name__
    fields = list(schema.model_fields.keys())
    passes.append(f"Schema: {name} fields={fields}")
    print(f"  ✅ {name} -> fields: {fields}")

# ========== 5. SECURITY CHECKS ==========
print("\n[5] SECURITY / JWT CHECKS")
print("-" * 40)

from app.core.security import create_access_token, create_refresh_token, verify_password, get_password_hash

try:
    hashed = get_password_hash("test_password")
    assert verify_password("test_password", hashed), "Password verification failed"
    passes.append("Security: password hash/verify")
    print("  ✅ Password hash + verify works")
except Exception as e:
    errors.append(f"Security: password hash/verify -> {e}")
    print(f"  ❌ Password hash/verify -> {e}")

try:
    token = create_access_token(subject="user-123", role="Admin")
    assert len(token) > 20, "Token too short"
    passes.append("Security: access token creation")
    print(f"  ✅ Access token creation works (len={len(token)})")
except Exception as e:
    errors.append(f"Security: access token -> {e}")
    print(f"  ❌ Access token -> {e}")

try:
    rtoken = create_refresh_token(subject="user-123")
    assert len(rtoken) > 20, "Refresh token too short"
    passes.append("Security: refresh token creation")
    print(f"  ✅ Refresh token creation works (len={len(rtoken)})")
except Exception as e:
    errors.append(f"Security: refresh token -> {e}")
    print(f"  ❌ Refresh token -> {e}")

# ========== 6. EMBEDDING CLIENT CHECK ==========
print("\n[6] EMBEDDING CLIENT CHECK")
print("-" * 40)

try:
    from app.shared.ai.embedding_client import get_embedding, get_embeddings
    emb = get_embedding("test sentence for embedding")
    assert isinstance(emb, list), f"Expected list, got {type(emb)}"
    assert len(emb) == 384, f"Expected 384 dims, got {len(emb)}"
    passes.append(f"Embedding: get_embedding works (dims={len(emb)})")
    print(f"  ✅ get_embedding works -> {len(emb)} dimensions")
except Exception as e:
    errors.append(f"Embedding: {e}")
    print(f"  ❌ get_embedding -> {e}")

# ========== 7. S3 CLIENT CHECK ==========
print("\n[7] S3/MINIO CLIENT CHECK")
print("-" * 40)

from app.shared.storage.s3_client import s3_client
if s3_client._client is None:
    passes.append("S3: Lazy init confirmed (no premature connection)")
    print("  ✅ S3 client is lazy (no connection at import time)")
else:
    warnings.append("S3: Client was already initialized at import time")
    print("  ⚠️  S3 client was initialized at import time")

# ========== 8. CORS CHECK ==========
print("\n[8] CORS MIDDLEWARE CHECK")
print("-" * 40)

cors_found = False
for middleware in app.user_middleware:
    if "CORSMiddleware" in str(middleware):
        cors_found = True
        break

if cors_found:
    passes.append("CORS: middleware registered")
    print("  ✅ CORS middleware is registered")
else:
    errors.append("CORS: middleware NOT registered")
    print("  ❌ CORS middleware NOT registered")

# ========== SUMMARY ==========
print("\n" + "=" * 60)
print("VALIDATION SUMMARY")
print("=" * 60)
print(f"  ✅ PASSED:   {len(passes)}")
print(f"  ⚠️  WARNINGS: {len(warnings)}")
print(f"  ❌ ERRORS:   {len(errors)}")

if errors:
    print("\n--- ERRORS ---")
    for e in errors:
        print(f"  ❌ {e}")

if warnings:
    print("\n--- WARNINGS ---")
    for w in warnings:
        print(f"  ⚠️  {w}")

print("\n" + "=" * 60)
if not errors:
    print("🎉 ALL CHECKS PASSED — Backend is ready!")
else:
    print(f"🚨 {len(errors)} error(s) found — needs attention")
print("=" * 60)
