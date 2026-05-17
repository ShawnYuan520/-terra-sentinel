"""Prompt 模板加载器"""
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str, **kwargs) -> str:
    """加载模板文件并填充变量。
    
    Usage:
        load_prompt("soil_analysis", field_name="试验田A", ph=6.8, ...)
    """
    path = PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        return ""
    template = path.read_text(encoding="utf-8")
    if kwargs:
        return template.format(**kwargs)
    return template


def get_system_prompt() -> str:
    """获取 Agent 系统提示词"""
    return load_prompt("general_assistant")