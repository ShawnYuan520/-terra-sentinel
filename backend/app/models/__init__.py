"""所有模型统一在此导入，确保 Base.metadata 能发现全部表。"""
from app.models.user import User
from app.models.field import Field
from app.models.soil_record import SoilRecord
from app.models.decomposer_type import DecomposerType
from app.models.remote_sensing_ts import RemoteSensingTimeseries
from app.models.carbon_report import CarbonReport
from app.models.knowledge_article import KnowledgeArticle
from app.models.ai_agent_log import AIAgentLog
from app.models.raster_layer import RasterLayer
from app.models.machinery import Machinery
from app.models.notification_setting import NotificationSetting
from app.models.team_member import TeamMember
from app.models.device import Device
from app.models.login_device import LoginDevice
from app.models.notification import Notification

__all__ = [
    "User", "Field", "SoilRecord", "DecomposerType",
    "RemoteSensingTimeseries", "CarbonReport", "KnowledgeArticle",
    "AIAgentLog", "RasterLayer", "Machinery",
    "NotificationSetting", "TeamMember", "Device", "LoginDevice", "Notification",
]