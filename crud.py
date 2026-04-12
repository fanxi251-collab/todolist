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


# ==================== 账目模块 ====================

DEFAULT_EXPENSE_CATEGORIES = [
    {"name": "餐饮", "icon": "🍔", "color": "#F59E0B"},
    {"name": "交通", "icon": "🚗", "color": "#3B82F6"},
    {"name": "购物", "icon": "🛒", "color": "#EC4899"},
    {"name": "娱乐", "icon": "🎮", "color": "#8B5CF6"},
    {"name": "学习", "icon": "📚", "color": "#10B981"},
    {"name": "住宿", "icon": "🏠", "color": "#6366F1"},
    {"name": "医疗", "icon": "💊", "color": "#EF4444"},
    {"name": "其他", "icon": "📦", "color": "#9CA3AF"},
]

DEFAULT_INCOME_CATEGORIES = [
    {"name": "工资", "icon": "💰", "color": "#10B981"},
    {"name": "奖金", "icon": "🎁", "color": "#F59E0B"},
    {"name": "兼职", "icon": "💼", "color": "#3B82F6"},
    {"name": "投资收益", "icon": "📈", "color": "#8B5CF6"},
    {"name": "其他", "icon": "💵", "color": "#9CA3AF"},
]


def init_default_categories(db: Session):
    """初始化默认类别"""
    existing = db.query(models.Category).first()
    if existing:
        return  # 已初始化
    
    # 创建支出类别
    for cat in DEFAULT_EXPENSE_CATEGORIES:
        db_category = models.Category(
            name=cat["name"],
            type="expense",
            icon=cat["icon"],
            color=cat["color"]
        )
        db.add(db_category)
    
    # 创建收入类别
    for cat in DEFAULT_INCOME_CATEGORIES:
        db_category = models.Category(
            name=cat["name"],
            type="income",
            icon=cat["icon"],
            color=cat["color"]
        )
        db.add(db_category)
    
    db.commit()


def get_categories(db: Session, type: str = None):
    """获取类别列表"""
    query = db.query(models.Category)
    if type:
        query = query.filter(models.Category.type == type)
    return query.order_by(models.Category.type, models.Category.name).all()


def get_category_by_id(db: Session, category_id: int):
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def create_category(db: Session, category: schemas.CategoryCreate):
    db_category = models.Category(
        name=category.name,
        type=category.type,
        icon=category.icon,
        color=category.color
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: int, category: schemas.CategoryCreate):
    db_category = get_category_by_id(db, category_id)
    if not db_category:
        return None
    
    db_category.name = category.name
    db_category.type = category.type
    db_category.icon = category.icon
    db_category.color = category.color
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int):
    db_category = get_category_by_id(db, category_id)
    if not db_category:
        return None
    db.delete(db_category)
    db.commit()
    return True


