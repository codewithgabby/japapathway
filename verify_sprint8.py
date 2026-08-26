# verify_sprint8.py
"""
Sprint 8 Verification Script
Run this after starting the server to test the dashboard endpoint.
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def test_user_auth():
    print("\n Testing User Authentication...")
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/auth/login", json={
            "email": "applicant.test@appname.com",
            "password": "TestApplicant123!"
        })
        if response.status_code == 200:
            tokens = response.json()
            print(" Test user logged in")
            return {"Authorization": f"Bearer {tokens['access_token']}"}
        else:
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
                print(f"❌ User auth failed: {response.status_code}")
                return None


async def test_unauthenticated():
    print("\n Testing Unauthenticated Access...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/dashboard")
        if response.status_code == 401 or response.status_code == 403:
            print(f" Unauthenticated request rejected: {response.status_code}")
        else:
            print(f"❌ Expected rejection but got: {response.status_code}")


async def test_dashboard(headers):
    print("\n Testing Dashboard Endpoint...")
    async with httpx.AsyncClient(headers=headers) as client:
        response = await client.get(f"{BASE_URL}/dashboard")
        
        if response.status_code != 200:
            print(f"❌ Dashboard failed: {response.status_code} - {response.text}")
            return
        
        data = response.json()
        
        # User section
        print("\n👤 User Section:")
        user = data.get("user", {})
        print(f"   Name: {user.get('full_name')}")
        print(f"   Email: {user.get('email')}")
        
        # Journey section
        print("\n Journey Section:")
        journey = data.get("journey", {})
        print(f"   Has roadmap: {journey.get('has_roadmap')}")
        print(f"   Pathway: {journey.get('pathway_name') or 'None'}")
        print(f"   Progress: {journey.get('completion_percentage', 0)}%")
        print(f"   Steps: {journey.get('completed_steps', 0)}/{journey.get('total_steps', 0)}")
        if journey.get("next_step"):
            print(f"   Next step: {journey['next_step'].get('title')}")
        
        # Readiness section
        print("\n📋 Readiness Section:")
        readiness = data.get("readiness", {})
        print(f"   Has checklist: {readiness.get('has_checklist')}")
        print(f"   Completion: {readiness.get('completion_percentage', 0)}%")
        print(f"   Required: {readiness.get('completed_required', 0)}/{readiness.get('total_required', 0)}")
        if readiness.get("missing_documents"):
            print(f"   Missing: {len(readiness['missing_documents'])} documents")
        
        # SOP Documents section
        print("\n📝 SOP Documents Section:")
        sop_docs = data.get("sop_documents", [])
        print(f"   Total documents: {len(sop_docs)}")
        for doc in sop_docs:
            print(f"   - {doc.get('document_type', 'unknown').upper()}: {doc.get('status')} ({doc.get('progress_percentage', 0)}% answered)")
            if doc.get("latest_draft"):
                draft = doc["latest_draft"]
                print(f"     Draft v{draft.get('version')}: {draft.get('generation_status')}")
                if draft.get("warnings_count", 0) > 0:
                    print(f"     Warnings: {draft['warnings_count']}")
                if draft.get("missing_information_count", 0) > 0:
                    print(f"     Missing info: {draft['missing_information_count']}")
        
        # Next Action
        print("\n Next Action:")
        next_action = data.get("next_action", {})
        print(f"   Type: {next_action.get('type')}")
        print(f"   Title: {next_action.get('title')}")
        print(f"   Description: {next_action.get('description')}")
        print(f"   Priority: {next_action.get('priority')}")


async def test_user_isolation():
    print("\n Testing User Isolation...")
    
    # Create a second user
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/auth/register", json={
            "email": "isolation.test@appname.com",
            "password": "IsolationTest123!",
            "full_name": "Isolation Test User"
        })
        if response.status_code == 200:
            tokens2 = response.json()
            headers2 = {"Authorization": f"Bearer {tokens2['access_token']}"}
            
            # User 2 gets their own dashboard
            response = await client.get(f"{BASE_URL}/dashboard", headers=headers2)
            if response.status_code == 200:
                data2 = response.json()
                user2_email = data2["user"]["email"]
                print(f" User 2 sees their own email: {user2_email}")
                
                # Verify user 2 doesn't see user 1's data
                if user2_email == "isolation.test@appname.com":
                    print(" User isolation confirmed — no data leak")
                else:
                    print("❌ User isolation failed")
        else:
            print(f"❌ Failed to create second user: {response.status_code}")


async def test_empty_state():
    print("\n🆕 Testing Empty State (New User)...")
    async with httpx.AsyncClient() as client:
        # Register fresh user with no data
        response = await client.post(f"{BASE_URL}/auth/register", json={
            "email": f"empty.{asyncio.get_event_loop().time()}@appname.com",
            "password": "EmptyTest123!",
            "full_name": "Empty State User"
        })
        if response.status_code == 200:
            tokens = response.json()
            headers = {"Authorization": f"Bearer {tokens['access_token']}"}
            
            response = await client.get(f"{BASE_URL}/dashboard", headers=headers)
            if response.status_code == 200:
                data = response.json()
                journey = data.get("journey", {})
                readiness = data.get("readiness", {})
                sop_docs = data.get("sop_documents", [])
                next_action = data.get("next_action", {})
                
                print(f"   Has roadmap: {journey.get('has_roadmap')}")
                print(f"   Has checklist: {readiness.get('has_checklist')}")
                print(f"   SOP documents: {len(sop_docs)}")
                print(f"   Next action: {next_action.get('type')}")
                
                if not journey.get("has_roadmap") and not readiness.get("has_checklist") and len(sop_docs) == 0:
                    print(" Empty state handled gracefully")
                else:
                    print("❌ Empty state not handled correctly")
            else:
                print(f"❌ Dashboard failed for empty user: {response.status_code}")
        else:
            print(f"❌ Failed to register empty user: {response.status_code}")


async def main():
    print("=" * 60)
    print("SPRINT 8 VERIFICATION - Dashboard")
    print("=" * 60)
    
    # Unauthenticated test
    await test_unauthenticated()
    
    # User auth
    user_headers = await test_user_auth()
    if not user_headers:
        print("\n❌ User auth failed. Exiting.")
        return
    
    # Dashboard test
    await test_dashboard(user_headers)
    
    # User isolation
    await test_user_isolation()
    
    # Empty state
    await test_empty_state()
    
    print("\n" + "=" * 60)
    print("SPRINT 8 VERIFICATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())