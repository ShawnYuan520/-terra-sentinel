from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.services.carbon.carbon import CarbonService
from app.schemas.carbon import CarbonReportCreate, CarbonReportOut, CarbonReportListOut

router = APIRouter(prefix="/carbon", tags=["碳汇报告"])


@router.post("/reports", response_model=CarbonReportOut)
async def generate_report(
    data: CarbonReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    svc = CarbonService(db)
    return await svc.generate_report(current_user["sub"], data)


@router.get("/reports", response_model=CarbonReportListOut)
async def list_reports(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    svc = CarbonService(db)
    total, items = await svc.get_reports_by_user(current_user["sub"], offset, limit)
    return CarbonReportListOut(total=total, items=items)


@router.get("/reports/{report_id}/pdf")
async def download_report_pdf(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """下载碳汇报告 PDF（需安装 WeasyPrint 系统依赖）"""
    from app.services.carbon.pdf_report import PDFReportService  # 懒加载，避免 WeasyPrint 阻塞启动
    svc = PDFReportService(db)
    pdf_bytes = await svc.generate(report_id, current_user["sub"])
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=carbon_report_{report_id[:8]}.pdf"},
    )