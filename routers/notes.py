from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import os
import uuid
from datetime import datetime

from database import get_db
import crud
import schemas

router = APIRouter(prefix="/notes", tags=["notes"])

UPLOAD_DIR = "uploads"
ATTACHMENT_DIR = "attachments"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ATTACHMENT_DIR, exist_ok=True)


@router.get("", response_model=List[schemas.NoteResponse])
def get_notes(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    tag_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    notes = crud.get_notes(db, skip=skip, limit=limit, search=search, tag_id=tag_id)
    return notes


@router.get("/today", response_model=List[schemas.NoteResponse])
def get_today_notes(db: Session = Depends(get_db)):
    notes = crud.get_today_notes(db)
    return notes


@router.post("", response_model=schemas.NoteResponse)
def create_note(
    content: Optional[str] = Form(None),
    reminder_date: Optional[date] = Form(None),
    is_pinned: bool = Form(False),
    tag_ids: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    attachment: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    tag_id_list = []
    if tag_ids:
        tag_id_list = [int(tid) for tid in tag_ids.split(",") if tid]
    
    image_path = None
    if image:
        file_ext = os.path.splitext(image.filename)[1] or ".jpg"
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        with open(file_path, "wb") as f:
            f.write(image.file.read())
        
        image_path = f"/uploads/{file_name}"
    
    attachment_path = None
    if attachment:
        file_ext = os.path.splitext(attachment.filename)[1]
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(ATTACHMENT_DIR, file_name)
        
        with open(file_path, "wb") as f:
            f.write(attachment.file.read())
        
        attachment_path = f"/attachments/{file_name}"
    
    note_create = schemas.NoteCreate(
        content=content,
        reminder_date=reminder_date,
        is_pinned=is_pinned,
        tag_ids=tag_id_list
    )
    
    note = crud.create_note(db, note_create, image_path, attachment_path)
    return note


@router.put("/{note_id}", response_model=schemas.NoteResponse)
def update_note(
    note_id: int,
    content: Optional[str] = Form(None),
    reminder_date: Optional[date] = Form(None),
    is_pinned: Optional[bool] = Form(None),
    tag_ids: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    attachment: Optional[UploadFile] = File(None),
    remove_image: bool = Form(False),
    remove_attachment: bool = Form(False),
    db: Session = Depends(get_db)
):
    existing_note = crud.get_note_by_id(db, note_id)
    if not existing_note:
        raise HTTPException(status_code=404, detail="便签不存在")
    
    tag_id_list = None
    if tag_ids is not None:
        tag_id_list = [int(tid) for tid in tag_ids.split(",") if tid]
    
    image_path = None
    if remove_image and existing_note.image_path:
        old_file = os.path.join(".", existing_note.image_path.lstrip("/"))
        if os.path.exists(old_file):
            os.remove(old_file)
    elif image:
        if existing_note.image_path:
            old_file = os.path.join(".", existing_note.image_path.lstrip("/"))
            if os.path.exists(old_file):
                os.remove(old_file)
        
        file_ext = os.path.splitext(image.filename)[1] or ".jpg"
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        with open(file_path, "wb") as f:
            f.write(image.file.read())
        
        image_path = f"/uploads/{file_name}"
    
    attachment_path = None
    if remove_attachment and existing_note.attachment_path:
        old_file = os.path.join(".", existing_note.attachment_path.lstrip("/"))
        if os.path.exists(old_file):
            os.remove(old_file)
    elif attachment:
        if existing_note.attachment_path:
            old_file = os.path.join(".", existing_note.attachment_path.lstrip("/"))
            if os.path.exists(old_file):
                os.remove(old_file)
        
        file_ext = os.path.splitext(attachment.filename)[1]
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(ATTACHMENT_DIR, file_name)
        
        with open(file_path, "wb") as f:
            f.write(attachment.file.read())
        
        attachment_path = f"/attachments/{file_name}"
    
    note_update = schemas.NoteUpdate(
        content=content,
        reminder_date=reminder_date,
        is_pinned=is_pinned,
        tag_ids=tag_id_list
    )
    
    note = crud.update_note(db, note_id, note_update, image_path, attachment_path)
    return note


@router.patch("/{note_id}/pin")
def pin_note(note_id: int, is_pinned: bool = True, db: Session = Depends(get_db)):
    note = crud.pin_note(db, note_id, is_pinned)
    if not note:
        raise HTTPException(status_code=404, detail="便签不存在")
    return {"message": f"已{'置顶' if is_pinned else '取消置顶'}"}


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = crud.soft_delete_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="便签不存在")
    return {"message": "已移到回收站"}


@router.post("/export")
def export_notes(format: str = "json", db: Session = Depends(get_db)):
    notes = crud.get_notes(db, include_deleted=True)
    tags = crud.get_tags(db)
    
    if format == "json":
        import json
        data = {
            "notes": [schemas.NoteResponse.model_validate(n).model_dump() for n in notes],
            "tags": [schemas.TagResponse.model_validate(t).model_dump() for t in tags],
            "exported_at": datetime.now().isoformat()
        }
        return data
    elif format == "csv":
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Content", "Reminder Date", "Created At", "Is Deleted", "Is Pinned"])
        
        for note in notes:
            writer.writerow([
                note.id,
                note.content or "",
                str(note.reminder_date) if note.reminder_date else "",
                note.created_at.isoformat() if note.created_at else "",
                note.is_deleted,
                note.is_pinned
            ])
        
        return {"csv": output.getvalue()}
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")
