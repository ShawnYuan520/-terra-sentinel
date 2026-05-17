"""Agent tool registry — tool registration + LLM function-calling schemas"""
from app.prompts import get_system_prompt

# 工具执行器注册表
_tool_executors: dict[str, callable] = {}


def register_tool(name: str):
    """装饰器：注册工具执行函数"""
    def decorator(func):
        _tool_executors[name] = func
        return func
    return decorator


async def execute_tool(tool_name: str, args: dict, db) -> dict:
    """执行单个工具调用"""
    executor = _tool_executors.get(tool_name)
    if not executor:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return await executor(db, **args)
    except Exception as e:
        return {"error": str(e)}


SYSTEM_PROMPT = get_system_prompt()

# DeepSeek / OpenAI 兼容的 function calling schema
TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "analyze_soil",
            "description": "分析当前选中地块的土壤数据，返回土壤状况评价和施肥建议。field_id 由系统自动填充。",
            "parameters": {
                "type": "object",
                "properties": {
                    "field_id": {"type": "string", "description": "田块 UUID，系统自动填充无需手动指定"},
                },
                "required": ["field_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取当前选中地块的实时天气、7天预报和农业气象指标。field_id 由系统自动填充。",
            "parameters": {
                "type": "object",
                "properties": {
                    "field_id": {"type": "string", "description": "田块 UUID，系统自动填充无需手动指定"},
                },
                "required": ["field_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_carbon",
            "description": "分析当前选中地块的碳汇数据，诊断影响因子并给出管理建议。field_id 由系统自动填充。",
            "parameters": {
                "type": "object",
                "properties": {
                    "field_id": {"type": "string", "description": "田块 UUID，系统自动填充无需手动指定"},
                },
                "required": ["field_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ndvi_trend",
            "description": "获取当前选中地块的 NDVI 植被指数时序趋势。field_id 由系统自动填充。",
            "parameters": {
                "type": "object",
                "properties": {
                    "field_id": {"type": "string", "description": "田块 UUID，系统自动填充无需手动指定"},
                    "days": {"type": "integer", "description": "历史天数，默认 90"},
                },
                "required": ["field_id"],
            },
        },
    },
]
