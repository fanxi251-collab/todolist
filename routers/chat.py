from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import json
from datetime import date

from database import get_db
import crud
import schemas

router = APIRouter(prefix="/chat", tags=["智能对话"])


def get_dashscope_client():
    """获取 DashScope 客户端"""
    try:
        from dashscope import Generation
        return Generation
    except ImportError:
        raise HTTPException(status_code=500, detail="请安装 dashscope: pip install dashscope")


def call_qwen(prompt: str, history: list = None) -> str:
    """调用通义千问 API"""
    from dashscope import Generation
    import os
    
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="未设置 DASHSCOPE_API_KEY 环境变量")
    
    # 构建消息
    messages = []
    
    # 系统提示
    system_prompt = """你是一个智能生活助手，可以帮助用户管理便签、待办事项、账本等。

你可以：
1. 查看用户的便签记录和今日待办
2. 根据用户的数据给出合理的规划建议
3. 当用户要求添加便签或待办时，提取信息并创建

重要规则：
- 如果用户要求创建便签/待办，请先提取：内容、日期（格式YYYY-MM-DD）
- 创建成功后，告知用户"已为您创建便签：[内容]，日期：[日期]"
- 如果无法提取完整信息，询问用户补充

请用友好、简洁的中文回答问题。"""
    messages.append({"role": "system", "content": system_prompt})
    
    # 历史消息
    if history:
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
    
    # 当前问题
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = Generation.call(
            model="qwen-max",
            messages=messages,
            result_format="message"
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            raise HTTPException(status_code=500, detail=f"API调用失败: {response.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调用失败: {str(e)}")


def get_user_data_summary(db: Session) -> str:
    """获取用户数据摘要，供 AI 了解用户状态"""
    summary = []
    
    # 今日待办
    today = date.today()
    today_notes = db.query(crud.models.Note).filter(
        crud.models.Note.reminder_date == today,
        crud.models.Note.is_deleted == False
    ).all()
    
    if today_notes:
        summary.append("📅 今日待办:")
        for note in today_notes[:10]:
            content = note.content[:50] if note.content else "无内容"
            summary.append(f"  - {content}")
    else:
        summary.append("📅 今日待办: 无")
    
    # 便签（最近10条）
    notes = db.query(crud.models.Note).filter(
        crud.models.Note.is_deleted == False
    ).order_by(crud.models.Note.created_at.desc()).limit(10).all()
    
    if notes:
        summary.append("\n📝 最近便签:")
        for note in notes[:5]:
            content = note.content[:30] if note.content else "无内容"
            summary.append(f"  - {content}")
    
    # 账目（本月的收支）
    from datetime import datetime
    start_date = today.replace(day=1)
    
    expenses = db.query(crud.models.Expense).filter(
        crud.models.Expense.date >= start_date,
        crud.models.Expense.date <= today
    ).all()
    
    incomes = db.query(crud.models.Income).filter(
        crud.models.Income.date >= start_date,
        crud.models.Income.date <= today
    ).all()
    
    total_exp = sum(e.amount for e in expenses)
    total_inc = sum(i.amount for i in incomes)
    
    summary.append(f"\n💰 本月账目:")
    summary.append(f"  - 支出: ¥{(total_exp/100):.2f}")
    summary.append(f"  - 收入: ¥{(total_inc/100):.2f}")
    summary.append(f"  - 结余: ¥{((total_inc-total_exp)/100):.2f}")
    
    return "\n".join(summary)


@router.post("", response_model=dict)
def chat(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    conversation_id = request.conversation_id
    
    # 检测是否需要创建便签
    note_creation = detect_note_creation(request.message)
    
    # 获取或创建会话
    if conversation_id:
        conversation = crud.get_conversation(db, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        # 创建新会话
        conversation = crud.create_conversation(db, title=request.message[:30])
        conversation_id = conversation.id
    
    # 保存用户消息
    crud.add_message(db, conversation_id, "user", request.message)
    
    # 获取历史消息
    messages = crud.get_messages(db, conversation_id)
    history = [{"role": m.role, "content": m.content} for m in messages[:-1]]
    
    # 获取用户数据摘要
    user_data = get_user_data_summary(db)
    
    # 如果检测到创建便签请求，先创建便签
    created_note = None
    if note_creation:
        created_note = create_note_from_ai_request(db, note_creation)
    
    # 构建完整提示（含用户数据）
    full_prompt = f"""用户当前数据:
{user_data}

用户问题: {request.message}"""
    
    try:
        # 调用 AI
        response = call_qwen(full_prompt, history)
        
        # 如果创建了便签，在回复中添加成功信息
        if created_note:
            date_str = created_note.reminder_date.strftime("%Y年%m月%d日") if created_note.reminder_date else "今天"
            response = f"✅ 已为您创建便签！\n\n📝 内容：{created_note.content}\n📅 日期：{date_str}\n\n---\n\n{response}"
        
        # 保存助手回复
        crud.add_message(db, conversation_id, "assistant", response)
        
        return {
            "response": response,
            "conversation_id": conversation_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def detect_note_creation(message: str) -> dict:
    """检测用户是否要求创建便签，提取信息"""
    from datetime import datetime
    import re
    
    # 关键词检测
    keywords = ["添加", "创建", "记下", "帮我记", "设置提醒", "待办", "任务", "安排"]
    has_keyword = any(k in message for k in keywords)
    
    if not has_keyword:
        return None
    
    # 尝试提取日期
    date_patterns = [
        r'(\d{1,2})月(\d{1,2})日',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(\d{4})/(\d{1,2})/(\d{1,2})',
        r'今天',
        r'明天',
        r'后天',
    ]
    
    date_str = None
    reminder_date = None
    
    today = date.today()
    
    if "今天" in message:
        reminder_date = today
    elif "明天" in message:
        reminder_date = today.replace(day=today.day + 1)
    elif "后天" in message:
        reminder_date = today.replace(day=today.day + 2)
    else:
        for pattern in date_patterns:
            match = re.search(pattern, message)
            if match:
                if pattern == r'(\d{1,2})月(\d{1,2})日':
                    month, day = int(match.group(1)), int(match.group(2))
                    year = today.year
                    if month < today.month or (month == today.month and day < today.day):
                        year += 1
                    reminder_date = date(year, month, day)
                elif pattern in [r'(\d{4})-(\d{1,2})-(\d{1,2})', r'(\d{4})/(\d{1,2})/(\d{1,2})']:
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    reminder_date = date(year, month, day)
                break
    
    # 提取内容（移除日期相关文字）
    content = message
    for word in ["添加", "创建", "记下", "帮我记", "设置提醒", "待办", "任务", "安排", "线上笔试", "笔试"]:
        content = content.replace(word, "")
    content = content.strip("，。！？:：1234567890-/")
    
    if not content:
        return None
    
    return {
        "content": content,
        "reminder_date": reminder_date
    }


def create_note_from_ai_request(db: Session, note_info: dict) -> object:
    """根据 AI 解析的信息创建便签"""
    note_data = schemas.NoteCreate(
        content=note_info.get("content", ""),
        reminder_date=note_info.get("reminder_date"),
        is_pinned=False,
        tag_ids=[]
    )
    return crud.create_note(db, note_data, None, None)


@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db)):
    """获取对话列表"""
    conversations = crud.list_conversations(db)
    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat()
            }
            for c in conversations
        ]
    }


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """获取对话详情"""
    conversation = crud.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    messages = crud.get_messages(db, conversation_id)
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    }


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """删除对话"""
    result = crud.delete_conversation(db, conversation_id)
    if not result:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "会话已删除"}


@router.post("/conversations")
def create_conversation(request: schemas.ConversationCreate, db: Session = Depends(get_db)):
    """创建新对话"""
    conversation = crud.create_conversation(db, title=request.title or "新对话")
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat()
    }