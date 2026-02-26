"""
内容调优服务

对已生成的小红书内容进行标题和正文优化
"""

import json
import logging
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

from backend.utils.text_client import get_text_chat_client
from backend.utils.title_utils import truncate_title

logger = logging.getLogger(__name__)


class RefineService:
    """内容调优服务"""

    # 标题优化提示词
    TITLE_PROMPT = """你是一个小红书内容优化专家。请根据以下规则优化标题：

1. 标题要吸引眼球，激发好奇心
2. 使用数字、emoji 符号增加吸引力
3. 控制在20字以内，突出关键词
4. 符合小红书风格

原文标题：{original_title}

请直接输出优化后的标题，不要其他内容。
"""

    # 正文优化提示词
    CONTENT_PROMPT = """你是一个小红书内容优化专家。请根据以下规则优化正文：

1. 语言口语化，符合小红书风格
2. 分段落，使用 emoji 装饰
3. 重点内容加粗或使用符号强调
4. 开头要抓住注意力
5. 结尾要有互动引导（提问或呼吁）

原文正文：
{original_content}

请直接输出优化后的正文，不要其他内容。
"""

    # 批量优化提示词
    BATCH_PROMPT = """你是一个小红书内容优化专家。请同时优化标题和正文：

原始标题：{original_title}
原始正文：
{original_content}

要求：
1. 标题：20字以内，吸引眼球，使用emoji
2. 正文：口语化，分段落，加emoji，结尾有互动引导
3. 标签：提供5-8个合适的标签

请以JSON格式输出：
{{
    "optimized_title": "优化后的标题",
    "optimized_content": "优化后的正文",
    "tags": ["标签1", "标签2", "标签3"]
}}
"""

    def __init__(self):
        self.text_config = self._load_text_config()
        self.client = self._get_client()

    def _load_text_config(self) -> dict:
        """加载文本生成配置"""
        config_path = Path(__file__).parent.parent.parent / 'text_providers.yaml'

        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
                return config
            except yaml.YAMLError as e:
                logger.error(f"文本配置 YAML 解析失败: {e}")

        return {
            'active_provider': 'google_gemini',
            'providers': {
                'google_gemini': {
                    'type': 'google_gemini',
                    'model': 'gemini-2.0-flash-exp',
                    'temperature': 1.0,
                    'max_output_tokens': 8000
                }
            }
        }

    def _get_client(self):
        """获取文本生成客户端"""
        active_provider = self.text_config.get('active_provider', 'google_gemini')
        providers = self.text_config.get('providers', {})
        
        if active_provider not in providers:
            raise ValueError(f"文本服务商 [{active_provider}] 不存在")
        
        provider_config = providers.get(active_provider, {})
        
        if not provider_config.get('api_key'):
            raise ValueError(f"文本服务商 [{active_provider}] 未配置 API Key")
        
        return get_text_chat_client(provider_config)

    def _get_model_params(self) -> Dict[str, Any]:
        """获取模型参数"""
        active_provider = self.text_config.get('active_provider', 'google_gemini')
        providers = self.text_config.get('providers', {})
        provider_config = providers.get(active_provider, {})
        
        return {
            'model': provider_config.get('model', 'gemini-2.0-flash-exp'),
            'temperature': provider_config.get('temperature', 1.0),
            'max_output_tokens': provider_config.get('max_output_tokens', 4000)
        }

    def refine_title(self, original_title: str) -> Dict[str, Any]:
        """
        优化标题
        
        Args:
            original_title: 原始标题
            
        Returns:
            {'success': bool, 'optimized_title': str, 'error': str}
        """
        try:
            params = self._get_model_params()
            prompt = self.TITLE_PROMPT.format(original_title=original_title)
            
            response = self.client.generate_text(
                prompt=prompt,
                **params
            )
            
            optimized_title = response.strip()
            optimized_title = truncate_title(optimized_title)
            
            logger.info(f"标题优化完成: {original_title} -> {optimized_title}")
            
            return {
                'success': True,
                'optimized_title': optimized_title
            }
            
        except Exception as e:
            logger.error(f"标题优化失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def refine_content(self, original_content: str) -> Dict[str, Any]:
        """
        优化正文
        
        Args:
            original_content: 原始正文
            
        Returns:
            {'success': bool, 'optimized_content': str, 'error': str}
        """
        try:
            params = self._get_model_params()
            prompt = self.CONTENT_PROMPT.format(original_content=original_content)
            
            response = self.client.generate_text(
                prompt=prompt,
                **params
            )
            
            optimized_content = response.strip()
            
            logger.info(f"正文优化完成，长度: {len(original_content)} -> {len(optimized_content)}")
            
            return {
                'success': True,
                'optimized_content': optimized_content
            }
            
        except Exception as e:
            logger.error(f"正文优化失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def refine_all(
        self,
        original_title: str,
        original_content: str
    ) -> Dict[str, Any]:
        """
        批量优化标题和正文
        
        Args:
            original_title: 原始标题
            original_content: 原始正文
            
        Returns:
            {'success': bool, 'optimized_title': str, 'optimized_content': str, 'tags': list, 'error': str}
        """
        try:
            params = self._get_model_params()
            prompt = self.BATCH_PROMPT.format(
                original_title=original_title,
                original_content=original_content
            )
            
            response = self.client.generate_text(
                prompt=prompt,
                **params
            )
            
            # 尝试解析 JSON
            result = self._parse_json_response(response)
            
            logger.info(f"内容优化完成")
            
            return {
                'success': True,
                'optimized_title': truncate_title(result.get('optimized_title', original_title)),
                'optimized_content': result.get('optimized_content', original_content),
                'tags': result.get('tags', [])
            }
            
        except Exception as e:
            logger.error(f"内容优化失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """解析 JSON 响应"""
        import re
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # 尝试从 markdown 代码块中提取
        json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', response_text)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # 尝试找到 JSON 对象
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            try:
                return json.loads(response_text[start_idx:end_idx + 1])
            except json.JSONDecodeError:
                pass
        
        logger.warning(f"无法解析 JSON，返回原始文本")
        return {'optimized_title': '', 'optimized_content': response_text, 'tags': []}


def get_refine_service() -> RefineService:
    """获取调优服务实例"""
    return RefineService()
