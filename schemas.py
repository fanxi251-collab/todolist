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
    is_pinned: bool = False


class NoteCreate(NoteBase):
    tag_ids: List[int] = []


class NoteUpdate(BaseModel):
    content: Optional[str] = None
    reminder_date: Optional[date] = None
    tag_ids: Optional[List[int]] = None
    is_pinned: Optional[bool] = None


class NoteResponse(NoteBase):
    id: int
    image_path: Optional[str] = None
    attachment_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True


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


# ==================== 账目模块 ====================

class CategoryBase(BaseModel):
    name: str
    type: str  # 'expense' 或 'income'
    icon: str = "💰"
    color: str = "#3B82F6"


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ExpenseBase(BaseModel):
    amount: int  # 金额（分）
    description: Optional[str] = None
    date: date
    category_id: Optional[int] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    amount: Optional[int] = None
    description: Optional[str] = None
    date: Optional[date] = None
    category_id: Optional[int] = None


class ExpenseResponse(ExpenseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True


class IncomeBase(BaseModel):
    amount: int  # 金额（分）
    description: Optional[str] = None
    date: date
    category_id: Optional[int] = None


class IncomeCreate(IncomeBase):
    pass


class IncomeUpdate(BaseModel):
    amount: Optional[int] = None
    description: Optional[str] = None
    date: Optional[date] = None
    category_id: Optional[int] = None


class IncomeResponse(IncomeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True


class AccountSummary(BaseModel):
    """账目汇总"""
    total_income: int
    total_expense: int
    balance: int
    expense_by_category: List[dict]
    income_by_category: List[dict]
    daily_stats: List[dict]


# ==================== 智能对话模块 ====================

class MessageCreate(BaseModel):
    role: str
    content: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: Optional[str] = "新对话"


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