def create_expense(db: Session, expense: schemas.ExpenseCreate):
    db_expense = models.Expense(
        amount=expense.amount,
        description=expense.description,
        date=expense.date,
        category_id=expense.category_id
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def get_expenses(db: Session, start_date: date = None, end_date: date = None, category_id: int = None, limit: int = 100):
    query = db.query(models.Expense)
    if start_date:
        query = query.filter(models.Expense.date >= start_date)
    if end_date:
        query = query.filter(models.Expense.date <= end_date)
    if category_id:
        query = query.filter(models.Expense.category_id == category_id)
    return query.order_by(models.Expense.date.desc(), models.Expense.id.desc()).limit(limit).all()


def get_expense_by_id(db: Session, expense_id: int):
    return db.query(models.Expense).filter(models.Expense.id == expense_id).first()


def update_expense(db: Session, expense_id: int, expense: schemas.ExpenseUpdate):
    db_expense = get_expense_by_id(db, expense_id)
    if not db_expense:
        return None
    
    if expense.amount is not None:
        db_expense.amount = expense.amount
    if expense.description is not None:
        db_expense.description = expense.description
    if expense.date is not None:
        db_expense.date = expense.date
    if expense.category_id is not None:
        db_expense.category_id = expense.category_id
    
    db_expense.updated_at = datetime.now()
    db.commit()
    db.refresh(db_expense)
    return db_expense


def delete_expense(db: Session, expense_id: int):
    db_expense = get_expense_by_id(db, expense_id)
    if not db_expense:
        return None
    db.delete(db_expense)
    db.commit()
    return True


def create_income(db: Session, income: schemas.IncomeCreate):
    db_income = models.Income(
        amount=income.amount,
        description=income.description,
        date=income.date,
        category_id=income.category_id
    )
    db.add(db_income)
    db.commit()
    db.refresh(db_income)
    return db_income


def get_incomes(db: Session, start_date: date = None, end_date: date = None, category_id: int = None, limit: int = 100):
    query = db.query(models.Income)
    if start_date:
        query = query.filter(models.Income.date >= start_date)
    if end_date:
        query = query.filter(models.Income.date <= end_date)
    if category_id:
        query = query.filter(models.Income.category_id == category_id)
    return query.order_by(models.Income.date.desc(), models.Income.id.desc()).limit(limit).all()


def get_income_by_id(db: Session, income_id: int):
    return db.query(models.Income).filter(models.Income.id == income_id).first()


def update_income(db: Session, income_id: int, income: schemas.IncomeUpdate):
    db_income = get_income_by_id(db, income_id)
    if not db_income:
        return None
    
    if income.amount is not None:
        db_income.amount = income.amount
    if income.description is not None:
        db_income.description = income.description
    if income.date is not None:
        db_income.date = income.date
    if income.category_id is not None:
        db_income.category_id = income.category_id
    
    db_income.updated_at = datetime.now()
    db.commit()
    db.refresh(db_income)
    return db_income


def delete_income(db: Session, income_id: int):
    db_income = get_income_by_id(db, income_id)
    if not db_income:
        return None
    db.delete(db_income)
    db.commit()
    return True


def get_account_summary(db: Session, start_date: date = None, end_date: date = None):
    """获取账目汇总"""
    if not start_date:
        start_date = date.today().replace(day=1)  # 默认本月
    if not end_date:
        end_date = date.today()
    
    # 支出统计
    expenses = db.query(models.Expense).filter(
        models.Expense.date >= start_date,
        models.Expense.date <= end_date
    ).all()
    total_expense = sum(e.amount for e in expenses)
    
    # 按类别统计支出
    expense_by_category = {}
    for e in expenses:
        cat_name = e.category.name if e.category else "未分类"
        cat_color = e.category.color if e.category else "#9CA3AF"
        if cat_name not in expense_by_category:
            expense_by_category[cat_name] = {"name": cat_name, "amount": 0, "color": cat_color}
        expense_by_category[cat_name]["amount"] += e.amount
    
    # 收入统计
    incomes = db.query(models.Income).filter(
        models.Income.date >= start_date,
        models.Income.date <= end_date
    ).all()
    total_income = sum(i.amount for i in incomes)
    
    # 按类别统计收入
    income_by_category = {}
    for i in incomes:
        cat_name = i.category.name if i.category else "未分类"
        cat_color = i.category.color if i.category else "#9CA3AF"
        if cat_name not in income_by_category:
            income_by_category[cat_name] = {"name": cat_name, "amount": 0, "color": cat_color}
        income_by_category[cat_name]["amount"] += i.amount
    
    # 按日统计
    daily_stats = {}
    for e in expenses:
        day_key = e.date.isoformat()
        if day_key not in daily_stats:
            daily_stats[day_key] = {"date": day_key, "expense": 0, "income": 0}
        daily_stats[day_key]["expense"] += e.amount
    for i in incomes:
        day_key = i.date.isoformat()
        if day_key not in daily_stats:
            daily_stats[day_key] = {"date": day_key, "expense": 0, "income": 0}
        daily_stats[day_key]["income"] += i.amount
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "expense_by_category": sorted(expense_by_category.values(), key=lambda x: x["amount"], reverse=True),
        "income_by_category": sorted(income_by_category.values(), key=lambda x: x["amount"], reverse=True),
        "daily_stats": sorted(daily_stats.values(), key=lambda x: x["date"])
    }


# ==================== 智能对话模块 ====================

def create_conversation(db: Session, title: str = "新对话"):
    db_conversation = models.Conversation(title=title)
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


def get_conversation(db: Session, conversation_id: int):
    return db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()


def list_conversations(db: Session, limit: int = 50):
    return db.query(models.Conversation).order_by(models.Conversation.updated_at.desc()).limit(limit).all()


def update_conversation_title(db: Session, conversation_id: int, title: str):
    db_conversation = get_conversation(db, conversation_id)
    if not db_conversation:
        return None
    db_conversation.title = title
    db_conversation.updated_at = datetime.now()
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


def delete_conversation(db: Session, conversation_id: int):
    db_conversation = get_conversation(db, conversation_id)
    if not db_conversation:
        return None
    db.delete(db_conversation)
    db.commit()
    return True


def add_message(db: Session, conversation_id: int, role: str, content: str):
    db_message = models.Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )
    db.add(db_message)
    
    # 更新会话的更新时间
    db_conversation = get_conversation(db, conversation_id)
    if db_conversation:
        db_conversation.updated_at = datetime.now()
    
    db.commit()
    db.refresh(db_message)
    return db_message


def get_messages(db: Session, conversation_id: int):
    return db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.created_at).all()
