from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, delete as sql_delete
from datetime import datetime, date, timedelta
from typing import List, Optional
import models
import schemas


def get_notes(db: Session, skip: int = 0, limit: int = 100, search: str = None, tag_id: int = None, include_deleted: bool = False):
    query = db.query(models.Note)
    
    if not include_deleted:
        query = query.filter(models.Note.is_deleted == False)
    
    if search:
        query = query.filter(models.Note.content.contains(search))
    
    if tag_id:
        query = query.filter(models.Note.tags.any(models.Tag.id == tag_id))
    
    return query.order_by(models.Note.is_pinned.desc(), models.Note.created_at.desc()).offset(skip).limit(limit).all()


def get_note_by_id(db: Session, note_id: int):
    return db.query(models.Note).filter(models.Note.id == note_id).first()


def get_note_by_date(db: Session, reminder_date: date, exclude_id: int = None):
    query = db.query(models.Note).filter(
        and_(
            models.Note.reminder_date == reminder_date,
            models.Note.is_deleted == False
        )
    )
    if exclude_id:
        query = query.filter(models.Note.id != exclude_id)
    return query.first()


def get_today_notes(db: Session):
    today = date.today()
    return db.query(models.Note).filter(
        and_(
            models.Note.reminder_date == today,
            models.Note.is_deleted == False
        )
    ).all()


def get_deleted_notes(db: Session):
    return db.query(models.Note).filter(
        models.Note.is_deleted == True
    ).order_by(models.Note.deleted_at.desc()).all()


def create_note(db: Session, note: schemas.NoteCreate, image_path: Optional[str] = None, attachment_path: Optional[str] = None):
    db_note = models.Note(
        content=note.content,
        reminder_date=note.reminder_date,
        image_path=image_path,
        attachment_path=attachment_path,
        is_pinned=note.is_pinned
    )
    
    if note.tag_ids:
        tags = db.query(models.Tag).filter(models.Tag.id.in_(note.tag_ids)).all()
        db_note.tags = tags
    
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def update_note(db: Session, note_id: int, note: schemas.NoteUpdate, image_path: Optional[str] = None, attachment_path: Optional[str] = None):
    db_note = get_note_by_id(db, note_id)
    if not db_note:
        return None
    
    if note.content is not None:
        db_note.content = note.content
    if note.reminder_date is not None:
        db_note.reminder_date = note.reminder_date
    if image_path is not None:
        db_note.image_path = image_path
    if attachment_path is not None:
        db_note.attachment_path = attachment_path
    if note.is_pinned is not None:
        db_note.is_pinned = note.is_pinned
    if note.tag_ids is not None:
        tags = db.query(models.Tag).filter(models.Tag.id.in_(note.tag_ids)).all()
        db_note.tags = tags
    
    db_note.updated_at = datetime.now()
    db.commit()
    db.refresh(db_note)
    return db_note


def pin_note(db: Session, note_id: int, is_pinned: bool = True):
    db_note = get_note_by_id(db, note_id)
    if not db_note:
        return None
    
    db_note.is_pinned = is_pinned
    db_note.updated_at = datetime.now()
    db.commit()
    db.refresh(db_note)
    return db_note


def soft_delete_note(db: Session, note_id: int):
    db_note = get_note_by_id(db, note_id)
    if not db_note:
        return None
    
    db_note.is_deleted = True
    db_note.deleted_at = datetime.now()
    db.commit()
    return db_note


def restore_note(db: Session, note_id: int):
    db_note = get_note_by_id(db, note_id)
    if not db_note:
        return None
    
    db_note.is_deleted = False
    db_note.deleted_at = None
    db.commit()
    return db_note


def permanently_delete_note(db: Session, note_id: int):
    db_note = get_note_by_id(db, note_id)
    if not db_note:
        return None
    
    db.delete(db_note)
    db.commit()
    return True


def cleanup_old_deleted_notes(db: Session, days: int = 7):
    cutoff_date = datetime.now() - timedelta(days=days)
    deleted_notes = db.query(models.Note).filter(
        and_(
            models.Note.is_deleted == True,
            models.Note.deleted_at < cutoff_date
        )
    ).all()
    
    for note in deleted_notes:
        db.delete(note)
    
    db.commit()
    return len(deleted_notes)


def get_tags(db: Session):
    return db.query(models.Tag).all()


def get_tag_by_id(db: Session, tag_id: int):
    return db.query(models.Tag).filter(models.Tag.id == tag_id).first()


def create_tag(db: Session, tag: schemas.TagCreate):
    db_tag = models.Tag(name=tag.name, color=tag.color)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag


def delete_tag(db: Session, tag_id: int):
    db_tag = get_tag_by_id(db, tag_id)
    if not db_tag:
        return None
    
    # 先解除与便签的关联
    db_tag.notes = []
    db.commit()
    
    db.delete(db_tag)
    db.commit()
    return db_tag
