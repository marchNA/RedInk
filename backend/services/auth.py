"""
小红书账号认证服务

管理登录状态、扫码登录、凭证检查
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from backend.services.xiaohongshu import get_browser

logger = logging.getLogger(__name__)


class AuthService:
    """小红书认证服务"""

    def __init__(self):
        self.cookies_path = self._get_cookies_path()
        self.status_file = self._get_status_file()
        self._browser = None

    def _get_cookies_path(self) -> str:
        """获取 cookies 存储路径"""
        data_dir = Path(__file__).parent.parent.parent / 'data'
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / 'xiaohongshu_cookies.json')

    def _get_status_file(self) -> str:
        """获取状态文件路径"""
        data_dir = Path(__file__).parent.parent.parent / 'data'
        return str(data_dir / 'xiaohongshu_auth_status.json')

    def _get_storage_state_path(self) -> str:
        """获取 storage_state 存储路径"""
        data_dir = Path(__file__).parent.parent.parent / 'data'
        return str(data_dir / 'xiaohongshu_storage_state.json')

    def _save_status(self, status: Dict[str, Any]):
        """保存认证状态"""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态失败: {e}")

    def get_status(self) -> Dict[str, Any]:
        """
        获取当前登录状态
        
        Returns:
            {'logged_in': bool, 'user_info': dict, 'last_check': str}
        """
        if not os.path.exists(self.cookies_path):
            return {
                'logged_in': False,
                'user_info': None,
                'last_check': None
            }
        
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"读取状态失败: {e}")
        
        return {
            'logged_in': False,
            'user_info': None,
            'last_check': None
        }

    async def start_login(self) -> Dict[str, Any]:
        """
        开始扫码登录流程
        
        Returns:
            {'success': bool, 'message': str}
        """
        try:
            # 避免重复点击导致多次弹窗
            if self._browser and self._browser.page and not self._browser.page.is_closed():
                return {
                    'success': True,
                    'message': '登录窗口已打开，请在现有窗口中完成扫码'
                }

            self._browser = get_browser(self.cookies_path)
            # 登录流程强制使用全新会话，避免误恢复历史登录态
            await self._browser.start(restore_session=False)
            
            # 访问登录页面
            await self._browser.page.goto('https://creator.xiaohongshu.com/')
            await self._browser.page.wait_for_timeout(1000)
            
            # 查找登录按钮并点击
            login_button = await self._browser.page.query_selector('text="立即登录"')
            if login_button:
                await login_button.click()
                await self._browser.page.wait_for_timeout(2000)
            
            # 等待用户扫码
            logger.info("请在浏览器中扫码登录小红书")
            
            return {
                'success': True,
                'message': '请在弹出的浏览器窗口中扫码登录'
            }
            
        except Exception as e:
            logger.error(f"启动登录失败: {e}")
            return {
                'success': False,
                'message': f'启动登录失败: {e}'
            }

    async def check_login(self) -> Dict[str, Any]:
        """
        检查登录状态
        
        Returns:
            {'logged_in': bool, 'user_info': dict}
        """
        try:
            if not self._browser or not self._browser.page:
                return {
                    'logged_in': False,
                    'user_info': None,
                    'message': '浏览器未启动'
                }
            
            status = await self._browser.check_login_status(passive=True)
            
            if status.get('logged_in'):
                await self._browser.save_cookies()
                await self._browser.save_session_state()
                self._save_status({
                    'logged_in': True,
                    'user_info': status.get('user_info'),
                    'last_check': status.get('last_check')
                })
            
            return status
            
        except Exception as e:
            logger.error(f"检查登录失败: {e}")
            return {
                'logged_in': False,
                'user_info': None,
                'error': str(e)
            }

    async def complete_login(self, timeout: int = 120) -> Dict[str, Any]:
        """
        等待用户完成扫码登录
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            {'success': bool, 'user_info': dict, 'message': str}
        """
        try:
            if not self._browser:
                return {
                    'success': False,
                    'user_info': None,
                    'message': '浏览器未启动'
                }
            
            success = await self._browser.wait_for_qr_scan(timeout)
            
            if success:
                status = await self._browser.check_login_status(passive=True)
                return {
                    'success': True,
                    'user_info': status.get('user_info'),
                    'message': '登录成功'
                }
            else:
                return {
                    'success': False,
                    'user_info': None,
                    'message': '登录超时，请重试'
                }
                
        except Exception as e:
            logger.error(f"登录完成检查失败: {e}")
            return {
                'success': False,
                'user_info': None,
                'message': str(e)
            }

    async def logout(self) -> Dict[str, Any]:
        """
        退出登录
        
        Returns:
            {'success': bool, 'message': str}
        """
        try:
            # 先关闭浏览器，防止并发轮询再次回写登录状态
            if self._browser:
                await self._browser.close()
                self._browser = None

            if os.path.exists(self.cookies_path):
                os.remove(self.cookies_path)

            if os.path.exists(self.status_file):
                os.remove(self.status_file)

            storage_state_path = self._get_storage_state_path()
            if os.path.exists(storage_state_path):
                os.remove(storage_state_path)

            # 明确写入未登录状态，防止并发请求读取到旧值
            self._save_status({
                'logged_in': False,
                'user_info': None,
                'last_check': None
            })
            
            logger.info("已退出登录")
            return {
                'success': True,
                'message': '已退出登录'
            }
            
        except Exception as e:
            logger.error(f"退出登录失败: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    async def close(self):
        """关闭浏览器"""
        if self._browser:
            await self._browser.close()
            self._browser = None


def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    return AuthService()
