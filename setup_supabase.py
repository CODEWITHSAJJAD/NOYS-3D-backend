"""
Supabase Database Setup Script
Run this script to initialize all required tables in Supabase
"""
import sys
sys.path.insert(0, "D:\\ClientProject\\backend")

from app.db.connection import get_supabase_client
from app.core.config import get_settings
import json

settings = get_settings()
supabase = get_supabase_client()

def create_table(table_name: str, schema: dict):
    """Create a table in Supabase using SQL"""
    try:
        # Supabase uses PostgreSQL, we'll execute SQL to create tables
        print(f"Checking if table '{table_name}' exists...")
        # Note: In production Supabase, you'd use the SQL editor or migrations
        # For now, we'll just print the schema
        print(f"  Schema for {table_name}: {json.dumps(schema, indent=2)}")
        return True
    except Exception as e:
        print(f"Error creating table {table_name}: {e}")
        return False


def init_tables():
    """Initialize all tables"""
    
    tables = {
        "users": """
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                credits INTEGER DEFAULT 0,
                subscription_plan VARCHAR(50) DEFAULT 'starter',
                avatar_url VARCHAR(500),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """,
        "categories": """
            CREATE TABLE IF NOT EXISTS categories (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """,
        "products": """
            CREATE TABLE IF NOT EXISTS products (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                image_url VARCHAR(500),
                category_id UUID REFERENCES categories(id),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """,
        "plans": """
            CREATE TABLE IF NOT EXISTS plans (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                credits INTEGER NOT NULL,
                features JSONB DEFAULT '[]',
                is_popular BOOLEAN DEFAULT false,
                stripe_price_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """,
        "credit_packs": """
            CREATE TABLE IF NOT EXISTS credit_packs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                credits INTEGER NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                stripe_price_id VARCHAR(255),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """,
        "orders": """
            CREATE TABLE IF NOT EXISTS orders (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) NOT NULL,
                items JSONB NOT NULL,
                total DECIMAL(10,2) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                shipping_address JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """,
        "generations": """
            CREATE TABLE IF NOT EXISTS generations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) NOT NULL,
                prompt TEXT NOT NULL,
                image_url VARCHAR(500),
                stl_url VARCHAR(500),
                is_saved BOOLEAN DEFAULT false,
                credits_used INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """,
        "payments": """
            CREATE TABLE IF NOT EXISTS payments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) NOT NULL,
                type VARCHAR(50) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                stripe_payment_intent_id VARCHAR(255),
                stripe_subscription_id VARCHAR(255),
                status VARCHAR(50) DEFAULT 'pending',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """
    }
    
    print("=" * 60)
    print("Supabase Database Setup")
    print("=" * 60)
    print(f"\nSupabase URL: {settings.supabase_url}")
    print("\nTables to create:")
    print("-" * 40)
    
    for table_name in tables.keys():
        print(f"  - {table_name}")
    
    print("\n" + "=" * 60)
    print("INSTRUCTIONS:")
    print("=" * 60)
    print("""
Since we're using Supabase's Python client directly (not SQLAlchemy 
with migrations), you need to create these tables manually in the 
Supabase SQL Editor.

Please run the following SQL in your Supabase SQL Editor:

""")
    
    for table_name, sql in tables.items():
        print(f"\n-- {table_name.upper()} --")
        print(sql)
    
    print("\n" + "=" * 60)
    print("After creating tables, you can seed initial data:")
    print("=" * 60)
    
    seed_sql = """
-- Seed Categories
INSERT INTO categories (id, name, slug, description) VALUES
('11111111-1111-1111-1111-111111111111', 'Sci-Fi Models', 'sci-fi-models', 'Futuristic 3D printed models'),
('22222222-2222-2222-2222-222222222222', 'Fantasy Miniatures', 'fantasy-miniatures', 'Fantasy-themed miniatures and figures'),
('33333333-3333-3333-3333-333333333333', 'Terrain & Scenery', 'terrain-scenery', 'Tabletop terrain and scenery'),
('44444444-4444-4444-4444-444444444444', 'Diorama Accessories', 'diorama-accessories', 'Accessories for dioramas');

-- Seed Plans
INSERT INTO plans (id, name, price, credits, features, is_popular) VALUES
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Starter', 0, 15, '["Free account access", "Save favorites", "Basic support"]', false),
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Bronze', 5.00, 40, '["7% off all orders", "Priority access", "25 AI credits/month"]', false),
('cccccccc-cccc-cccc-cccc-cccccccccccc', 'Silver', 9.99, 100, '["10% off", "Free delivery", "Priority support", "50 AI credits/month"]', true),
('dddddddd-dddd-dddd-dddd-dddddddddddd', 'Gold', 14.99, 250, '["15% off", "Free delivery", "Priority queue", "150 AI credits/month", "Exclusive items"]', false);

-- Seed Credit Packs
INSERT INTO credit_packs (id, credits, price, is_active) VALUES
('11111111-1111-1111-1111-111111111110', 10, 2.99, true),
('22222222-2222-2222-2222-222222222220', 25, 5.99, true),
('33333333-3333-3333-3333-333333333330', 50, 9.99, true),
('44444444-4444-4444-4444-444444444440', 100, 17.99, true);

-- Seed Sample Products
INSERT INTO products (id, name, description, price, category_id, is_active) VALUES
('aaaa1111-aaaa-1111-aaaa-111111111111', 'Cyberpunk City Diorama', 'A detailed cyberpunk cityscape diorama', 120.00, '11111111-1111-1111-1111-111111111111', true),
('bbbb2222-bbbb-2222-bbbb-222222222222', 'Fantasy Castle Miniature', 'Detailed fantasy castle for tabletop gaming', 85.00, '22222222-2222-2222-2222-222222222222', true),
('cccc3333-cccc-3333-cccc-333333333333', 'Sci-Fi Tank Model', 'Futuristic tank model for collectors', 45.00, '11111111-1111-1111-1111-111111111111', true),
('dddd4444-dddd-4444-dddd-444444444444', 'Ruined Castle Walls', 'Weathered castle wall terrain piece', 45.00, '33333333-3333-3333-3333-333333333333', true),
('eeee5555-eeee-5555-eeee-555555555555', 'Dwarven Stronghold', 'Intricate dwarven fortress model', 120.00, '33333333-3333-3333-3333-333333333333', true);
"""
    print(seed_sql)


if __name__ == "__main__":
    init_tables()