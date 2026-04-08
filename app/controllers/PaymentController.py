from fastapi import Request
from fastapi.responses import JSONResponse
from app.db.connection import get_supabase_client
from app.core.security import decode_access_token
from app.core.config import get_settings
from datetime import datetime
from uuid import uuid4
from typing import Optional
import json


supabase = get_supabase_client()
settings = get_settings()


def _get_current_user(request: Request) -> Optional[dict]:
    
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


async def subscribe_to_plan(request: Request):
    
    try:
        current_user = _get_current_user(request)
        if not current_user:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        body = await request.json()
        plan_id = body.get("plan_id")
        
        if not plan_id:
            return JSONResponse({"error": "Plan ID is required"}, status_code=400)

        plan_response = supabase.table("plans").select("*").eq("id", plan_id).execute()
        if not plan_response.data:
            return JSONResponse({"error": "Plan not found"}, status_code=404)
        
        plan = plan_response.data[0]

        if not settings.stripe_secret_key:

            payment = {
                "id": str(uuid4()),
                "user_id": current_user["id"],
                "type": "subscription",
                "amount": plan["price"],
                "status": "completed",
                "metadata": json.dumps({"plan_id": plan_id, "plan_name": plan["name"]}),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            supabase.table("users").update({
                "subscription_plan": plan["name"].lower().replace(" ", "_"),
                "credits": current_user.get("credits", 0) + plan["credits"],
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", current_user["id"]).execute()
            
            response = supabase.table("payments").insert(payment).execute()
            return response.data[0]
        
        return JSONResponse({"error": "Stripe integration coming soon"}, status_code=501)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def buy_credits(request: Request):
    
    try:
        current_user = _get_current_user(request)
        if not current_user:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        body = await request.json()
        credit_pack_id = body.get("credit_pack_id")
        
        if not credit_pack_id:
            return JSONResponse({"error": "Credit pack ID is required"}, status_code=400)

        pack_response = supabase.table("credit_packs").select("*").eq("id", credit_pack_id).execute()
        if not pack_response.data:
            return JSONResponse({"error": "Credit pack not found"}, status_code=404)
        
        pack = pack_response.data[0]

        if not settings.stripe_secret_key:

            payment = {
                "id": str(uuid4()),
                "user_id": current_user["id"],
                "type": "credit_pack",
                "amount": pack["price"],
                "status": "completed",
                "metadata": json.dumps({"pack_id": credit_pack_id, "credits": pack["credits"]}),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            supabase.table("users").update({
                "credits": current_user.get("credits", 0) + pack["credits"],
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", current_user["id"]).execute()
            
            response = supabase.table("payments").insert(payment).execute()
            return response.data[0]
        
        return JSONResponse({"error": "Stripe integration coming soon"}, status_code=501)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def list_payments(request: Request):
    
    try:
        current_user = _get_current_user(request)
        if not current_user:
            return JSONResponse({"error": "Authentication required"}, status_code=401)

        if current_user.get("role") == "admin":
            response = supabase.table("payments").select("*").order("created_at", desc=True).execute()
        else:
            response = supabase.table("payments").select("*").eq("user_id", current_user["id"]).order("created_at", desc=True).execute()
        
        return response.data
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def stripe_webhook(request: Request):
    
    try:
        if not settings.stripe_secret_key:
            return JSONResponse({"error": "Stripe not configured"}, status_code=503)

        return {"message": "Webhook received"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
