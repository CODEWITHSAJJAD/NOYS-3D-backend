from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import UploadFile, File, Form
from app.core.config import get_settings
from app.controllers import AuthController, ProductController, PlanController, OrderController, PaymentController, GenerationController, AdminController, UserController
from app.middleware.rate_limiter import RateLimiter, CacheMiddleware
from app.middleware.logging import RequestLoggingMiddleware, TimeoutMiddleware
import os
import uuid
from pathlib import Path

settings = get_settings()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Noys 3D Prints API",
    description="Backend API for Noys 3D Prints - 3D Printing E-commerce Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.add_middleware(TimeoutMiddleware, timeout=30.0)  # Timeout first
app.add_middleware(RateLimiter, calls=100, period=60)  # Rate limiting
app.add_middleware(CacheMiddleware)  # Simple caching
app.add_middleware(RequestLoggingMiddleware)  # Request logging

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Noys 3D Prints API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    
    import time
    import psutil

    db_status = "healthy"
    db_latency = 0
    try:
        from app.db.connection import get_supabase_client
        supabase = get_supabase_client()
        start = time.time()
        supabase.table("users").select("id").limit(1).execute()
        db_latency = (time.time() - start) * 1000
    except Exception as e:
        db_status = "unhealthy"
        db_latency = 0
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "database": {
                "status": db_status,
                "latency_ms": round(db_latency, 2)
            },
            "api": {
                "status": "healthy"
            }
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent
        }
    }


@app.post("/api/v1/auth/register")
async def register(request: Request):
    return await AuthController.signup(request)


@app.post("/api/v1/auth/login")
async def login(request: Request):
    return await AuthController.login(request)


@app.get("/api/v1/auth/me")
async def get_me(request: Request):
    return await AuthController.get_me(request)


@app.put("/api/v1/auth/me")
async def update_me(request: Request):
    return await AuthController.update_me(request)


@app.post("/api/v1/auth/logout")
async def logout():
    return AuthController.logout()


@app.get("/api/v1/user/profile")
async def get_user_profile(request: Request):
    return await UserController.get_user_profile(request)


@app.put("/api/v1/user/profile")
async def update_user_profile(request: Request):
    return await UserController.update_user_profile(request)


@app.put("/api/v1/user/password")
async def change_password(request: Request):
    return await UserController.change_password(request)


@app.post("/api/v1/contact")
async def submit_contact(request: Request):
    return await UserController.submit_contact(request)


@app.get("/api/v1/categories")
async def list_categories():
    return await ProductController.list_categories()


@app.get("/api/v1/categories/{category_id}")
async def get_category(category_id: str):
    return await ProductController.get_category(category_id)


@app.post("/api/v1/categories")
async def create_category(request: Request):
    return await ProductController.create_category(request)


@app.put("/api/v1/categories/{category_id}")
async def update_category(request: Request, category_id: str):
    return await ProductController.update_category(request, category_id)


@app.delete("/api/v1/categories/{category_id}")
async def delete_category(request: Request, category_id: str):
    return await ProductController.delete_category(request, category_id)


@app.get("/api/v1/products")
async def list_products(request: Request, category: str = None, active_only: bool = True):
    return await ProductController.list_products(category=category, active_only=active_only)


@app.get("/api/v1/products/{product_id}")
async def get_product(product_id: str):
    return await ProductController.get_product(product_id)


@app.post("/api/v1/products")
async def create_product(request: Request):
    return await ProductController.create_product(request)


@app.put("/api/v1/products/{product_id}")
async def update_product(request: Request, product_id: str):
    return await ProductController.update_product(request, product_id)


@app.delete("/api/v1/products/{product_id}")
async def delete_product(request: Request, product_id: str):
    return await ProductController.delete_product(request, product_id)


@app.get("/api/v1/plans")
async def list_plans():
    return await PlanController.list_plans()


@app.get("/api/v1/plans/{plan_id}")
async def get_plan(plan_id: str):
    return await PlanController.get_plan(plan_id)


@app.post("/api/v1/plans")
async def create_plan(request: Request):
    return await PlanController.create_plan(request)


@app.put("/api/v1/plans/{plan_id}")
async def update_plan(request: Request, plan_id: str):
    return await PlanController.update_plan(request, plan_id)


@app.delete("/api/v1/plans/{plan_id}")
async def delete_plan(request: Request, plan_id: str):
    return await PlanController.delete_plan(request, plan_id)


@app.get("/api/v1/credit-packs")
async def list_credit_packs(active_only: bool = True):
    return await PlanController.list_credit_packs(active_only=active_only)


@app.get("/api/v1/credit-packs/{pack_id}")
async def get_credit_pack(pack_id: str):
    return await PlanController.get_credit_pack(pack_id)


@app.post("/api/v1/credit-packs")
async def create_credit_pack(request: Request):
    return await PlanController.create_credit_pack(request)


@app.put("/api/v1/credit-packs/{pack_id}")
async def update_credit_pack(request: Request, pack_id: str):
    return await PlanController.update_credit_pack(request, pack_id)


