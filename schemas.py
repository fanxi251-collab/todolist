from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List


class TagBase(BaseModel):
    name: str
    color: str = "#3B82F6"


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: int

    class Config:
        from_attributes = True


class NoteBase(BaseModel):
    content: Optional[str] = None
    reminder_date: Optional[date] = None


class NoteCreate(NoteBase):
    tag_ids: List[int] = []


class NoteUpdate(BaseModel):
    content: Optional[str] = None
    reminder_date: Optional[date] = None
    tag_ids: Optional[List[int]] = None


class NoteResponse(NoteBase):
    id: int
    image_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True


class NoteWithImage(NoteResponse):
    image_data: Optional[str] = None


class WeatherResponse(BaseModel):
    city: str
    weather: str
    temperature: str
    wind: str
    humidity: str
    date: str


class ExportData(BaseModel):
    notes: List[NoteResponse]
    tags: List[TagResponse]
    exported_at: datetime
