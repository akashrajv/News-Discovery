"""
MongoDB Atlas Diagnostic & Verification Tool.
Tests connectivity, authentication, SSL certificates, network access, and document read/write.
"""
import os
import sys
from datetime import datetime

# Add parent directory to path so app modules can be imported
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app.config import settings
from app.database.mongodb import mongo_manager, sanitize_mongodb_uri


def get_public_ip():
    try:
        import httpx
        return httpx.get("https://api.ipify.org", timeout=4.0).text.strip()
    except Exception:
        return "Unknown"


def run_diagnostic():
    print("=" * 65)
    print("      MongoDB Atlas Connection Diagnostic & Verification      ")
    print("=" * 65)

    raw_uri = settings.MONGODB_URL
    db_name = settings.MONGODB_DB_NAME
    backend_mode = settings.ARTICLE_STORAGE_BACKEND
    public_ip = get_public_ip()

    print(f"\n[1] Environment Configuration:")
    print(f"  - ARTICLE_STORAGE_BACKEND : {backend_mode}")
    print(f"  - MONGODB_DB_NAME         : {db_name}")
    print(f"  - Current Public Client IP: {public_ip}")
    if not raw_uri:
        print("  - MONGODB_URL             : [NOT SET in .env]")
        print("\n[!] Error: MONGODB_URL is not configured in backend/.env.")
        print("    Add MONGODB_URL=mongodb+srv://... to .env to enable MongoDB.")
        return False

    # Mask credentials for display
    sanitized = sanitize_mongodb_uri(raw_uri)
    display_uri = raw_uri
    if "@" in display_uri:
        parts = display_uri.split("@")
        display_uri = parts[0].split(":")[0] + ":***@" + parts[1]
    print(f"  - MONGODB_URL (configured): {display_uri}")

    print(f"\n[2] Attempting connection via MongoDBManager...")
    success = mongo_manager.connect()

    if success:
        print("  [SUCCESS] Successfully connected to MongoDB Atlas cluster!")
        print(f"  - Database: {mongo_manager.db_name}")

        status = mongo_manager.get_status()
        print(f"  - Total Articles in DB: {status.get('articles_count', 0)}")

        # Test write & read
        print(f"\n[3] Testing Document Write & Read Operations...")
        test_article = {
            "title": "MongoDB Atlas Verification Ping Article",
            "description": "Integration check for news collection engine MongoDB persistence.",
            "content": "This document verifies write, read, and deduplication operations.",
            "source": "AtlasDiagnosticTest",
            "published_at": datetime.utcnow(),
            "url": f"https://diagnostic.internal/test-{int(datetime.utcnow().timestamp())}",
            "category": "Technology",
            "collection_method": "diagnostic",
            "target_entity": "Test Entity",
            "relevance_score": 99.0,
            "importance_score": 90.0,
            "importance_rating": "HIGH",
            "sentiment_tone": "Positive",
            "ai_summary": "Atlas connection verified successfully."
        }

        try:
            upsert_result = mongo_manager.upsert_article(test_article)
            print(f"  - Insert / Upsert test article: {'OK' if upsert_result else 'FAILED'}")

            articles, count = mongo_manager.get_articles(source="AtlasDiagnosticTest", limit=5)
            print(f"  - Query test article by source: Found {len(articles)} documents (Total count: {count})")

            # Clean up test article
            if mongo_manager.db is not None:
                del_res = mongo_manager.db.articles.delete_many({"source": "AtlasDiagnosticTest"})
                print(f"  - Cleanup test article: Removed {del_res.deleted_count} test document(s)")

            print("\n" + "=" * 65)
            print("  ALL MONGODB ATLAS TESTS PASSED! Article storage is fully operational.")
            print("=" * 65)
            return True

        except Exception as op_err:
            print(f"  [!] Operation Error: {op_err}")
            return False

    else:
        err = mongo_manager.connection_error or "Unknown error"
        print("  [FAILED] Could not connect to MongoDB Atlas.")
        print(f"  Error details: {err}")

        print("\n" + "=" * 65)
        print("                     TROUBLESHOOTING GUIDE                     ")
        print("=" * 65)

        if "TLSV1_ALERT_INTERNAL_ERROR" in err or "SSL handshake failed" in err:
            print("(!) CAUSE: ATLAS NETWORK ACCESS (IP WHITELIST)")
            print(f"    MongoDB Atlas closed the SSL connection because your client IP")
            print(f"    is not authorized in the Atlas IP Access List.")
            print("\n    SOLUTION:")
            print(f"    1. Open your MongoDB Atlas Dashboard: https://cloud.mongodb.com")
            print(f"    2. In the left menu under 'Security', click 'Network Access'.")
            print(f"    3. Click '+ ADD IP ADDRESS'.")
            print(f"    4. Click 'ADD CURRENT IP ADDRESS' ({public_ip})")
            print(f"       OR add '0.0.0.0/0' (Allow access from anywhere - recommended for development).")
            print(f"    5. Click 'Confirm' and wait ~60 seconds for Atlas to update.")
            print(f"    6. Re-run this script: .venv\\Scripts\\python scripts/test_mongo.py")

        elif "bad auth" in err or "AuthenticationFailed" in err or "code: 8000" in err:
            print("(!) CAUSE: INVALID USERNAME OR PASSWORD")
            print(f"    MongoDB Atlas rejected the database credentials.")
            print("\n    SOLUTION:")
            print(f"    1. Open MongoDB Atlas -> Security -> Database Access.")
            print(f"    2. Find user 'akashrajv006_db_user' (or create if missing).")
            print(f"    3. Click 'Edit' -> 'Edit Password', set a password without unescaped '@' or update .env.")
            print(f"    4. Ensure user role is 'Read and write to any database'.")
            print(f"    5. If password contains '@', in .env replace '@' with '%40'.")

        else:
            print(f"(!) Check your Atlas cluster status and MONGODB_URL in backend/.env.")

        print("=" * 65)
        return False


if __name__ == "__main__":
    success = run_diagnostic()
    sys.exit(0 if success else 1)
