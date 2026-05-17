"""空间查询服务 – SQLite适配版，用 shapely 解析 GeoJSON 字符串"""
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta, timezone
from shapely.geometry import shape as shply_shape
from shapely import box as shply_box
from app.models.field import Field
from app.models.remote_sensing_ts import RemoteSensingTimeseries


class PostGISSpatialService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _parse_geom(self, geom_text: str):
        """GeoJSON 字符串 → shapely geometry"""
        return shply_shape(json.loads(geom_text))

    async def get_field_geom(self, field_id: str) -> dict | None:
        """获取地块几何 + 元数据"""
        result = await self.db.execute(select(Field).where(Field.id == field_id))
        field = result.scalar_one_or_none()
        if not field:
            return None
        s = self._parse_geom(field.geom)
        return {
            "id": str(field.id),
            "name": field.name,
            "geom": field.geom,
            "centroid": [s.centroid.x, s.centroid.y],
            "area_ha": field.area_ha or round(s.area * 0.0001, 2),
            "bounds": list(s.bounds),
            "crop_type": field.crop_type,
        }

    async def get_fields_in_viewport(self, xmin: float, ymin: float, xmax: float, ymax: float, user_id: str | None = None) -> list[dict]:
        """视口裁剪查询 – 在 Python 层过滤"""
        vp_box = shply_box(xmin, ymin, xmax, ymax)
        q = select(Field)
        if user_id:
            q = q.where(Field.user_id == user_id)
        result = await self.db.execute(q)
        fields = []
        for f in result.scalars():
            try:
                s = self._parse_geom(f.geom)
            except Exception:
                continue
            if not s.intersects(vp_box):
                continue
            fields.append({
                "id": str(f.id),
                "name": f.name,
                "centroid": [s.centroid.x, s.centroid.y],
                "area_ha": f.area_ha or round(s.area * 0.0001, 2),
                "crop_type": f.crop_type,
            })
        return fields

    async def get_ts_for_field(self, field_id: str, days: int = 90) -> list[dict]:
        """获取地块最近 N 天遥感时序"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(RemoteSensingTimeseries)
            .where(
                RemoteSensingTimeseries.field_id == field_id,
                RemoteSensingTimeseries.timestamp >= cutoff,
            )
            .order_by(desc(RemoteSensingTimeseries.timestamp))
        )
        return [
            {
                "timestamp": r.timestamp.isoformat(),
                "source": r.source,
                "ndvi": r.ndvi,
                "evi": r.evi,
                "ndwi": r.ndwi,
                "surface_temp": r.surface_temp,
                "cloud_cover": r.cloud_cover,
            }
            for r in result.scalars()
        ]