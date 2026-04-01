from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from database import engine, Base, get_db, SessionLocal
from routers import notes, recycle, weather
import crud
import schemas

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        crud.cleanup_old_deleted_notes(db, days=7)
    finally:
        db.close()
    yield


app = FastAPI(title="Todo List API", description="简洁清爽的待办事项管理平台", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes.router)
app.include_router(recycle.router)
app.include_router(weather.router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

attachment_dir = os.path.join(os.path.dirname(__file__), "attachments")
os.makedirs(attachment_dir, exist_ok=True)
app.mount("/attachments", StaticFiles(directory=attachment_dir), name="attachments")


@app.get("/")
def root():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return FileResponse(index_path)


@app.get("/tags", tags=["tags"])
def get_tags(db: SessionLocal = Depends(get_db)):
    tags = crud.get_tags(db)
    return tags


@app.post("/tags", tags=["tags"])
def create_tag(tag: schemas.TagCreate, db: SessionLocal = Depends(get_db)):
    return crud.create_tag(db, tag)


@app.delete("/tags/{tag_id}", tags=["tags"])
def delete_tag(tag_id: int, db: SessionLocal = Depends(get_db)):
    result = crud.delete_tag(db, tag_id)
    if not result:
        raise HTTPException(status_code=404, detail="标签不存在")
    return {"message": "标签已删除"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
