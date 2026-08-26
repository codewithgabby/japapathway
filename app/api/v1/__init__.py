# app/api/v1/__init__.py
from app.api.v1 import auth, users, system, pathways, admin_pathways
from app.api.v1 import documents, admin_documents
from app.api.v1 import sop, admin_sop
from app.api.v1 import content, admin_content
from app.api.v1 import dashboard

__all__ = [
    "auth",
    "users",
    "system",
    "pathways",
    "admin_pathways",
    "documents",
    "admin_documents",
    "sop",
    "admin_sop",
    "content",
    "admin_content",
    "dashboard"
]