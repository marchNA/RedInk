"""
小红书浏览器自动化模块

负责浏览器实例管理、登录、cookies 持久化
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class XiaohongshuBrowser:
    """小红书浏览器管理器"""

    def __init__(self, cookies_path: Optional[str] = None):
        """
        初始化浏览器管理器
        
        Args:
            cookies_path: cookies 存储文件路径
        """
        self.cookies_path = cookies_path or self._get_default_cookies_path()
        self.storage_state_path = self._get_default_storage_state_path()
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def _get_default_cookies_path(self) -> str:
        """获取默认 cookies 存储路径"""
        data_dir = Path(__file__).parent.parent.parent / 'data'
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / 'xiaohongshu_cookies.json')

    def _get_default_storage_state_path(self) -> str:
        """获取默认 storage_state 存储路径（包含 cookies + localStorage）"""
        data_dir = Path(__file__).parent.parent.parent / 'data'
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / 'xiaohongshu_storage_state.json')

    async def start(self, restore_session: bool = True):
        """启动浏览器"""
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self._launch_browser_with_fallback()
            # 使用桌面端 UA，避免被识别为移动端导致“网页发布不支持”
            context_options = {
                'viewport': {'width': 1366, 'height': 900},
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            }
            # 优先加载完整会话状态（cookies + localStorage）
            if restore_session and os.path.exists(self.storage_state_path):
                context_options['storage_state'] = self.storage_state_path
                logger.info("检测到 storage_state，尝试恢复完整登录会话")
            self.context = await self.browser.new_context(**context_options)
            if restore_session:
                await self._load_cookies()
            self.page = await self.context.new_page()
            logger.info("浏览器启动成功")
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            raise

    async def _launch_browser_with_fallback(self):
        """
        启动浏览器（优先 Chrome，回退 Edge，最后使用 Playwright 自带 Chromium）
        """
        launch_args = {
            'headless': False,
            'args': ['--disable-blink-features=AutomationControlled']
        }

        # 1) 优先 Google Chrome
        try:
            browser = await self.playwright.chromium.launch(
                channel='chrome',
                **launch_args
            )
            logger.info("使用 Chrome 启动浏览器")
            return browser
        except Exception as e:
            logger.warning(f"Chrome 启动失败，尝试 Edge: {e}")

        # 2) 回退 Microsoft Edge
        try:
            browser = await self.playwright.chromium.launch(
                channel='msedge',
                **launch_args
            )
            logger.info("使用 Edge 启动浏览器")
            return browser
        except Exception as e:
            logger.warning(f"Edge 启动失败，尝试内置 Chromium: {e}")

        # 3) 最终回退 Playwright 内置 Chromium
        browser = await self.playwright.chromium.launch(**launch_args)
        logger.info("使用 Playwright 内置 Chromium 启动浏览器")
        return browser

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("浏览器已关闭")

    async def _load_cookies(self):
        """加载 cookies"""
        if os.path.exists(self.cookies_path):
            try:
                with open(self.cookies_path, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                await self.context.add_cookies(cookies)
                logger.info("Cookies 加载成功")
            except Exception as e:
                logger.warning(f"Cookies 加载失败: {e}")

    async def save_cookies(self):
        """保存 cookies"""
        try:
            cookies = await self.context.cookies()
            with open(self.cookies_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            logger.info("Cookies 保存成功")
        except Exception as e:
            logger.error(f"Cookies 保存失败: {e}")

    async def save_session_state(self):
        """保存完整会话状态（cookies + localStorage）"""
        try:
            await self.context.storage_state(path=self.storage_state_path)
            logger.info("Storage State 保存成功")
        except Exception as e:
            logger.error(f"Storage State 保存失败: {e}")

    async def check_login_status(self, passive: bool = False) -> Dict[str, Any]:
        """
        检查登录状态
        
        Returns:
            {'logged_in': bool, 'user_info': dict}
        """
        try:
            if not self.context:
                return {'logged_in': False, 'user_info': None, 'error': '浏览器上下文未初始化'}

            if not self.page or self.page.is_closed():
                self.page = await self.context.new_page()

            # passive=True 时不主动跳转，避免扫码页被轮询强制刷新
            if not passive:
                await self.page.goto(
                    'https://creator.xiaohongshu.com/',
                    timeout=15000,
                    wait_until='domcontentloaded'
                )
                await self.page.wait_for_timeout(2000)
            else:
                try:
                    await self.page.wait_for_load_state('domcontentloaded', timeout=2000)
                except Exception:
                    pass

            # 1) URL 明确指向登录页：未登录
            current_url = (self.page.url or '').lower()
            if 'login' in current_url:
                return {'logged_in': False, 'user_info': None}

            # 2) 页面出现登录关键词：未登录（避免误判）
            page_text = await self.page.evaluate("document.body ? document.body.innerText : ''")
            login_keywords = ['立即登录', '扫码登录', '手机号登录', '验证码登录', '登录后']
            if any(k in page_text for k in login_keywords):
                return {'logged_in': False, 'user_info': None}

            # 3) 检测登录后的用户区域（正向信号）
            user_info = await self.page.evaluate('''
                () => {
                    const candidates = [
                        document.querySelector('[class*="user-name"]'),
                        document.querySelector('[class*="nickname"]'),
                        document.querySelector('[class*="avatar"]'),
                        document.querySelector('[class*="user"]')
                    ].filter(Boolean)
                    for (const el of candidates) {
                        const txt = (el.textContent || '').trim()
                        if (txt) return { name: txt }
                    }
                    return { name: '小红书用户' }
                }
            ''')

            # 仅在通过负向检查后，才认定登录成功
            await self.save_cookies()
            await self.save_session_state()
            return {'logged_in': True, 'user_info': user_info}
        except Exception as e:
            # 轮询期间禁止自动创建额外页面，避免不断弹出新登录界面
            logger.warning(f"检查登录状态失败: {e}")
            return {'logged_in': False, 'user_info': None, 'error': str(e)}

    async def wait_for_qr_scan(self, timeout: int = 120) -> bool:
        """
        等待用户扫码登录
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            是否登录成功
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = await self.check_login_status(passive=True)
            if status.get('logged_in'):
                await self.save_cookies()
                await self.save_session_state()
                return True
            await self.page.wait_for_timeout(2000)
        
        logger.warning("扫码登录超时")
        return False


def get_browser(cookies_path: Optional[str] = None) -> XiaohongshuBrowser:
    """获取浏览器实例"""
    return XiaohongshuBrowser(cookies_path)
