"""Test API endpoints with real Neon database."""
import httpx
import json

BASE = "http://127.0.0.1:8000/api/v1"

def test_api():
    client = httpx.Client(timeout=60)

    # 1. Register restaurant
    print("=" * 50)
    print("1. Registering restaurant...")
    r = client.post(f"{BASE}/auth/register", json={
        "restaurant_name": "Milliy Taomlar",
        "admin_phone": "+998901234567",
        "admin_password": "boss12345",
        "admin_full_name": "Alisher Karimov"
    })
    print(f"   Status: {r.status_code}")
    data = r.json()
    print(f"   Response: {json.dumps(data, indent=2, default=str)}")
    
    if r.status_code in (200, 201):
        token = data.get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get profile
        print("\n2. Getting profile...")
        r2 = client.get(f"{BASE}/auth/me", headers=headers)
        print(f"   Status: {r2.status_code}")
        profile = r2.json()
        print(f"   User: {profile.get('full_name')} | Role: {profile.get('role')}")
        
        # 3. Create category
        print("\n3. Creating menu category...")
        r3 = client.post(f"{BASE}/menu/categories?name=Palovlar&description=Eng mazali palovlar", headers=headers)
        print(f"   Status: {r3.status_code}")
        print(f"   Response: {r3.json()}")

        # 4. Create menu item
        print("\n4. Creating menu item...")
        cat_data = r3.json()
        cat_id = cat_data.get("id")
        if cat_id:
            r4 = client.post(
                f"{BASE}/menu/items?category_id={cat_id}&name=Toshkent palovi&price=45000&description=An'anaviy toshkent palovi&preparation_time=30",
                headers=headers
            )
            print(f"   Status: {r4.status_code}")
            print(f"   Response: {r4.json()}")
        
        # 5. Get statistics (boss)
        print("\n5. Boss dashboard stats...")
        r5 = client.get(f"{BASE}/boss/statistics", headers=headers)
        print(f"   Status: {r5.status_code}")
        print(f"   Stats: {json.dumps(r5.json(), indent=2, default=str)}")

        # 6. Get menu
        print("\n6. Viewing menu...")
        r6 = client.get(f"{BASE}/customer/menu", headers=headers)
        print(f"   Status: {r6.status_code}")
        menu = r6.json()
        print(f"   Categories: {len(menu)}")
        for cat in menu:
            print(f"   - {cat['name']}: {len(cat['items'])} items")
    else:
        print(f"   Registration failed!")

    print("\n" + "=" * 50)
    print("API test complete!")

test_api()
