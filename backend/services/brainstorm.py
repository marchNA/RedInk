"""
创意风暴服务

提供两类能力：
1. 多轮对话推进：帮助用户澄清选题和表达方向
2. 一键成稿：基于对话生成主题、图文大纲和文案（标题/正文/标签）
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

import yaml

from backend.services.content import get_content_service
from backend.services.outline import get_outline_service
from backend.utils.text_client import get_text_chat_client

logger = logging.getLogger(__name__)


class BrainstormService:
    """创意风暴服务"""

    def __init__(self):
        self.text_config = self._load_text_config()
        self.client = self._get_client()

    def _load_text_config(self) -> dict:
        config_path = Path(__file__).parent.parent.parent / "text_providers.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {
            "active_provider": "google_gemini",
            "providers": {
                "google_gemini": {
                    "type": "google_gemini",
                    "model": "gemini-2.0-flash-exp",
                    "temperature": 0.9,
                    "max_output_tokens": 4000,
                }
            },
        }

    def _get_client(self):
        active_provider = self.text_config.get("active_provider", "google_gemini")
        providers = self.text_config.get("providers", {})
        provider_config = providers.get(active_provider, {})
        if not provider_config.get("api_key"):
            raise ValueError("文本服务商未配置 API Key")
        return get_text_chat_client(provider_config)

    def _model_settings(self) -> Dict[str, Any]:
        active_provider = self.text_config.get("active_provider", "google_gemini")
        providers = self.text_config.get("providers", {})
        provider_config = providers.get(active_provider, {})
        return {
            "model": provider_config.get("model", "gemini-2.0-flash-exp"),
            "temperature": provider_config.get("temperature", 0.9),
            "max_output_tokens": provider_config.get("max_output_tokens", 4000),
        }

    def _parse_json(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        md_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
        if md_match:
            try:
                return json.loads(md_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return json.loads(text[start_idx : end_idx + 1])
        raise ValueError("无法解析 JSON 响应")

    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        lines = []
        for msg in messages:
            role = "用户" if msg.get("role") == "user" else "助手"
            content = (msg.get("content") or "").strip()
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def chat(self, messages: List[Dict[str, str]], user_input: str) -> Dict[str, Any]:
        history_text = self._format_messages(messages)
        prompt = f"""你是一个小红书创作教练。你要通过对话帮助用户把模糊想法变成可发布的内容方向。

对话历史：
{history_text if history_text else "（无）"}

用户刚刚说：
{user_input}

请给出：
1) 简洁、有推进性的回复（120字内）
2) 2-3 个下一步可选方向（短句）

严格输出 JSON：
{{
  "assistant_reply": "你的回复",
  "next_options": ["选项1", "选项2", "选项3"]
}}
"""

        settings = self._model_settings()
        raw = self.client.generate_text(prompt=prompt, **settings)
        data = self._parse_json(raw)

        reply = (data.get("assistant_reply") or "").strip()
        options = data.get("next_options") or []
        if not isinstance(options, list):
            options = []

        return {
            "success": True,
            "assistant_reply": reply or "我先帮你聚焦目标用户和场景，再继续细化。",
            "next_options": [str(x) for x in options][:3],
        }

    def compose(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        history_text = self._format_messages(messages)
        if not history_text.strip():
            return {"success": False, "error": "对话为空，请先聊几句再生成。"}

        # 先把聊天整理成可执行的创作简报
        brief_prompt = f"""你是内容策划，请把下面对话整理成创作简报。

对话：
{history_text}

生成约束：
- 最终用于发布的标题必须在20字以内
- 最终用于发布的正文必须在1000字以内

严格输出 JSON：
{{
  "topic": "20字以内主题",
  "brief": "可直接用于生成小红书图文的完整需求说明，包含目标人群、场景、语气、结构偏好、禁忌点"
}}
"""

        settings = self._model_settings()
        brief_raw = self.client.generate_text(prompt=brief_prompt, **settings)
        brief_data = self._parse_json(brief_raw)

        topic = (brief_data.get("topic") or "").strip() or "创意风暴笔记"
        brief = (brief_data.get("brief") or "").strip() or history_text

        outline_service = get_outline_service()
        outline_result = outline_service.generate_outline(
            brief,
            images=None,
            input_mode="free_text",
        )
        if not outline_result.get("success"):
            return outline_result

        content_service = get_content_service()
        content_result = content_service.generate_content(topic, outline_result.get("outline", ""))
        if not content_result.get("success"):
            return content_result

        return {
            "success": True,
            "topic": topic,
            "brief": brief,
            "outline": outline_result.get("outline", ""),
            "pages": outline_result.get("pages", []),
            "content": {
                "titles": content_result.get("titles", []),
                "copywriting": content_result.get("copywriting", ""),
                "tags": content_result.get("tags", []),
            },
        }


def get_brainstorm_service() -> BrainstormService:
    return BrainstormService()
