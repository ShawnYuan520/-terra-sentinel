"""种子数据 – 东北区域 Demo 数据（不依赖任何外部文件）"""
import asyncio
import json
import math
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./agrispatial.db")
# SQLite 需要 check_same_thread，PostgreSQL 不需要
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_async_engine(DATABASE_URL, echo=False, connect_args=_connect_args)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    from app.models import (
        User, Field, SoilRecord, DecomposerType, KnowledgeArticle,
        CarbonReport, RemoteSensingTimeseries, RasterLayer, Machinery
    )
    from app.core.security import hash_password
    from app.core.database import Base
    from app.services.synthetic_data import read_soil_profile, read_stats
    from app.services.raster import RASTER_CONFIG

    # 确保所有表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # ── 清空所有数据 ──
        for t in [
            RemoteSensingTimeseries, CarbonReport, SoilRecord, Field,
            KnowledgeArticle, DecomposerType, RasterLayer, Machinery, User
        ]:
            await db.execute(t.__table__.delete())

        # ══════ 栅格图层元数据 (从合成统计信息) ══════
        for name, cfg in RASTER_CONFIG.items():
            stats = read_stats(name)
            b = stats["bounds"] if stats else [0, 0, 0, 0]
            db.add(RasterLayer(
                id=f"raster-{name}",
                name=name, filename=cfg["file"], description=cfg["desc"],
                width=stats.get("width"), height=stats.get("height"),
                crs=stats.get("crs"), resolution=stats.get("resolution"),
                bounds_left=b[0], bounds_bottom=b[1], bounds_right=b[2], bounds_top=b[3],
                min_value=stats.get("min"), max_value=stats.get("max"), mean_value=stats.get("mean"),
            ))
        await db.flush()
        print(f"  [DB] {len(RASTER_CONFIG)} raster layer metadata records")

        # ══════ 用户 ══════
        admin = User(
            id="admin-001", username="admin",
            hashed_password=hash_password("admin123"),
            role="admin", phone="13800000000", area="黑龙江省农业技术推广中心"
        )
        farmer1 = User(
            id="farmer-001", username="farmer1",
            hashed_password=hash_password("123456"),
            role="farmer", phone="13800001111", area="黑龙江双城"
        )
        farmer2 = User(
            id="farmer-002", username="farmer2",
            hashed_password=hash_password("123456"),
            role="farmer", phone="13800002222", area="黑龙江五常"
        )
        db.add_all([admin, farmer1, farmer2])

        # ══════ 腐解剂类型 ══════
        decomposers = [
            DecomposerType(
                id="d-001", name="高活性腐解剂·北方型",
                suitable_crops="玉米,小麦,水稻", suitable_soil="黑土,草甸土",
                usage_guide="每亩用量5kg，秸秆还田后均匀喷施于地表，配合翻压效果更佳",
                description="适用于东北黑土区，耐低温环境，可快速分解秸秆纤维，同步抑制土壤病原菌",
                features="快速腐解,抑菌驱虫,耐低温,促根壮苗",
            ),
            DecomposerType(
                id="d-002", name="温和型腐解剂·标准",
                suitable_crops="小麦,大豆", suitable_soil="棕壤,褐土",
                usage_guide="每亩用量3kg，与秸秆混合翻压入土15-20cm",
                description="适合有机质含量丰富的土壤，温和分解有机质，维持土壤微生态平衡",
                features="维持微生态,缓释养分,减少板结,保护蚯蚓",
            ),
            DecomposerType(
                id="d-003", name="保水型腐解剂·旱作区",
                suitable_crops="玉米,高粱,马铃薯", suitable_soil="栗钙土,黄绵土",
                usage_guide="每亩用量4kg，覆土后灌溉一次，保持土壤湿润",
                description="针对干旱/半干旱地区设计，增强土壤保水能力，减少蒸发损失",
                features="保水抗旱,缓释腐解,提高出苗率,减少灌溉需求",
            ),
            DecomposerType(
                id="d-004", name="高肥型腐解剂·增产型",
                suitable_crops="水稻,玉米,大豆", suitable_soil="水稻土,潮土",
                usage_guide="每亩用量5kg，灌水后施用效果最佳，配合有机肥使用",
                description="加速秸秆碳转化为土壤有机质，显著提升SOC含量，适合有机质偏低地块",
                features="增碳培肥,活化养分,增产10-15%,改善团粒结构",
            ),
        ]
        db.add_all(decomposers)

        # ══════ 农机 ══════
        machinery_list = [
            Machinery(id="m-001", name="AgriTrac 智能拖拉机 X500", type="整地机械",
                      description="搭载北斗导航自动驾驶系统，精度±2.5cm，支持夜间作业。配套多种农具实现耕、耙、播一体化。",
                      specs='{"power":"150 马力","width":"3.6m 作业幅宽","fuel":"柴油/国四排放","nav":"北斗+GPS 双模"}',
                      suitable_for="大面积耕整地、播种、中耕", accent="#2EC85D", image_type="tractor"),
            Machinery(id="m-002", name="AgriHarvest 联合收割机 H300", type="收获机械",
                      description="全喂入自走式，割幅3.2m，适应玉米、小麦、大豆等多种作物，损失率<1.5%。",
                      specs='{"power":"180 马力","width":"3.2m 割幅","capacity":"8-12 亩/小时","loss":"<1.5%"}',
                      suitable_for="玉米、小麦、大豆、水稻收获", accent="#D97706", image_type="harvester"),
            Machinery(id="m-003", name="AgriSpray 智能喷雾器 S200", type="植保机械",
                      description="搭载AI视觉识别杂草，变量精准喷施，节省农药30%。无人机+地面自走式双模式。",
                      specs='{"tank":"500L 药箱","width":"12m 喷幅","drones":"2 架 T40","save":"节药30%"}',
                      suitable_for="除草、杀虫、叶面肥喷施", accent="#3B82F6", image_type="sprayer"),
            Machinery(id="m-004", name="AgriTill 旋耕机 R150", type="耕作机械",
                      description="配套120-180马力拖拉机，深耕25cm，碎土率≥85%，适合保护性耕作和秸秆还田。",
                      specs='{"power":"120-180hp","depth":"25cm","width":"2.5m","rate":"碎土率≥85%"}',
                      suitable_for="旋耕、灭茬、秸秆还田、平整土地", accent="#8B5E3C", image_type="tiller"),
            Machinery(id="m-005", name="AgriSeed 精量播种机 P100", type="播种机械",
                      description="气吸式精量播种，单粒率≥95%，行距可调，支持玉米、大豆、甜菜等多种作物。",
                      specs='{"rows":"6 行","spacing":"45-70cm 可调","rate":"单粒率≥95%","speed":"8-10 km/h"}',
                      suitable_for="玉米、大豆、甜菜、向日葵精量播种", accent="#22C55E", image_type="seeder"),
        ]
        db.add_all(machinery_list)

        # ══════ 田块 (黑龙江双城真实坐标范围) ══════
        fields_data = [
            # farmer1的田块
            ("field-001", farmer1.id, "双城试验田A", 126.31, 45.38, 126.33, 45.40, 22.5, "玉米"),
            ("field-002", farmer1.id, "双城试验田B", 126.35, 45.39, 126.37, 45.41, 18.0, "大豆"),
            ("field-003", farmer1.id, "双城向阳坡地", 126.28, 45.36, 126.30, 45.38, 30.0, "玉米"),
            # farmer2的田块
            ("field-004", farmer2.id, "五常水稻田1号", 127.15, 44.92, 127.17, 44.94, 15.0, "水稻"),
            ("field-005", farmer2.id, "五常旱田试验区", 127.18, 44.91, 127.20, 44.93, 12.0, "小麦"),
        ]

        fields = []
        for fid, uid, name, lon1, lat1, lon2, lat2, area, crop in fields_data:
            geom = json.dumps({
                "type": "Polygon",
                "coordinates": [[
                    [lon1, lat1], [lon2, lat1],
                    [lon2, lat2], [lon1, lat2],
                    [lon1, lat1],
                ]]
            })
            f = Field(id=fid, user_id=uid, name=name, geom=geom, area_ha=area, crop_type=crop)
            fields.append(f)
            db.add(f)
        await db.flush()
        print(f"  [DB] {len(fields)} fields")

        # ══════ 土壤记录 (合成数据) ══════
        now = datetime.now(timezone.utc)
        soil_records_data = [
            ("field-001", 126.32, 45.39),
            ("field-002", 126.36, 45.40),
            ("field-003", 126.29, 45.37),
            ("field-004", 127.16, 44.93),
            ("field-005", 127.19, 44.92),
        ]
        for field_id, lon, lat in soil_records_data:
            soil = read_soil_profile(lon, lat)
            sr = SoilRecord(
                field_id=field_id,
                ph=soil["ph"],
                organic_matter=round((soil["soc"] or 25) * 1.72, 1),
                nitrogen=round((soil["soc"] or 25) * 0.065, 1),
                phosphorus=round(20 + (soil["soc"] or 25) * 0.2, 1),
                potassium=round(120 + (soil["clay"] or 28) * 0.7, 1),
                moisture=round(20 + (soil["silt"] or 42) * 0.04, 1),
                recommended_decomposer_id="d-001" if (soil["soc"] or 30) < 25 else "d-004",
                record_date=now - timedelta(days=30),
            )
            db.add(sr)
            # 历史记录
            sr2 = SoilRecord(
                field_id=field_id,
                ph=round(soil["ph"] + 0.2, 1) if soil["ph"] else 6.8,
                organic_matter=round((soil["soc"] or 25) * 1.72 - 2, 1),
                nitrogen=round((soil["soc"] or 25) * 0.06, 1),
                phosphorus=round(18 + (soil["soc"] or 25) * 0.18, 1),
                potassium=round(115 + (soil["clay"] or 28) * 0.65, 1),
                moisture=round(18 + (soil["silt"] or 42) * 0.04, 1),
                record_date=now - timedelta(days=180),
            )
            db.add(sr2)
        print(f"  [DB] {len(soil_records_data) * 2} soil records (current + historical)")

        # ══════ 碳汇报告 ══════
        carbon_reports_data = [
            ("field-001", farmer1.id, 150.0),
            ("field-002", farmer1.id, 120.0),
            ("field-004", farmer2.id, 200.0),
        ]
        for field_id, user_id, straw in carbon_reports_data:
            soil = read_soil_profile(
                {"field-001": 126.32, "field-002": 126.36, "field-004": 127.16}[field_id],
                {"field-001": 45.39, "field-002": 45.40, "field-004": 44.93}[field_id],
            )
            carbon = round(straw * 0.4 * (soil.get("soc", 30) / 30), 1)
            cr = CarbonReport(
                user_id=user_id, field_id=field_id,
                period_start=datetime(2025, 1, 1, tzinfo=timezone.utc),
                period_end=datetime(2025, 12, 31, tzinfo=timezone.utc),
                straw_amount=straw, carbon_amount=carbon, status="generated",
                ai_analysis=(
                    f"该地块年度碳汇量 {carbon} tCO₂e。土壤有机碳 {soil.get('soc',0):.1f}g/kg，"
                    f"等级{soil.get('soil_grade','良好')}。NDVI均值0.68，"
                    f"植被覆盖良好。建议维持当前秸秆还田策略并监测土壤湿度。"
                ),
            )
            db.add(cr)
        print(f"  [DB] {len(carbon_reports_data)} carbon reports")

        # ══════ 遥感时序 (NDVI合成数据) ══════
        import random
        random.seed(42)
        ndvi_field_centers = {
            "field-001": (126.32, 45.39, 1),    # 耕地
            "field-002": (126.36, 45.40, 1),
            "field-004": (127.16, 44.93, 1),
        }
        rs_count = 0
        for field_id, (lon, lat, lu) in ndvi_field_centers.items():
            soil = read_soil_profile(lon, lat)
            dem = soil.get("dem", 180)
            soc = soil.get("soc", 25)
            base_ndvi = 0.72 - abs(dem - 200) / 2000 + (soc - 20) * 0.004
            base_ndvi = max(0.3, min(0.85, base_ndvi))
            for i in range(0, 180, 5):
                d = now - timedelta(days=i)
                doy = d.timetuple().tm_yday
                seasonal = 0.12 * math.sin(2 * math.pi * (doy - 120) / 365)
                ndvi_val = round(max(0.12, min(0.92, base_ndvi + seasonal + random.uniform(-0.05, 0.05))), 3)
                db.add(RemoteSensingTimeseries(
                    field_id=field_id, timestamp=d,
                    source="Sentinel-2 (synthetic)",
                    ndvi=ndvi_val,
                    evi=round(ndvi_val * 0.65 + random.uniform(-0.03, 0.03), 3),
                    surface_temp=round(15 + 15 * math.sin(2 * math.pi * (doy - 100) / 365) + random.uniform(-3, 3), 1),
                    cloud_cover=round(random.uniform(3, 30), 1),
                ))
                rs_count += 1
        print(f"  [DB] {rs_count} remote sensing time-series points")

        # ══════ 知识库文章 ══════
        articles = [
            KnowledgeArticle(
                id="k-001", title="秸秆还田腐解技术指南",
                category="usage_guide",
                summary="详细介绍秸秆还田的技术要点、腐解剂选择方法和最佳实践流程",
                tags="秸秆还田,腐解剂,技术指南,保护性耕作",
                content="""## 秸秆还田技术指南

### 1. 为什么要秸秆还田？
秸秆还田是保护性耕作的核心技术之一，能有效增加土壤有机质、改善土壤结构、减少化肥用量。

### 2. 技术要点
- **时机选择**：作物收获后立即进行，趁秸秆含水量较高时还田
- **粉碎长度**：玉米秸秆粉碎长度控制在5-10cm
- **翻压深度**：一般15-20cm，沙土地可稍深
- **腐解剂使用**：每亩2-5kg，均匀喷施后翻压

### 3. 腐解剂选择
根据土壤有机质含量和作物类型选择合适的腐解剂类型：
- 有机质偏低(<10g/kg)：选用高活性腐解剂
- 有机质适中(10-25g/kg)：选用标准型腐解剂
- 有机质丰富(>25g/kg)：选用温和型腐解剂

### 4. 注意事项
- 秸秆还田后需保持土壤湿润
- 避免在雨季集中还田
- 配合适量氮肥(5-8kg/亩尿素)调节C/N比""",
                views=1250,
            ),
            KnowledgeArticle(
                id="k-002", title="农业碳汇交易政策解读",
                category="policy",
                summary="解读农业农村部关于推进农业碳汇交易的指导意见，帮助农户了解碳汇交易流程",
                tags="碳汇交易,政策解读,碳中和,碳信用",
                content="""## 农业碳汇交易政策解读

### 政策背景
2024年，农业农村部发布《关于推进农业碳汇交易的指导意见》，明确提出将农业碳汇纳入全国碳市场交易体系。

### 什么是农业碳汇？
农业碳汇是指通过农业生产活动（如秸秆还田、保护性耕作、有机肥施用等）将大气中的CO₂固定在土壤和植被中的过程。

### 碳汇计算方法
每吨秸秆还田约可固定0.4 tCO₂e（吨二氧化碳当量），具体根据土壤类型和气候条件有所差异。

### 交易流程
1. 农户/合作社在碳汇平台注册
2. 第三方机构核证碳汇量
3. 碳汇量挂牌交易
4. 企业购买碳信用

### 收益估算
以100亩玉米田为例，年秸秆还田150kg/亩，可产生约6 tCO₂e碳汇，按当前30元/tCO₂e价格计算，年收入约180元。""",
                views=890,
            ),
            KnowledgeArticle(
                id="k-003", title="常见问题：腐解剂怎么选？",
                category="faq",
                summary="回答农户关于腐解剂选择的常见疑问",
                tags="腐解剂,常见问题,选型指南",
                content="""## 腐解剂常见问题解答

### Q: 腐解剂是什么？
腐解剂是一种微生物制剂，含有多种有益微生物和酶，能加速秸秆纤维素的分解转化。

### Q: 怎么选择适合的腐解剂？
主要考虑以下因素：
1. **土壤有机质含量**：低有机质选高活性型，高有机质选温和型
2. **作物类型**：玉米秸秆纤维素含量高，需要活性较强的腐解剂
3. **气候条件**：干旱地区选保水型，冷凉地区选耐低温型
4. **土壤质地**：黏重土壤需配合疏松型腐解剂

### Q: 腐解剂什么时候用效果最好？
作物收获后立即使用效果最佳，此时秸秆含水量较高，温度适宜微生物活动。

### Q: 使用腐解剂后多久能看到效果？
一般15-25天可看到明显腐解效果，具体取决于温度和湿度条件。""",
                views=670,
            ),
            KnowledgeArticle(
                id="k-004", title="NDVI植被指数在农业中的应用",
                category="usage_guide",
                summary="讲解NDVI指数的含义、计算方法及其在作物长势监测中的应用",
                tags="NDVI,遥感,植被指数,长势监测",
                content="""## NDVI植被指数应用指南

### 什么是NDVI？
NDVI（归一化植被指数）是利用卫星遥感数据计算出的反映植被生长状况的指标，取值范围-1到1。

### NDVI值解读
- NDVI < 0.2：裸土、休耕地或刚播种
- NDVI 0.2-0.4：作物苗期，植被覆盖度低
- NDVI 0.4-0.6：作物生长中期
- NDVI 0.6-0.8：作物旺盛生长期
- NDVI > 0.8：植被覆盖度极高

### 农业应用场景
1. **作物长势监测**：通过NDVI时序变化判断作物生长阶段
2. **产量预估**：NDVI峰值与最终产量高度相关
3. **灾害评估**：干旱、病虫害导致NDVI异常下降
4. **精准施肥**：根据NDVI空间分布进行变量施肥""",
                views=450,
            ),
            KnowledgeArticle(
                id="k-005", title="东北黑土保护性耕作技术规程",
                category="usage_guide",
                summary="农业部颁发的东北黑土区保护性耕作技术标准，涵盖免耕、少耕、秸秆覆盖等核心技术",
                tags="黑土地,保护性耕作,技术规程,标准",
                content="""## 东北黑土保护性耕作技术规程

### 1. 总则
本标准适用于东北黑土区（包括黑龙江、吉林、辽宁及内蒙古东四盟）的玉米、大豆、水稻等主要农作物的保护性耕作。

### 2. 核心技术
#### 2.1 免耕播种
- 前茬作物收获后不翻耕，直接进行下茬播种
- 要求：播种机具有破茬开沟功能，确保种子与土壤良好接触

#### 2.2 秸秆覆盖
- 收获后将秸秆粉碎覆盖地表，覆盖率≥30%
- 玉米秸秆覆盖量3000-6000kg/ha

#### 2.3 深松作业
- 每2-3年进行一次深松，深度30-40cm
- 打破犁底层，增强土壤蓄水能力

### 3. 技术效益
- 减少水土流失50-90%
- 增加土壤有机质0.05-0.1%/年
- 节约作业成本20-30%
- 提高水分利用效率15-25%""",
                views=780,
            ),
            KnowledgeArticle(
                id="k-006", title="2025年农业补贴政策汇总",
                category="policy",
                summary="汇总2025年国家和东北三省的主要农业补贴政策，包括耕地地力保护补贴、秸秆还田补贴等",
                tags="补贴,政策,耕地保护,秸秆还田",
                content="""## 2025年农业补贴政策汇总

### 国家层面
1. **耕地地力保护补贴**：每亩约57-72元，具体以各省发布为准
2. **农机购置补贴**：最高补贴比例30%，重点支持智能农机
3. **秸秆综合利用补贴**：每亩秸秆还田补贴20-40元
4. **碳汇交易试点补贴**：参与碳汇交易的农户可获得额外奖励

### 黑龙江省
1. **黑土地保护补贴**：实施保护性耕作的每亩补贴30-50元
2. **有机肥替代化肥**：每亩补贴100元

### 吉林省
1. **保护性耕作补贴**：每亩补贴25-40元
2. **玉米大豆轮作补贴**：每亩补贴150元

### 如何申请？
1. 向村委会/乡镇农技站提交申请
2. 提供土地承包合同或流转协议
3. 配合第三方核查验收""",
                views=1560,
            ),
            KnowledgeArticle(
                id="k-007", title="土壤检测指标解读",
                category="faq",
                summary="教你看懂土壤检测报告的各项指标：pH、有机质、氮磷钾、微量元素等",
                tags="土壤检测,指标解读,pH,有机质,氮磷钾",
                content="""## 土壤检测指标解读指南

### pH值（酸碱度）
- <5.5：强酸性，需施石灰改良
- 5.5-6.5：微酸性，适宜多数作物
- 6.5-7.5：中性，最适合作物生长
- 7.5-8.5：微碱性
- >8.5：强碱性

### 有机质（g/kg）
- <10：缺乏，需大量增施有机肥
- 10-20：中等
- 20-30：丰富
- >30：很丰富，东北黑土典型值

### 全氮（g/kg）
- <0.5：缺乏
- 0.5-1.0：中等
- 1.0-1.5：丰富
- >1.5：很丰富

### 有效磷（mg/kg）
- <5：极缺
- 5-10：缺乏
- 10-20：中等
- 20-40：丰富
- >40：很丰富

### 速效钾（mg/kg）
- <50：极缺
- 50-100：缺乏
- 100-150：中等
- 150-200：丰富
- >200：很丰富""",
                views=340,
            ),
            KnowledgeArticle(
                id="k-008", title="智慧农业平台使用教程",
                category="tutorial",
                summary="AgriSpatial平台完整使用教程：从注册登录到田块管理、土壤分析、碳汇报告生成",
                tags="教程,使用指南,入门,平台功能",
                content="""## AgriSpatial 智慧农业平台使用教程

### 1. 注册与登录
访问平台网址，点击"注册"创建账号。填写用户名、密码和基本信息。

### 2. 创建田块
登录后在GIS地图页面，点击"新建田块"按钮，在地图上绘制田块边界，填写田块名称和作物类型。

### 3. 土壤分析
选择田块后，点击"土壤分析"可查看：
- 土壤有机碳(SOC)含量
- pH值
- 土壤质地（砂/粉/粘粒比例）
- 土壤肥力等级

### 4. 碳汇报告
在"碳汇报告"页面，选择田块和统计周期，输入秸秆还田量，系统自动计算碳汇量。

### 5. AI助手
点击"AI助手"可与智能助手对话，询问土壤改良、病虫害防治、天气预报等问题。

### 6. 知识库
"知识库"页面提供农业技术文章、政策解读、常见问题解答等资源。""",
                views=2100,
            ),
            KnowledgeArticle(
                id="k-009", title="玉米高产栽培技术",
                category="usage_guide",
                summary="东北春玉米高产栽培全流程技术方案，涵盖品种选择、播种、施肥、病虫害防治等关键环节",
                tags="玉米,高产,栽培技术,东北",
                content="""## 东北春玉米高产栽培技术

### 品种选择
选择适合当地积温条件的高产抗病品种，如先玉335、郑单958等。

### 播种
- **播种期**：4月下旬至5月上旬，地温稳定通过10°C
- **播种密度**：每亩4000-5000株
- **播种深度**：3-5cm

### 施肥方案
- **基肥**：有机肥2000kg/亩 + 复合肥40kg/亩
- **追肥**：拔节期追施尿素15-20kg/亩
- **叶面肥**：抽雄期喷施磷酸二氢钾

### 病虫害防治
- 玉米螟：心叶末期BT制剂灌心
- 大斑病：发病初期喷施丙环唑
- 蚜虫：吡虫啉喷雾防治

### 收获
- 适时晚收，籽粒含水量降至25%以下
- 机械化收获损失率控制在2%以内""",
                views=980,
            ),
            KnowledgeArticle(
                id="k-010", title="气候变化对东北农业的影响与适应",
                category="policy",
                summary="分析气候变化对东北地区农业生产的影响，提出适应性对策",
                tags="气候变化,东北农业,适应对策,粮食安全",
                content="""## 气候变化对东北农业的影响与适应

### 气候变化趋势
1. **温度升高**：东北地区年均温每10年升高约0.3°C
2. **降水变化**：年降水量总体略增但分布不均，春季干旱加剧
3. **极端天气**：暴雨、干旱、低温冷害频次增加

### 对农业的影响
1. **种植边界北移**：玉米种植北界已北移约200km
2. **生长季延长**：无霜期每10年延长约3-5天
3. **病虫害加重**：越冬虫源基数增大，病害发生期提前

### 适应对策
1. **调整品种布局**：选用生育期更长的中晚熟品种
2. **改进耕作制度**：推广保护性耕作和秸秆覆盖
3. **完善水利设施**：加强抗旱水源工程建设
4. **发展智慧农业**：利用遥感监测和精准农业技术""",
                views=560,
            ),
        ]
        db.add_all(articles)
        print(f"  [DB] {len(articles)} knowledge articles")

        await db.commit()
        print("\n=== Seed Complete ===")
        print(f"  10 raster layers (synthetic stats)")
        print(f"  3 users: admin/admin123, farmer1/123456, farmer2/123456")
        print(f"  {len(fields)} fields (with real coordinates)")
        print(f"  {len(soil_records_data) * 2} soil records (synthetic from coordinates)")
        print(f"  4 decomposer types")
        print(f"  5 machinery types")
        print(f"  {len(carbon_reports_data)} carbon reports")
        print(f"  {rs_count} remote sensing time-series points")
        print(f"  {len(articles)} knowledge articles")


if __name__ == "__main__":
    asyncio.run(seed())
