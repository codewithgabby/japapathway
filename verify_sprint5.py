# verify_sprint5.py
"""
Sprint 5 Verification Script
Run this after starting the server to test all Content Engine endpoints.
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


async def test_admin_categories(headers):
    print("\n📂 Testing Admin Content Categories...")
    async with httpx.AsyncClient(headers=headers) as client:
        # List categories
        response = await client.get(f"{BASE_URL}/admin/content/categories")
        if response.status_code == 200:
            categories = response.json()
            print(f" Got {len(categories)} categories")
            for cat in categories:
                print(f"   - {cat['name']} ({cat['slug']}) - {cat['articles_count']} articles - Status: {cat['status']}")
        else:
            print(f" Failed to list categories: {response.status_code}")
            return None
        
        # Create new category
        print("\nCreating test category...")
        new_category = {
            "name": "IRCC Guidance",
            "slug": "ircc-guidance",
            "description": "Official IRCC guidance and reference information"
        }
        response = await client.post(f"{BASE_URL}/admin/content/categories", json=new_category)
        if response.status_code == 201:
            category = response.json()
            print(f" Created category: {category['name']}")
            return category['id']
        else:
            print(f" Failed to create category: {response.status_code} - {response.text}")
            return None


async def test_admin_articles(headers, category_id):
    print("\n📄 Testing Admin Content Articles...")
    async with httpx.AsyncClient(headers=headers) as client:
        # List articles
        response = await client.get(f"{BASE_URL}/admin/content/articles")
        if response.status_code == 200:
            articles = response.json()
            print(f" Got {len(articles)} articles")
            for article in articles[:3]:
                print(f"   - {article['title']} ({article['status']}) - {article['pathway_name']}")
        else:
            print(f" Failed to list articles: {response.status_code}")
        
        # Get pathway ID
        response = await client.get(f"{BASE_URL}/pathways")
        if response.status_code != 200:
            print(" Cannot get pathways")
            return
        
        pathways = response.json()
        if not pathways:
            print(" No pathways available")
            return
        
        pathway_id = pathways[0]['id']
        print(f"\nUsing pathway: {pathways[0]['name']}")
        
        # Create test article
        print("\nCreating test article...")
        new_article = {
            "category_id": category_id,
            "pathway_id": pathway_id,
            "title": "Test Article for IRCC Guidance",
            "slug": "test-ircc-guidance-article",
            "summary": "A test article for verification",
            "content": "This is test content for verification purposes."
        }
        response = await client.post(f"{BASE_URL}/admin/content/articles", json=new_article)
        if response.status_code == 201:
            article = response.json()
            print(f" Created article: {article['title']}")
            article_id = article['id']
            
            # Get article versions
            print("\nGetting article versions...")
            response = await client.get(f"{BASE_URL}/admin/content/articles/{article_id}/versions")
            if response.status_code == 200:
                versions = response.json()
                print(f" Versions: {len(versions)}")
                for v in versions:
                    print(f"   - Version {v['version']}: {v['status']}")
            
            # Publish article
            print("\nPublishing article...")
            response = await client.put(
                f"{BASE_URL}/admin/content/articles/{article_id}/status",
                json={"status": "published"}
            )
            if response.status_code == 200:
                result = response.json()
                print(f" Published: {result['status']} (Version {result['version']})")
            else:
                print(f" Failed to publish: {response.status_code}")
            
            # Get published version
            print("\nGetting published version...")
            response = await client.get(
                f"{BASE_URL}/admin/content/articles/{article_id}/versions/published"
            )
            if response.status_code == 200:
                published = response.json()
                print(f" Published version: {published['version']}")
            
            return article_id
        else:
            print(f" Failed to create article: {response.status_code} - {response.text}")
            return None


async def test_public_content():
    print("\n🌐 Testing Public Content Endpoints...")
    async with httpx.AsyncClient() as client:
        # List categories (public)
        response = await client.get(f"{BASE_URL}/content/categories")
        if response.status_code == 200:
            categories = response.json()
            print(f" Got {len(categories)} published categories")
        else:
            print(f" Failed: {response.status_code}")
        
        # List articles (public)
        response = await client.get(f"{BASE_URL}/content/articles")
        if response.status_code == 200:
            articles = response.json()
            print(f"Got {len(articles)} published articles")
            for article in articles[:3]:
                print(f"   - {article['title']} - {article['pathway_name']}")
        else:
            print(f"Failed: {response.status_code}")
        
        # Get article by slug
        if articles:
            slug = articles[0]['slug']
            response = await client.get(f"{BASE_URL}/content/articles/{slug}")
            if response.status_code == 200:
                article = response.json()
                print(f"\n Got article: {article['title']}")
                print(f"   Category: {article['category_name']}")
                print(f"   Pathway: {article['pathway_name']}")
                print(f"   Status: {article['status']}")
                print(f"   Content length: {len(article['content'] or '')} chars")
            else:
                print(f"Failed to get article: {response.status_code}")


async def main():
    print("=" * 60)
    print("SPRINT 5 VERIFICATION - Content Engine")
    print("=" * 60)
    
    # Admin tests
    admin_headers = await test_admin_auth()
    if not admin_headers:
        print("\n Admin auth failed. Exiting.")
        return
    
    category_id = await test_admin_categories(admin_headers)
    if category_id:
        await test_admin_articles(admin_headers, category_id)
    
    # Public tests
    await test_public_content()
    
    print("\n" + "=" * 60)
    print("SPRINT 5 VERIFICATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())