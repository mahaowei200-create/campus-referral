from pathlib import Path    # 系统路径工具，用来定位 static 前端文件夹

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles   # FastAPI 内置静态文件托管工具，用来加载 html/js/css 前端页面

from app.api.routes import router
from app.api.campus_referral import (
    admin_router as campus_referral_admin_router,
    router as campus_referral_router,
)
from app.core.bootstrap import create_schema, seed_data
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.tool_queue import get_tool_queue_worker


def create_app() -> FastAPI:
    app = FastAPI(title="MindBridge Python", version="0.1.0")

    @app.middleware("http")     #用途：开发时修改前端页面，刷新浏览器立刻生效，不用手动清缓存。
    async def no_cache_frontend_assets(request, call_next):
        response = await call_next(request)           # 先放行请求，执行接口/页面逻辑，拿到返回响应
        path = request.url.path
        if path == "/" or path.endswith((".html", ".js", ".css")):   # 如果是首页 / 或者 html/js/css 前端静态资源
            response.headers["Cache-Control"] = "no-store"                # 设置响应头，告诉浏览器不要缓存页面
        return response 

    @app.on_event("startup")    #项目启动时会执行
    def startup() -> None:      
        create_schema()      #根据ORM实体创建数据库表
        db = SessionLocal()
        try:
            seed_data(db)
        finally:
            db.close()
        #后台异步任务工作器
        worker = get_tool_queue_worker(get_settings())
        worker.start()
        app.state.tool_queue_worker = worker

    @app.on_event("shutdown")
    def shutdown() -> None:
        worker = getattr(app.state, "tool_queue_worker", None)
        if worker is not None:
            worker.stop()

    app.include_router(router)
    app.include_router(campus_referral_router)
    app.include_router(campus_referral_admin_router)
    #把项目内置的前端页面（html、js、css、图片）托管给 FastAPI，访问网站根路径直接打开网页，后端自带前端，不用单独开前端服务。
    static_dir = Path(__file__).resolve().parent / "static"
    # app.mount () 是把某一段 URL 前缀，绑定到独立文件服务。mount 专门处理静态资源，不走后端业务逻辑，直接返回本地文件。
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")    
    return app


app = create_app()
