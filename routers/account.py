from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta

from database import get_db
import crud
import schemas

router = APIRouter(prefix="/account", tags=["account"])


# ==================== 类别管理 ====================

@router.get("/categories", response_model=List[schemas.CategoryResponse])
def get_categories(type: Optional[str] = None, db: Session = Depends(get_db)):
    """获取类别列表"""
    return crud.get_categories(db, type)


@router.post("/categories", response_model=schemas.CategoryResponse)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    """创建类别"""
    return crud.create_category(db, category)


@router.put("/categories/{category_id}", response_model=schemas.CategoryResponse)
def update_category(category_id: int, category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    """更新类别"""
    result = crud.update_category(db, category_id, category)
    if not result:
        raise HTTPException(status_code=404, detail="类别不存在")
    return result


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """删除类别"""
    result = crud.delete_category(db, category_id)
    if not result:
        raise HTTPException(status_code=404, detail="类别不存在")
    return {"message": "类别已删除"}


# ==================== 支出管理 ====================

@router.get("/expenses", response_model=List[schemas.ExpenseResponse])
def get_expenses(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取支出列表"""
    return crud.get_expenses(db, start_date, end_date, category_id, limit)


@router.post("/expenses", response_model=schemas.ExpenseResponse)
def create_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    """创建支出"""
    return crud.create_expense(db, expense)


@router.put("/expenses/{expense_id}", response_model=schemas.ExpenseResponse)
def update_expense(expense_id: int, expense: schemas.ExpenseUpdate, db: Session = Depends(get_db)):
    """更新支出"""
    result = crud.update_expense(db, expense_id, expense)
    if not result:
        raise HTTPException(status_code=404, detail="支出记录不存在")
    return result


@router.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    """删除支出"""
    result = crud.delete_expense(db, expense_id)
    if not result:
        raise HTTPException(status_code=404, detail="支出记录不存在")
    return {"message": "支出已删除"}


# ==================== 收入管理 ====================

@router.get("/incomes", response_model=List[schemas.IncomeResponse])
def get_incomes(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取收入列表"""
    return crud.get_incomes(db, start_date, end_date, category_id, limit)


@router.post("/incomes", response_model=schemas.IncomeResponse)
def create_income(income: schemas.IncomeCreate, db: Session = Depends(get_db)):
    """创建收入"""
    return crud.create_income(db, income)


@router.put("/incomes/{income_id}", response_model=schemas.IncomeResponse)
def update_income(income_id: int, income: schemas.IncomeUpdate, db: Session = Depends(get_db)):
    """更新收入"""
    result = crud.update_income(db, income_id, income)
    if not result:
        raise HTTPException(status_code=404, detail="收入记录不存在")
    return result


@router.delete("/incomes/{income_id}")
def delete_income(income_id: int, db: Session = Depends(get_db)):
    """删除收入"""
    result = crud.delete_income(db, income_id)
    if not result:
        raise HTTPException(status_code=404, detail="收入记录不存在")
    return {"message": "收入已删除"}


# ==================== 账目汇总 ====================

@router.get("/summary", response_model=schemas.AccountSummary)
def get_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """获取账目汇总"""
    return crud.get_account_summary(db, start_date, end_date)