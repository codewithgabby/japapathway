# verify_sprint4.py
"""
Sprint 4 Verification Script
Run this after starting the server to test all SOP Builder endpoints.
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def test_admin_auth():
    print("\n Testing Admin Authentication...")
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/auth/login", json={
            "email": "admin@appname.com",
            "password": "changeme123"
        })
        if response.status_code == 200:
            tokens = response.json()
            print(" Admin login successful")
            return {"Authorization": f"Bearer {tokens['access_token']}"}
        else:
            print(f" Admin login failed: {response.status_code}")
            return None

async def test_user_auth():
    print("\n Testing User Authentication...")
    async with httpx.AsyncClient() as client:
        # Try login with saved credentials
        response = await client.post(f"{BASE_URL}/auth/login", json={
            "email": "applicant.test@appname.com",
            "password": "TestApplicant123!"
        })
        if response.status_code == 200:
            tokens = response.json()
            print(" Test user logged in")
            return {"Authorization": f"Bearer {tokens['access_token']}"}
        else:
            # Try register
            response = await client.post(f"{BASE_URL}/auth/register", json={
                "email": "applicant.test@appname.com",
                "password": "TestApplicant123!",
                "full_name": "Test Applicant"
            })
            if response.status_code == 200:
                tokens = response.json()
                print(" Test user registered")
                return {"Authorization": f"Bearer {tokens['access_token']}"}
            else:
                print(f" User auth failed: {response.status_code}")
                return None

async def test_admin_templates(headers):
    print("\n Testing Admin Template Endpoints...")
    async with httpx.AsyncClient(headers=headers) as client:
        # List templates
        response = await client.get(f"{BASE_URL}/admin/sop/templates")
        if response.status_code == 200:
            templates = response.json()
            print(f" Got {len(templates)} templates")
            for t in templates:
                print(f"   - {t['name']} ({t['document_type']}) - {t['sections_count']} sections - Status: {t['status']}")
        else:
            print(f" Failed to list templates: {response.status_code}")
            return None
        
        # Get template detail
        if templates:
            template_id = templates[0]['id']
            response = await client.get(f"{BASE_URL}/admin/sop/templates/{template_id}")
            if response.status_code == 200:
                detail = response.json()
                print(f"\n Template detail: {detail['name']}")
                print(f"   Document type: {detail['document_type']}")
                print(f"   Sections: {len(detail['sections'])}")
                for section in detail['sections']:
                    print(
                        f"   Section {section['order_index']}: "
                        f"{section['name']} ({section['questions_count']} questions)"
                    )
        
        return templates

async def test_user_templates(headers):
    print("\n👤 Testing Applicant Template Endpoints...")
    async with httpx.AsyncClient(headers=headers) as client:
        # List available templates
        response = await client.get(f"{BASE_URL}/sop/templates")
        if response.status_code == 200:
            templates = response.json()
            print(f" Got {len(templates)} available templates")
            for t in templates:
                print(f"   - {t['name']} ({t['document_type']})")
            return templates
        else:
            print(f" Failed to list templates: {response.status_code}")
            return None

async def test_user_document_flow(headers, templates):
    print("\n Testing Applicant Document Flow...")
    
    if not templates:
        print(" No templates available")
        return
    
    # Find SOP template
    sop_template = None
    loe_template = None
    for t in templates:
        if t['document_type'] == 'sop':
            sop_template = t
        if t['document_type'] == 'loe':
            loe_template = t
    
    if not sop_template:
        print(" No SOP template found")
        return
    
    async with httpx.AsyncClient(headers=headers) as client:
        # Get pathway ID from template
        pathway_id = sop_template['pathway_id']
        
        # Create SOP document
        print("\nCreating SOP document...")
        response = await client.post(f"{BASE_URL}/sop/my-documents", json={
            "pathway_id": pathway_id,
            "template_id": sop_template['id'],
            "document_type": "sop"
        })
        if response.status_code == 201:
            document = response.json()
            document_id = document['id']
            print(f" Created SOP document: {document_id}")
            print(f"   Status: {document['status']}")
            
            # Get document detail with responses
            print("\nGetting document detail...")
            response = await client.get(f"{BASE_URL}/sop/my-documents/{document_id}")
            if response.status_code == 200:
                detail = response.json()
                print(f" Document: {detail['document_type']}")
                print(f"   Responses: {len(detail['responses'])}")
                
                # Answer first few questions using responses from document detail
                if detail['responses']:
                    print("\nAnswering questions...")
                    answers = []
                    for response_item in detail['responses'][:4]:
                        answers.append({
                            "question_id": response_item['question_id'],
                            "answer_text": f"This is my answer for: {response_item['question_text'][:50]}..."
                        })
                    
                    if answers:
                        response = await client.post(
                            f"{BASE_URL}/sop/my-documents/{document_id}/responses",
                            json={"answers": answers}
                        )
                        if response.status_code == 201:
                            saved = response.json()
                            print(f" Saved {len(saved)} responses")
                            
                            # Get progress
                            response = await client.get(f"{BASE_URL}/sop/my-documents/{document_id}/progress")
                            if response.status_code == 200:
                                progress = response.json()
                                print(f"\n Progress: {progress['progress_percentage']}%")
                                print(f"   Answered: {progress['answered_questions']}/{progress['total_questions']}")
                                print(f"   Sections completed: {progress['completed_sections']}/{progress['total_sections']}")
                    else:
                        print(" No questions found to answer")
                else:
                    print(" No responses found in document detail")
            else:
                print(f" Failed to get document detail: {response.status_code}")
            
            # Create LOE document (multiple LOEs supported)
            if loe_template:
                print("\nCreating LOE document...")
                response = await client.post(f"{BASE_URL}/sop/my-documents", json={
                    "pathway_id": pathway_id,
                    "template_id": loe_template['id'],
                    "document_type": "loe",
                    "title": "LOE - Study Gap",
                    "reason": "Explaining my study gap"
                })
                if response.status_code == 201:
                    loe_document = response.json()
                    loe_id = loe_document['id']
                    print(f" Created LOE: {loe_document['title']}")
                    
                    # Link LOE to SOP
                    print("\nLinking LOE to SOP...")
                    response = await client.post(
                        f"{BASE_URL}/sop/my-documents/{document_id}/relationships",
                        json={
                            "related_document_id": loe_id,
                            "relationship_type": "supports"
                        }
                    )
                    if response.status_code == 201:
                        print(" Linked LOE to SOP")
                    else:
                        print(f" Failed to link: {response.status_code}")
                    
                    # Get relationships
                    response = await client.get(f"{BASE_URL}/sop/my-documents/{document_id}/relationships")
                    if response.status_code == 200:
                        relationships = response.json()
                        print(f" Relationships: {len(relationships)}")
                        for rel in relationships:
                            print(f"   - {rel['relationship_type']}: {rel['related_document_id']}")
                else:
                    print(f" Failed to create LOE: {response.status_code} - {response.text}")
            
            # Get all user documents
            print("\nGetting all user documents...")
            response = await client.get(f"{BASE_URL}/sop/my-documents")
            if response.status_code == 200:
                documents = response.json()
                print(f" Total documents: {len(documents)}")
                for doc in documents:
                    print(f"   - {doc['document_type'].upper()}: {doc['title'] or 'Untitled'} - Status: {doc['status']}")
        else:
            print(f" Failed to create document: {response.status_code} - {response.text}")

async def main():
    print("=" * 60)
    print("SPRINT 4 VERIFICATION - SOP Builder")
    print("=" * 60)
    
    # Admin tests
    admin_headers = await test_admin_auth()
    if not admin_headers:
        print("\n Admin auth failed. Exiting.")
        return
    
    await test_admin_templates(admin_headers)
    
    # User tests
    user_headers = await test_user_auth()
    if not user_headers:
        print("\n User auth failed. Exiting.")
        return
    
    templates = await test_user_templates(user_headers)
    await test_user_document_flow(user_headers, templates)
    
    print("\n" + "=" * 60)
    print("SPRINT 4 VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())