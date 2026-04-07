from fastapi import Request
from fastapi.responses import JSONResponse
from app.db.connection import get_supabase_client
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from datetime import datetime
from uuid import uuid4


supabase = get_supabase_client()


def register():
    """Register new user"""
    try:
        request = Request
        # This will be called via dependency injection in routes
        return {"message": "Register endpoint"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


def login():
    """Login user"""
    try:
        return {"message": "Login endpoint"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def signup(request: Request):
    """Create new user account"""
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        name = body.get("name")
        
        if not email or not password or not name:
            return JSONResponse({"error": "Email, password, and name are required"}, status_code=400)
        
        # Check if user exists
        existing = supabase.table("users").select("id").eq("email", email).execute()
        if existing.data:
            return JSONResponse({"error": "Email already registered"}, status_code=400)
        
        # Create user
        user_id = str(uuid4())
        password_hash = get_password_hash(password)
        
        user = {
            "id": user_id,
            "email": email,
            "password_hash": password_hash,
            "name": name,
            "role": "user",
            "credits": 15,
            "subscription_plan": "starter",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("users").insert(user).execute()
        
        # Create token
        access_token = create_access_token(data={"sub": user_id})
        
        return {"access_token": access_token, "token_type": "bearer", "user": {"id": user_id, "email": email, "name": name, "role": "user"}}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def login(request: Request):
    """Login user and return JWT token"""
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        
        if not email or not password:
            return JSONResponse({"error": "Email and password are required"}, status_code=400)
        
        # Find user
        response = supabase.table("users").select("*").eq("email", email).execute()
        if not response.data:
            return JSONResponse({"error": "Invalid email or password"}, status_code=401)
        
        user = response.data[0]
        
        # Verify password
        if not verify_password(password, user["password_hash"]):
            return JSONResponse({"error": "Invalid email or password"}, status_code=401)
        
        # Create token
        access_token = create_access_token(data={"sub": user["id"]})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
                "credits": user.get("credits", 0),
                "subscription_plan": user.get("subscription_plan", "starter"),
                "shipping_address": user.get("shipping_address", "")
            }
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def get_me(request: Request):
    """Get current user info"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse({"error": "Missing or invalid authorization header"}, status_code=401)
        
        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)
        
        if not payload:
            return JSONResponse({"error": "Invalid or expired token"}, status_code=401)
        
        user_id = payload.get("sub")
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if not response.data:
            return JSONResponse({"error": "User not found"}, status_code=404)
        
        user = response.data[0]
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "credits": user.get("credits", 0),
            "subscription_plan": user.get("subscription_plan", "starter"),
            "shipping_address": user.get("shipping_address", ""),
            "created_at": user["created_at"]
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def update_me(request: Request):
    """Update current user info"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse({"error": "Missing or invalid authorization header"}, status_code=401)
        
        token = auth_header.split(" ")[1]
        payload = decode_access_token(token)
        
        if not payload:
            return JSONResponse({"error": "Invalid or expired token"}, status_code=401)
        
        user_id = payload.get("sub")
        body = await request.json()
        
        update_data = {k: v for k, v in body.items() if v is not None}
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table("users").update(update_data).eq("id", user_id).execute()
        
        if not response.data:
            return JSONResponse({"error": "Failed to update user"}, status_code=400)
        
        return response.data[0]
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


def logout():
    """Logout user"""
    return {"message": "Successfully logged out"}