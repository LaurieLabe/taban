from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import init_db
from routers import auth, users, events, match, messages
import os

app = FastAPI(title="她伴 API", version="1.0.0")

# CORS — 允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# 注册路由
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(match.router)
app.include_router(messages.router)

@app.get("/api")
def api_root():
    return {"message": "她伴 API 运行中"}

# 前端静态文件（前端和后端同端口，无跨域问题）
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(FRONTEND_DIR):
    @app.get("/app")
    @app.get("/app/")
    async def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")