from pydantic import BaseModel


class RasterPointOut(BaseModel):
    raster: str
    lon: float
    lat: float
    value: float | None


class RasterStatsOut(BaseModel):
    name: str
    description: str
    width: int
    height: int
    crs: str
    bounds: list[float]
    resolution: str
    min: float | None
    max: float | None
    mean: float | None
    std: float | None


class SoilProfileOut(BaseModel):
    location: dict
    analyzed_at: str
    dem: float | None = None
    slope: float | None = None
    aspect: float | None = None
    landuse: int | None = None
    landuse_name: str | None = None
    soc: float | None = None
    sand: float | None = None
    silt: float | None = None
    clay: float | None = None
    ph: float | None = None
    texture: int | None = None
    texture_name: str | None = None
    soil_grade: str | None = None
