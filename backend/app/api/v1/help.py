"""帮助中心 API — FAQs和搜索"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.knowledge_article import KnowledgeArticle
from app.models.notification import Notification

router = APIRouter(prefix="/help", tags=["帮助"])


class ContactRequest(BaseModel):
    name: str = ""
    email: str = ""
    message: str


@router.get("/faqs")
async def list_faqs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeArticle)
        .where(KnowledgeArticle.category == "faq")
        .order_by(KnowledgeArticle.views.desc())
        .limit(20)
    )
    articles = list(result.scalars().all())
    return {
        "total": len(articles),
        "items": [
            {
                "id": a.id,
                "question": a.title,
                "answer": a.content,
                "summary": a.summary,
                "tags": [t.strip() for t in a.tags.split(",")] if a.tags else [],
                "views": a.views or 0,
            }
            for a in articles
        ],
    }


@router.get("/search")
async def search_help(
    q: str = Query(..., description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
):
    search = f"%{q}%"
    result = await db.execute(
        select(KnowledgeArticle)
        .where(
            KnowledgeArticle.title.ilike(search) |
            KnowledgeArticle.content.ilike(search) |
            KnowledgeArticle.summary.ilike(search)
        )
        .order_by(KnowledgeArticle.views.desc())
        .limit(20)
    )
    articles = list(result.scalars().all())
    return {
        "total": len(articles),
        "query": q,
        "items": [
            {
                "id": a.id,
                "title": a.title,
                "summary": a.summary,
                "category": a.category,
                "views": a.views or 0,
                "publish_time": a.publish_time.isoformat() if a.publish_time else None,
            }
            for a in articles
        ],
    }


@router.get("/categories")
async def help_categories(db: AsyncSession = Depends(get_db)):
    """帮助中心的分类导航结构"""
    return {
        "categories": [
            {"key": "getting-started", "label": "快速入门", "icon": "Rocket", "description": "5分钟了解平台核心功能"},
            {"key": "usage_guide", "label": "功能指南", "icon": "BookOpen", "description": "各功能的详细操作说明"},
            {"key": "faq", "label": "常见问题", "icon": "MessageCircle", "description": "用户最常问的问题"},
            {"key": "tutorial", "label": "视频教程", "icon": "Play", "description": "手把手教你使用平台"},
            {"key": "policy", "label": "政策解读", "icon": "FileText", "description": "最新的农业政策法规"},
            {"key": "general", "label": "更新日志", "icon": "Clock", "description": "平台版本更新记录"},
            {"key": "contact", "label": "联系我们", "icon": "Phone", "description": "客服和技术支持"},
        ],
    }


@router.get("/hot-tags")
async def hot_tags(db: AsyncSession = Depends(get_db)):
    """热门搜索标签"""
    result = await db.execute(
        select(KnowledgeArticle.tags)
        .where(KnowledgeArticle.tags.isnot(None))
        .limit(50)
    )
    all_tags: list[str] = []
    for (tags_str,) in result.all():
        if tags_str:
            all_tags.extend(t.strip() for t in tags_str.split(",") if t.strip())

    # 按出现频率排序取前8
    from collections import Counter
    tag_counts = Counter(all_tags)
    top_tags = [tag for tag, _ in tag_counts.most_common(8)]

    if len(top_tags) < 5:
        top_tags.extend(["NDVI分析", "田块管理", "AI分析", "数据导出", "处方图生成"])
        top_tags = list(dict.fromkeys(top_tags))[:8]

    return {"tags": top_tags}


@router.post("/contact")
async def submit_contact(data: ContactRequest, db: AsyncSession = Depends(get_db)):
    """提交联系表单 — 存入通知表供管理员查看"""
    contact_text = f"[用户反馈] {data.name or '匿名'}"
    if data.email:
        contact_text += f" ({data.email})"
    contact_text += f": {data.message}"
    notif = Notification(user_id="admin", text=contact_text, notify_type="contact")
    db.add(notif)
    await db.flush()
    return {"ok": True, "message": "您的留言已收到，我们会尽快回复！"}
