from fastapi import Request
from fastapi.responses import JSONResponse
from app.db.connection import get_supabase_client
from app.core.security import decode_access_token
from datetime import datetime
from uuid import uuid4
from typing import Optional


supabase = get_supabase_client()


def _get_current_user(request: Request) -> Optional[dict]:
    """Helper to get current user from token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    
    if not response.data:
        return None
    
    return response.data[0]


async def generate_model(request: Request):
    """Generate 3D model"""
    try:
        current_user = _get_current_user(request)
        if not current_user:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        # Check credits
        user_credits = current_user.get("credits", 0)
        if user_credits < 1:
            return JSONResponse({"error": "Insufficient credits. Please purchase more credits."}, status_code=402)
        
        # Get form data
        form = await request.form()
        prompt = form.get("prompt")
        
        if not prompt:
            return JSONResponse({"error": "Prompt is required"}, status_code=400)
        
        # Check if images were uploaded (not supported in mock - just warn)
        image_files = form.getlist("images")
        if image_files:
            # Images uploaded but mock generation doesn't support them - just log it
            pass
        
        # Mock generation (in production, call actual AI service)
        generation = {
            "id": str(uuid4()),
            "user_id": current_user["id"],
            "prompt": prompt,
            "image_url": "https://placeholder.com/generated-model-1.jpg",
            "stl_url": None,
            "is_saved": False,
            "credits_used": 1,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Deduct credits
        supabase.table("users").update({
            "credits": user_credits - 1,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", current_user["id"]).execute()
        
        # Save generation
        response = supabase.table("generations").insert(generation).execute()
        
        return response.data[0]
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def list_generations(request: Request, saved_only: bool = False):
    """Get user's generations"""
    try:
        current_user = _get_current_user(request)
        if not current_user:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        query = supabase.table("generations").select("*").eq("user_id", current_user["id"])
        
        if saved_only:
            query = query.eq("is_saved", True)
        
        response = query.order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def get_generation(request: Request, generation_id: str):
    """Get single generation"""
    try:
        current_user = _get_current_user(request)
        if not current_user:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        response = supabase.table("generations").select("*").eq("id", generation_id).execute()
        
        if not response.data:
            return JSONResponse({"error": "Generation not found"}, status_code=404)
        
        generation = response.data[0]
        
        # Check ownership
        if generation["user_id"] != current_user["id"] and current_user.get("role") != "admin":
            return JSONResponse({"error": "Access denied"}, status_code=403)
        
        return generation
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def save_generation(request: Request, generation_id: str):
    """Save generation to gallery"""
    try:
        current_user = _get_current_user(request)
        if not current_user:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        response = supabase.table("generations").select("*").eq("id", generation_id).execute()
        
        if not response.data:
            return JSONResponse({"error": "Generation not found"}, status_code=404)
        
        generation = response.data[0]
        
        if generation["user_id"] != current_user["id"]:
            return JSONResponse({"error": "Access denied"}, status_code=403)
        
        update_response = supabase.table("generations").update({"is_saved": True}).eq("id", generation_id).execute()
        
        return update_response.data[0]
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def delete_generation(request: Request, generation_id: str):
    """Delete generation"""
    try:
        current_user = _get_current_user(request)
        if not current_user:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        response = supabase.table("generations").select("*").eq("id", generation_id).execute()
        
        if not response.data:
            return JSONResponse({"error": "Generation not found"}, status_code=404)
        
        generation = response.data[0]
        
        if generation["user_id"] != current_user["id"] and current_user.get("role") != "admin":
            return JSONResponse({"error": "Access denied"}, status_code=403)
        
        delete_response = supabase.table("generations").delete().eq("id", generation_id).execute()
        
        return {"message": "Generation deleted successfully"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def get_gallery(request: Request):
    """Get user's gallery (saved generations)"""
    try:
        current_user = _get_current_user(request)
        if not current_user:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        response = supabase.table("generations").select("*").eq("user_id", current_user["id"]).eq("is_saved", True).order("created_at", desc=True).execute()
        
        return response.data
    except Exception as e:
        import logging
        logging.error(f"Gallery error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)