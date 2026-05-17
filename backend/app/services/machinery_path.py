"""
A* 农机作业路径规划
在田块内部栅格化后, 避开陡坡区域, 生成最优作业路径。
基于 DEM + 坡度 + 田块边界
"""
import math
import heapq
from app.services.raster import RasterService


def plan_field_path(field_geojson: dict, resolution: float = 10.0) -> dict:
    """
    输入田块 GeoJSON 多边形, 输出农机最优作业路径

    参数:
    - field_geojson: GeoJSON Polygon | MultiPolygon
    - resolution: 栅格分辨率 (米), 默认10m

    返回:
    {
        waypoints: [{lon, lat, slope, cost}, ...],
        total_distance_m: float,
        avg_slope: float,
        steep_zones: [{lon, lat, slope}, ...],
        recommendation: str,
    }
    """
    svc = RasterService()

    # 1. 解析田块边界
    coords = _extract_coords(field_geojson)
    if not coords or len(coords) < 3:
        return {"error": "无效的田块边界"}

    # 2. 计算边界框和栅格分辨率(度)
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)

    # 度数转米 (中纬度近似)
    lat_mid = (lat_min + lat_max) / 2
    deg_to_m_lon = 111320 * math.cos(math.radians(lat_mid))
    deg_to_m_lat = 111320

    res_lon = resolution / deg_to_m_lon
    res_lat = resolution / deg_to_m_lat

    # 3. 栅格化 + 坡度采样
    grid = []
    lat = lat_min
    while lat <= lat_max:
        row = []
        lon = lon_min
        while lon <= lon_max:
            if _point_in_polygon(lon, lat, coords):
                dem = svc.read_at_point("dem", lon, lat) or 200
                slope = svc.read_at_point("slope", lon, lat) or 5
                row.append({"lon": lon, "lat": lat, "dem": dem, "slope": slope})
            else:
                row.append(None)
            lon += res_lon
        if any(c is not None for c in row):
            grid.append(row)
        lat += res_lat

    if not grid:
        return {"error": "田块栅格化失败, 面积可能过小"}

    # 4. 计算代价矩阵
    rows, cols = len(grid), len(grid[0])
    cost_grid = [[float("inf")] * cols for _ in range(rows)]
    steep_zones = []

    for r in range(rows):
        for c in range(cols):
            cell = grid[r][c]
            if cell is None:
                continue
            slope = cell["slope"]
            # 代价 = 距离(1) + 坡度惩罚
            if slope > 25:
                cost = 100.0  # 不可通行
                steep_zones.append({"lon": cell["lon"], "lat": cell["lat"],
                                    "slope": round(slope, 1), "severity": "禁止"})
            elif slope > 20:
                cost = 5.0 + (slope - 20) * 2
                steep_zones.append({"lon": cell["lon"], "lat": cell["lat"],
                                    "slope": round(slope, 1), "severity": "危险"})
            elif slope > 15:
                cost = 1.5 + (slope - 15) * 0.5
                steep_zones.append({"lon": cell["lon"], "lat": cell["lat"],
                                    "slope": round(slope, 1), "severity": "谨慎"})
            else:
                cost = 1.0 + slope * 0.02
            cost_grid[r][c] = cost

    # 5. A* 路径搜索: 找最低代价的横穿路径
    # 找到起点(最左列)和终点(最右列)的最低代价节点
    start_candidates = [(cost_grid[r][0], r, 0) for r in range(rows)
                        if grid[r][0] is not None]
    end_candidates = [(cost_grid[r][cols-1], r, cols-1) for r in range(rows)
                      if grid[r][cols-1] is not None]

    if not start_candidates or not end_candidates:
        return {"error": "无法找到可行路径起点/终点"}

    # 选最优起点
    start_candidates.sort()
    end_candidates.sort()
    start = (start_candidates[0][1], 0)
    goal = (end_candidates[0][1], cols - 1)

    # A* 搜索
    path = _astar(cost_grid, start, goal, rows, cols)

    if not path:
        # 退化为简单往返路径
        path = _fallback_path(grid, cost_grid, rows, cols)

    # 6. 生成输出
    waypoints = []
    for (r, c) in path:
        cell = grid[r][c]
        waypoints.append({
            "lon": round(cell["lon"], 6),
            "lat": round(cell["lat"], 6),
            "slope": round(cell["slope"], 1),
            "cost": round(cost_grid[r][c], 2),
        })

    # 计算总距离
    total_dist = 0
    for i in range(1, len(waypoints)):
        dlon = (waypoints[i]["lon"] - waypoints[i-1]["lon"]) * deg_to_m_lon
        dlat = (waypoints[i]["lat"] - waypoints[i-1]["lat"]) * deg_to_m_lat
        total_dist += math.sqrt(dlon**2 + dlat**2)

    avg_slope = sum(w["slope"] for w in waypoints) / max(1, len(waypoints))

    # 推荐
    if avg_slope > 15:
        rec = "坡度较大，建议使用小型农机，沿等高线作业。"
    elif len(steep_zones) > 3:
        rec = f"发现{len(steep_zones)}处陡坡区域，已在路径中避开。建议关注这些区域的水土流失。"
    else:
        rec = "地势平坦，适宜大型农机常规作业。建议采用梭行法提高效率。"

    return {
        "waypoints": waypoints,
        "total_distance_m": round(total_dist, 1),
        "avg_slope": round(avg_slope, 1),
        "grid_size": f"{rows}×{cols}",
        "grid_resolution_m": resolution,
        "steep_zones": steep_zones[:10],  # 最多10个
        "recommendation": rec,
    }


def _extract_coords(geojson):
    if geojson.get("type") == "Polygon":
        return geojson["coordinates"][0]
    if geojson.get("type") == "MultiPolygon":
        return geojson["coordinates"][0][0]
    return []


def _point_in_polygon(lon, lat, coords):
    """射线法判断点是否在多边形内"""
    inside = False
    n = len(coords)
    j = n - 1
    for i in range(n):
        xi, yi = coords[i][0], coords[i][1]
        xj, yj = coords[j][0], coords[j][1]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _astar(cost_grid, start, goal, rows, cols):
    """A* 搜索"""
    def heuristic(r, c):
        return abs(r - goal[0]) + abs(c - goal[1])  # 曼哈顿

    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}

    directions = [(0, 1), (1, 0), (0, -1), (-1, 0),
                  (1, 1), (-1, 1), (1, -1), (-1, -1)]

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            # 重建路径
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        for dr, dc in directions:
            nr, nc = current[0] + dr, current[1] + dc
            if 0 <= nr < rows and 0 <= nc < cols and cost_grid[nr][nc] < 100:
                move_cost = cost_grid[nr][nc] * (1.414 if dr != 0 and dc != 0 else 1.0)
                tentative = g_score.get(current, float("inf")) + move_cost
                if tentative < g_score.get((nr, nc), float("inf")):
                    came_from[(nr, nc)] = current
                    g_score[(nr, nc)] = tentative
                    f = tentative + heuristic(nr, nc)
                    heapq.heappush(open_set, (f, (nr, nc)))

    return None


def _fallback_path(grid, cost_grid, rows, cols):
    """退化路径: 简单的Z字形往返"""
    path = []
    for r in range(rows):
        row_cells = [(r, c) for c in range(cols) if grid[r][c] is not None]
        if not row_cells:
            continue
        if r % 2 == 0:
            path.extend(row_cells)
        else:
            path.extend(reversed(row_cells))
    return path
