# verify_sprint3.py
"""
Sprint 3 Verification Script
Run this after starting the server to test all document readiness endpoints.
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def test_admin_auth():
    print("\nTesting Admin Authentication...")
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/auth/login", json={
            "email": "admin@appname.com",
            "password": "changeme123"
        })
        if response.status_code == 200:
            tokens = response.json()
            print("Admin login successful")
            return {"Authorization": f"Bearer {tokens['access_token']}"}
        else:
            print(f" Admin login failed: {response.status_code}")
            return None

async def test_user_auth():
    print("\n Testing User Authentication...")
    async with httpx.AsyncClient() as client:
        # Try register
        response = await client.post(f"{BASE_URL}/auth/register", json={
            "email": "doctest@example.com",
            "password": "testpassword123",
            "full_name": "Document Test User"
        })
        if response.status_code == 200:
            tokens = response.json()
            print("Test user registered")
            return {"Authorization": f"Bearer {tokens['access_token']}"}
        else:
            # Try login
            response = await client.post(f"{BASE_URL}/auth/login", json={
                "email": "doctest@example.com",
                "password": "testpassword123"
            })
            if response.status_code == 200:
                tokens = response.json()
                print("Test user logged in")
                return {"Authorization": f"Bearer {tokens['access_token']}"}
            else:
                print(" User auth failed")
                return None

async def test_admin_document_categories(headers):
    print("\n📂 Testing Admin Document Categories...")
    async with httpx.AsyncClient(headers=headers) as client:
        # List categories
        response = await client.get(f"{BASE_URL}/admin/document-categories")
        if response.status_code == 200:
            categories = response.json()
            print(f"Got {len(categories)} document categories")
            for cat in categories:
                print(f"   - {cat['name']} ({cat['slug']})")
        else:
            print(f"Failed to list categories: {response.status_code}")
            return None
        
        # Create new category
        print("\nCreating test category...")
        new_category = {
            "name": "Professional",
            "slug": "professional",
            "description": "Professional certifications and memberships",
            "sort_order": 9
        }
        response = await client.post(f"{BASE_URL}/admin/document-categories", json=new_category)
        if response.status_code == 201:
            category = response.json()
            print(f"Created category: {category['name']}")
            return category['id']
        else:
            print(f"Failed to create category: {response.status_code}")
            return None

async def test_admin_document_types(headers, category_id):
    print("\nTesting Admin Document Types...")
    async with httpx.AsyncClient(headers=headers) as client:
        # List all types
        response = await client.get(f"{BASE_URL}/admin/document-types")
        if response.status_code == 200:
            types = response.json()
            print(f"Got {len(types)} document types")
        else:
            print(f"Failed to list types: {response.status_code}")
        
        # Create new type
        print("\nCreating test document type...")
        new_type = {
            "category_id": category_id,
            "name": "Professional License",
            "slug": "professional-license",
            "description": "Professional certification or license",
            "is_active": True
        }
        response = await client.post(f"{BASE_URL}/admin/document-types", json=new_type)
        if response.status_code == 201:
            doc_type = response.json()
            print(f" Created document type: {doc_type['name']}")
            return doc_type['id']
        else:
            print(f" Failed to create type: {response.status_code}")
            return None

async def test_admin_pathway_requirements(headers, pathway_id, document_type_id):
    print("\n🔗 Testing Pathway Document Requirements...")
    async with httpx.AsyncClient(headers=headers) as client:
        # List existing requirements
        response = await client.get(f"{BASE_URL}/admin/pathways/{pathway_id}/requirements")
        if response.status_code == 200:
            requirements = response.json()
            print(f" Got {len(requirements)} existing requirements for pathway")
            for req in requirements[:5]:
                print(f"   - {req['document_name']} (Required: {req['is_required']})")
        else:
            print(f" Failed to list requirements: {response.status_code}")
        
        # Add new requirement
        print("\nAdding test requirement...")
        new_requirement = {
            "pathway_id": pathway_id,
            "document_type_id": document_type_id,
            "is_required": False,
            "instructions": "Optional professional credential",
            "display_order": 100
        }
        response = await client.post(
            f"{BASE_URL}/admin/pathways/{pathway_id}/requirements",
            json=new_requirement
        )
        if response.status_code == 201:
            req = response.json()
            print(f" Added requirement: {req['document_name']}")
        else:
            print(f" Failed to add requirement: {response.status_code} - {response.text}")

async def test_user_readiness(headers):
    print("\n👤 Testing User Document Readiness...")
    async with httpx.AsyncClient(headers=headers) as client:
        # Get public pathways
        response = await client.get(f"{BASE_URL}/pathways")
        if response.status_code != 200:
            print(" Cannot get pathways")
            return
        
        pathways = response.json()
        if not pathways:
            print(" No pathways available")
            return
        
        pathway_id = pathways[0]['id']
        pathway_slug = pathways[0]['slug']
        print(f"Using pathway: {pathways[0]['name']}")
        
        # Start roadmap if not started
        print("\nStarting roadmap...")
        response = await client.post(f"{BASE_URL}/my-roadmap/start", json={
            "pathway_id": pathway_id
        })
        if response.status_code not in [200, 201, 400]:
            print(f" Failed to start roadmap: {response.status_code}")
            return
        
        # Get document checklist
        print("\nGetting document checklist...")
        response = await client.get(f"{BASE_URL}/readiness/checklist")
        if response.status_code == 200:
            checklist = response.json()
            print(f" Got {len(checklist)} document checklist items")
            for item in checklist[:5]:
                print(f"   - {item['document_name']} ({'Required' if item['is_required'] else 'Optional'}) - Status: {item['status']}")
            
            # Update first 3 items as ready
            for i, item in enumerate(checklist[:3]):
                print(f"\nMarking '{item['document_name']}' as ready...")
                response = await client.put(
                    f"{BASE_URL}/readiness/checklist/{item['requirement_id']}",
                    json={"status": "ready", "notes": "Got it ready!"}
                )
                if response.status_code == 200:
                    updated = response.json()
                    print(f" Status: {updated['status']}")
                else:
                    print(f" Failed: {response.status_code}")
            
            # Get summary
            print("\nGetting readiness summary...")
            response = await client.get(f"{BASE_URL}/readiness/summary")
            if response.status_code == 200:
                summary = response.json()
                print(f"\n Document Readiness Summary")
                print(f"   Pathway: {summary['pathway_name']}")
                print(f"   Completion: {summary['completion_percentage']}%")
                print(f"   Required: {summary['completed_required']}/{summary['total_required']} completed")
                print(f"   Missing: {summary['missing_required']} required documents")
                if summary['missing_documents']:
                    print(f"   Missing list: {', '.join(summary['missing_documents'][:3])}")
                if summary['recommendations']:
                    print(f"\n Recommendations:")
                    for rec in summary['recommendations']:
                        print(f"   - {rec}")
            else:
                print(f" Failed to get summary: {response.status_code}")
            
            # Get missing documents
            print("\nGetting missing documents list...")
            response = await client.get(f"{BASE_URL}/readiness/missing")
            if response.status_code == 200:
                missing = response.json()
                print(f" Missing documents: {len(missing)}")
                for doc in missing[:3]:
                    print(f"   - {doc}")
        else:
            print(f" Failed to get checklist: {response.status_code} - {response.text}")

async def main():
    print("=" * 60)
    print("SPRINT 3 VERIFICATION - Smart Document Checker")
    print("=" * 60)
    
    # Admin tests
    admin_headers = await test_admin_auth()
    if not admin_headers:
        print("\n Admin auth failed. Exiting.")
        return
    
    category_id = await test_admin_document_categories(admin_headers)
    if not category_id:
        category_id = "00000000-0000-0000-0000-000000000000"  # dummy
    
    document_type_id = await test_admin_document_types(admin_headers, category_id)
    if not document_type_id:
        document_type_id = "00000000-0000-0000-0000-000000000000"  # dummy
    
    # Get first pathway ID for testing
    async with httpx.AsyncClient(headers=admin_headers) as client:
        response = await client.get(f"{BASE_URL}/admin/pathways")
        if response.status_code == 200:
            pathways = response.json()
            if pathways:
                pathway_id = pathways[0]['id']
                await test_admin_pathway_requirements(admin_headers, pathway_id, document_type_id)
    
    # User tests
    user_headers = await test_user_auth()
    if user_headers:
        await test_user_readiness(user_headers)
    
    print("\n" + "=" * 60)
    print("SPRINT 3 VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())