@app.delete("/api/v1/credit-packs/{pack_id}")
async def delete_credit_pack(request: Request, pack_id: str):
    return await PlanController.delete_credit_pack(request, pack_id)


@app.post("/api/v1/orders")
async def create_order(request: Request):
    return await OrderController.create_order(request)


@app.get("/api/v1/orders")
async def list_orders(request: Request):
    return await OrderController.list_orders(request)


@app.get("/api/v1/orders/{order_id}")
async def get_order(request: Request, order_id: str):
    return await OrderController.get_order(request, order_id)


@app.put("/api/v1/orders/{order_id}/status")
async def update_order_status(request: Request, order_id: str):
    return await OrderController.update_order_status(request, order_id)


@app.post("/api/v1/payments/subscribe")
async def subscribe_to_plan(request: Request):
    return await PaymentController.subscribe_to_plan(request)


@app.post("/api/v1/payments/buy-credits")
async def buy_credits(request: Request):
    return await PaymentController.buy_credits(request)


@app.post("/api/v1/payments/checkout")
async def create_checkout_session(request: Request):
    return await PaymentController.create_checkout_session(request)


@app.get("/api/v1/payments/config")
async def get_stripe_config(request: Request):
    return await PaymentController.get_stripe_config(request)


@app.get("/api/v1/payments")
async def list_payments(request: Request):
    return await PaymentController.list_payments(request)


@app.post("/api/v1/payments/webhook")
async def stripe_webhook(request: Request):
    return await PaymentController.stripe_webhook(request)


@app.post("/api/v1/generations/generate")
async def generate_model(request: Request):
    return await GenerationController.generate_model(request)


@app.get("/api/v1/generations")
async def list_generations(request: Request, saved_only: bool = False):
    return await GenerationController.list_generations(request, saved_only=saved_only)


@app.get("/api/v1/generations/gallery")
async def get_gallery(request: Request):
    return await GenerationController.get_gallery(request)


@app.get("/api/v1/generations/{generation_id}")
async def get_generation(request: Request, generation_id: str):
    return await GenerationController.get_generation(request, generation_id)


@app.post("/api/v1/generations/{generation_id}/save")
async def save_generation(request: Request, generation_id: str):
    return await GenerationController.save_generation(request, generation_id)


@app.delete("/api/v1/generations/{generation_id}")
async def delete_generation(request: Request, generation_id: str):
    return await GenerationController.delete_generation(request, generation_id)


@app.get("/api/v1/admin/stats")
async def get_stats(request: Request):
    return await AdminController.get_stats(request)


@app.get("/api/v1/admin/users")
async def list_users(request: Request, limit: int = 50, offset: int = 0):
    return await AdminController.list_users(request, limit=limit, offset=offset)


@app.get("/api/v1/admin/users/{user_id}")
async def get_user(request: Request, user_id: str):
    return await AdminController.get_user(request, user_id)


@app.put("/api/v1/admin/users/{user_id}")
async def update_user(request: Request, user_id: str):
    return await AdminController.update_user(request, user_id)


@app.delete("/api/v1/admin/users/{user_id}")
async def delete_user(request: Request, user_id: str):
    return await AdminController.delete_user(request, user_id)


@app.get("/api/v1/admin/orders")
async def list_all_orders(request: Request, limit: int = 50, offset: int = 0, status: str = None):
    return await AdminController.list_all_orders(request, limit=limit, offset=offset, status=status)


@app.get("/api/v1/admin/activity")
async def get_recent_activity(request: Request, limit: int = 20):
    return await AdminController.get_recent_activity(request, limit=limit)


@app.get("/api/v1/admin/settings")
async def get_settings(request: Request):
    return await AdminController.get_settings(request)


@app.put("/api/v1/admin/settings")
async def update_settings(request: Request):
    return await AdminController.update_settings(request)


@app.post("/api/v1/upload/image")
async def upload_image(file: UploadFile = File(...)):
    
    try:

        allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
        if file.content_type not in allowed_types:
            return JSONResponse({"error": "Invalid file type. Only JPEG, PNG, WEBP, GIF allowed"}, status_code=400)

        file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = UPLOAD_DIR / unique_filename

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        return {
            "filename": unique_filename,
            "url": f"/uploads/{unique_filename}",
            "content_type": file.content_type,
            "size": len(content)
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/v1/upload/generation")
async def upload_generation(file: UploadFile = File(...)):
    
    try:

        allowed_types = ["model/stl", "model/obj", "application/octet-stream"]
        if file.content_type not in allowed_types and not file.filename.endswith(('.stl', '.obj')):
            return JSONResponse({"error": "Invalid file type. Only STL and OBJ files allowed"}, status_code=400)

        file_ext = file.filename.split(".")[-1] if "." in file.filename else "stl"
        unique_filename = f"gen_{uuid.uuid4()}.{file_ext}"
        file_path = UPLOAD_DIR / unique_filename

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        return {
            "filename": unique_filename,
            "url": f"/uploads/{unique_filename}",
            "content_type": file.content_type,
            "size": len(content)
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    
    from fastapi.responses import FileResponse
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    return JSONResponse({"error": "File not found"}, status_code=404)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
