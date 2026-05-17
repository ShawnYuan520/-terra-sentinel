from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin_user
from app.models.knowledge_article import KnowledgeArticle

router = APIRouter(prefix="/knowledge", tags=["知识库"])


class ArticleCreate(BaseModel):
    title: str
    category: str = "general"
    summary: str | None = None
    tags: str | None = None
    content: str


class ArticleUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    summary: str | None = None
    tags: str | None = None
    content: str | None = None


def _article_to_dict(a: KnowledgeArticle) -> dict:
    tags_list = [t.strip() for t in a.tags.split(",")] if a.tags else []
    return {
        "id": a.id,
        "title": a.title,
        "category": a.category,
        "summary": a.summary,
        "tags": a.tags,
        "tags_list": tags_list,
        "content": a.content,
        "views": a.views or 0,
        "publish_time": a.publish_time.isoformat() if a.publish_time else None,
    }


@router.get("/articles")
async def list_articles(
    category: str | None = Query(None),
    q: str | None = Query(None, description="搜索关键词"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q_stmt = select(KnowledgeArticle)
    count_q = select(func.count()).select_from(KnowledgeArticle)
    if category:
        q_stmt = q_stmt.where(KnowledgeArticle.category == category)
        count_q = count_q.where(KnowledgeArticle.category == category)
    if q:
        search = f"%{q}%"
        q_stmt = q_stmt.where(
            KnowledgeArticle.title.ilike(search) |
            KnowledgeArticle.content.ilike(search) |
            KnowledgeArticle.summary.ilike(search)
        )
        count_q = count_q.where(
            KnowledgeArticle.title.ilike(search) |
            KnowledgeArticle.content.ilike(search) |
            KnowledgeArticle.summary.ilike(search)
        )
    q_stmt = q_stmt.order_by(KnowledgeArticle.publish_time.desc()).offset(offset).limit(limit)
    result = await db.execute(q_stmt)
    articles = list(result.scalars().all())
    total = (await db.execute(count_q)).scalar()
    return {
        "total": total,
        "items": [_article_to_dict(a) for a in articles],
    }


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """获取所有分类及其真实文章数量"""
    result = await db.execute(
        select(KnowledgeArticle.category, func.count(KnowledgeArticle.id))
        .group_by(KnowledgeArticle.category)
    )
    rows = list(result.all())
    category_meta = {
        "usage_guide": {"label": "使用指南", "icon": "BookOpen", "color": "#22C55E"},
        "policy": {"label": "政策补贴", "icon": "FileText", "color": "#EF4444"},
        "faq": {"label": "常见问题", "icon": "MessageCircle", "color": "#F59E0B"},
        "tutorial": {"label": "新手教程", "icon": "GraduationCap", "color": "#3B82F6"},
        "general": {"label": "综合", "icon": "Folder", "color": "#8B5CF6"},
    }
    categories = []
    for cat, count in rows:
        meta = category_meta.get(cat or "", {})
        categories.append({
            "key": cat or "general",
            "label": meta.get("label", cat or "综合"),
            "icon": meta.get("icon", "Folder"),
            "color": meta.get("color", "#64748B"),
            "count": count,
        })
    return {"categories": categories}


@router.get("/hot-questions")
async def hot_questions(db: AsyncSession = Depends(get_db)):
    """获取热门问题（从FAQ分类中按浏览量排序）"""
    result = await db.execute(
        select(KnowledgeArticle)
        .where(KnowledgeArticle.category == "faq")
        .order_by(KnowledgeArticle.views.desc())
        .limit(6)
    )
    articles = list(result.scalars().all())
    questions = [a.title for a in articles]
    # fallback if not enough FAQ articles
    if len(questions) < 6:
        fallback = [
            "秸秆腐解剂什么时候喷效果最好？",
            "玉米秸秆还田最佳湿度是多少？",
            "腐解剂用量怎么计算？",
            "碳汇交易怎么参与？",
            "土壤pH值偏低怎么改良？",
            "NDVI指数下降说明什么问题？",
        ]
        questions = questions + fallback[len(questions):]
    return {"questions": questions}


@router.get("/articles/{article_id}")
async def get_article(article_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeArticle).where(KnowledgeArticle.id == article_id))
    a = result.scalar_one_or_none()
    if not a:
        raise HTTPException(404, "文章不存在")
    # 增加浏览量
    a.views = (a.views or 0) + 1
    await db.flush()
    return _article_to_dict(a)


@router.post("/articles", status_code=status.HTTP_201_CREATED)
async def create_article(
    data: ArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    article = KnowledgeArticle(
        title=data.title,
        category=data.category,
        summary=data.summary,
        tags=data.tags,
        content=data.content,
    )
    db.add(article)
    await db.flush()
    return _article_to_dict(article)


@router.put("/articles/{article_id}")
async def update_article(
    article_id: str,
    data: ArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    result = await db.execute(select(KnowledgeArticle).where(KnowledgeArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(404, "文章不存在")

    if data.title is not None:
        article.title = data.title
    if data.category is not None:
        article.category = data.category
    if data.summary is not None:
        article.summary = data.summary
    if data.tags is not None:
        article.tags = data.tags
    if data.content is not None:
        article.content = data.content

    await db.flush()
    return _article_to_dict(article)


@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user),
):
    result = await db.execute(select(KnowledgeArticle).where(KnowledgeArticle.id == article_id))
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(404, "文章不存在")
    await db.delete(article)
    return {"ok": True}
