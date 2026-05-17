"""PDF 碳汇报告生成服务"""
import io
from pathlib import Path
from datetime import datetime, timezone
from weasyprint import HTML
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.carbon.carbon import CarbonService
from app.services.geo.postgis import PostGISSpatialService
from app.services.gee.gee_service import GEEService
from app.services.weather.weather_service import WeatherService

TEMPLATE_DIR = Path(__file__).parent / "templates"


class PDFReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(self, report_id: str, user_id: str) -> bytes:
        """生成碳汇报告 PDF，返回 bytes"""
        carbon_svc = CarbonService(self.db)
        geo_svc = PostGISSpatialService(self.db)
        gee_svc = GEEService()
        weather_svc = WeatherService()

        # 获取报告数据
        _, reports = await carbon_svc.get_reports_by_user(user_id, 0, 100)
        report = next((r for r in reports if str(r.id) == report_id), None)
        if not report:
            raise ValueError("报告不存在")

        # 地块信息
        field_info = await geo_svc.get_field_geom(str(report.field_id))
        centroid = field_info["centroid"] if field_info else [120.39, 36.06]

        # NDVI 数据
        ndvi_data = await gee_svc.get_ndvi_timeseries(str(report.field_id), centroid[0], centroid[1], 180)
        ndvi_values = [d.get("ndvi", 0) for d in ndvi_data if "ndvi" in d]
        mean_ndvi = round(sum(ndvi_values) / len(ndvi_values), 3) if ndvi_values else 0
        ndvi_trend = "上升" if len(ndvi_values) >= 2 and ndvi_values[-1] > ndvi_values[0] else "下降" if len(ndvi_values) >= 2 else "稳定"

        # 天气数据
        weather = await weather_svc.get_current_weather(centroid[1], centroid[0])

        # AI 分析
        ai_analysis = report.ai_analysis or "AI 分析暂未生成。建议通过 AI 助手获取详细诊断。"

        # 建议
        recommendations = self._build_recommendations(report, mean_ndvi, weather)

        # 渲染模板
        template = (TEMPLATE_DIR / "report.html").read_text(encoding="utf-8")
        html = template.format(
            field_name=field_info.get("name", "未知") if field_info else "未知",
            field_id=str(report.field_id),
            crop_type=field_info.get("crop_type", "未指定") if field_info else "未指定",
            area_ha=field_info.get("area_ha", 0) if field_info else 0,
            period_start=report.period_start.strftime("%Y-%m-%d"),
            period_end=report.period_end.strftime("%Y-%m-%d"),
            carbon_amount=report.carbon_amount or 0,
            straw_amount=report.straw_amount or 0,
            organic_matter="待测",
            mean_ndvi=mean_ndvi,
            ndvi_trend=ndvi_trend,
            temperature=weather["temperature_c"],
            humidity=weather["humidity_pct"],
            precipitation=weather["precipitation_mm"],
            description=weather["description"],
            ai_analysis=ai_analysis,
            recommendations=recommendations,
            report_date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            report_id=report_id,
        )

        # 生成 PDF
        pdf_bytes = HTML(string=html).write_pdf()
        return pdf_bytes

    def _build_recommendations(self, report, mean_ndvi, weather) -> str:
        tips = []
        if report.carbon_amount and report.carbon_amount < 30:
            tips.append("1. 增加秸秆还田量，当前碳固定量偏低，建议下一周期增加至 1.5 倍。")
        else:
            tips.append("1. 维持当前秸秆还田策略，碳汇量处于合理水平。")

        if mean_ndvi < 0.40:
            tips.append("2. NDVI 偏低，建议检查作物健康状况，必要时增施有机肥。")
        elif mean_ndvi > 0.60:
            tips.append("2. NDVI 表现良好，植被覆盖度高，有利于土壤碳积累。")

        if weather["precipitation_mm"] < 5:
            tips.append("3. 近期降雨偏少，建议适当灌溉以促进秸秆腐解。")
        else:
            tips.append("3. 近期降雨充足，秸秆腐解条件良好。")

        return "\n".join(tips)