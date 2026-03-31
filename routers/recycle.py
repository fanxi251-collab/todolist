from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
import crud
import schemas

router = APIRouter(prefix="/recycle", tags=["recycle"])


@router.get("", response_model=list[schemas.NoteResponse])
def get_recycle_notes(db: Session = Depends(get_db)):
    notes = crud.get_deleted_notes(db)
    return notes


@router.post("/{note_id}/restore")
def restore_note(note_id: int, db: Session = Depends(get_db)):
    note = crud.restore_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="回收站中找不到该便签")
    return {"message": "已恢复便签"}


@router.delete("/{note_id}")
def permanently_delete_note(note_id: int, db: Session = Depends(get_db)):
    result = crud.permanently_delete_note(db, note_id)
    if not result:
        raise HTTPException(status_code=404, detail="回收站中找不到该便签")
    return {"message": "已彻底删除"}


@router.post("/cleanup")
def cleanup_old_notes(days: int = 7, db: Session = Depends(get_db)):
    count = crud.cleanup_old_deleted_notes(db, days)
    return {"message": f"已清理 {count} 条过期便签"}
