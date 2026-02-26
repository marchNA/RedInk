"""
小红书内容发布模块

负责发布笔记到小红书
"""

import asyncio
import logging
import os
import re
import traceback
from urllib.parse import urlparse
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class XiaohongshuPublisher:
    """小红书内容发布器"""

    def __init__(self, cookies_path: Optional[str] = None):
        """
        初始化发布器
        
        Args:
            cookies_path: cookies 存储文件路径
        """
        from .browser import XiaohongshuBrowser
        self.browser = XiaohongshuBrowser(cookies_path)
        self.page = None
        self.project_root = Path(__file__).resolve().parents[3]

    async def initialize(self):
        """初始化浏览器和页面"""
        await self.browser.start()
        self.page = self.browser.page
        logger.info(f"发布器初始化完成 (project_root={self.project_root})")

    async def close(self):
        """关闭浏览器"""
        await self.browser.close()

    async def publish(
        self,
        title: str,
        content: str,
        image_paths: List[str],
        tags: Optional[List[str]] = None,
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发布笔记
        
        Args:
            title: 标题
            content: 正文内容
            image_paths: 图片路径列表
            tags: 标签列表
            
        Returns:
            {'success': bool, 'note_id': str, 'url': str, 'error': str}
        """
        trace = f"[publish:{trace_id}]" if trace_id else "[publish:-]"
        try:
            title_to_fill = (title or "").strip()[:20]
            content_to_fill = (content or "").strip()[:1000]
            if len((title or "").strip()) > 20:
                logger.warning(f"{trace} 标题超过20字，已截断为20字")
            if len((content or "").strip()) > 1000:
                logger.warning(f"{trace} 正文超过1000字，已截断为1000字")

            logger.info(
                f"{trace} 发布流程开始 "
                f"(title_len={len(title_to_fill)}, content_len={len(content_to_fill)}, "
                f"images={len(image_paths)}, tags={len(tags or [])})"
            )
            logger.debug(f"{trace} 原始图片路径: {image_paths}")

            # 检查登录状态
            status = await self.browser.check_login_status(passive=True)
            logger.info(f"{trace} 登录状态检查结果: logged_in={status.get('logged_in')}")
            if not status.get('logged_in'):
                return {
                    'success': False,
                    'error': '未登录，请先扫码登录'
                }

            # 访问创作者中心发布页面（使用更稳健的导航策略）
            nav_ok = await self._goto_publish_page(trace=trace)
            if not nav_ok:
                return {
                    'success': False,
                    'error': '打开小红书发布页超时，请检查网络或稍后重试'
                }

            # 上传图片
            uploaded = await self._upload_images(image_paths, trace=trace)
            if not uploaded:
                return {
                    'success': False,
                    'error': '未找到可用的图片上传控件，请检查小红书页面结构是否变更'
                }
            editor_ready = await self._wait_publish_editor_ready(trace=trace, timeout_ms=20000)
            if not editor_ready:
                return {
                    'success': False,
                    'error': '图片上传后未等到标题/正文编辑区，请检查页面加载状态'
                }

            # 填写标题
            filled_title = await self._fill_title(title_to_fill, trace=trace)
            if not filled_title:
                return {
                    'success': False,
                    'error': '未找到标题输入框，发布中止（避免空内容误发布）'
                }
            await self.page.wait_for_timeout(1000)

            # 填写正文
            filled_content = await self._fill_content(content_to_fill, trace=trace)
            if not filled_content:
                return {
                    'success': False,
                    'error': '未找到正文输入区域，发布中止（避免空内容误发布）'
                }
            await self.page.wait_for_timeout(1000)

            # 标签改为手动填写：不再自动注入，避免干扰人工编辑
            logger.info(f"{trace} 跳过自动标签填写（由用户手动填写）")

            # 点击发布按钮
            success = await self._click_publish(trace=trace)
            if not success:
                return {
                    'success': False,
                    'error': '发布失败，请手动检查'
                }

            # 获取笔记链接
            note_info = await self._get_note_info(trace=trace)
            if note_info.get('note_id') == 'unknown':
                return {
                    'success': False,
                    'error': f"无法确认发布成功，当前页面: {note_info.get('url', '')}"
                }
            
            logger.info(f"{trace} 发布成功: {note_info}")
            return {
                'success': True,
                **note_info
            }

        except Exception as e:
            logger.error(f"{trace} 发布失败: {e}")
            logger.debug(f"{trace} 发布异常堆栈:\n{traceback.format_exc()}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _goto_publish_page(self, trace: str = "[publish:-]") -> bool:
        """打开发布页：先进入发布主页面，再切换到图文发布页面。"""
        # 按实际行为分两段导航，避免直接进 target=image 时页面结构不完整
        bootstrap_url = "https://creator.xiaohongshu.com/publish/publish?from=tab_switch"
        image_target_url = "https://creator.xiaohongshu.com/publish/publish?from=tab_switch&target=image"
        fallback_url = "https://creator.xiaohongshu.com/publish/publish"

        attempts = [
            {"wait_until": "domcontentloaded", "timeout": 20000},
            {"wait_until": "domcontentloaded", "timeout": 30000},
            {"wait_until": "commit", "timeout": 20000},
        ]

        # Step 1: 先打开基础发布页
        bootstrap_ok = False
        for idx, cfg in enumerate(attempts, start=1):
            try:
                logger.info(
                    f"{trace} 尝试打开发布主页面 "
                    f"(url={bootstrap_url}, attempt={idx}, wait_until={cfg['wait_until']}, timeout={cfg['timeout']})"
                )
                await self.page.goto(bootstrap_url, wait_until=cfg["wait_until"], timeout=cfg["timeout"])
                await self.page.wait_for_timeout(1800)
                logger.info(
                    f"{trace} 发布主页面导航成功 "
                    f"(url={bootstrap_url}, attempt={idx}, page_url={self.page.url})"
                )
                bootstrap_ok = True
                break
            except Exception as e:
                logger.warning(f"{trace} 发布主页面导航失败（attempt={idx}）: {e}")
                await self.page.wait_for_timeout(1000)

        if not bootstrap_ok:
            # 最后回退一次通用地址，尽量保住流程
            try:
                logger.warning(f"{trace} 发布主页面多次失败，尝试回退地址: {fallback_url}")
                await self.page.goto(fallback_url, wait_until="domcontentloaded", timeout=20000)
                await self.page.wait_for_timeout(1200)
                bootstrap_ok = True
                logger.info(f"{trace} 回退地址打开成功 (page_url={self.page.url})")
            except Exception as e:
                logger.warning(f"{trace} 回退地址打开失败: {e}")
                return False

        # Step 2: 切换到图文发布页（target=image）
        for idx, cfg in enumerate(attempts, start=1):
            try:
                logger.info(
                    f"{trace} 尝试切换图文发布页 "
                    f"(url={image_target_url}, attempt={idx}, wait_until={cfg['wait_until']}, timeout={cfg['timeout']})"
                )
                await self.page.goto(image_target_url, wait_until=cfg["wait_until"], timeout=cfg["timeout"])
                await self.page.wait_for_timeout(1500)
                logger.info(
                    f"{trace} 图文发布页导航成功 "
                    f"(url={image_target_url}, attempt={idx}, page_url={self.page.url})"
                )
                return True
            except Exception as e:
                logger.warning(f"{trace} 图文发布页导航失败（attempt={idx}）: {e}")
                await self.page.wait_for_timeout(1000)

        return False

    async def _upload_images(self, image_paths: List[str], trace: str = "[publish:-]") -> bool:
        """上传图片（兼容不同页面结构）"""
        path_checks = []
        abs_paths = []
        for p in image_paths:
            resolved, tried = self._resolve_image_path(p)
            path_checks.append({
                'raw': p,
                'resolved': str(resolved) if resolved else '',
                'exists': bool(resolved and resolved.exists()),
                'tried': tried
            })
            if resolved and resolved.exists():
                abs_paths.append(str(resolved))

        # 去重，避免同一路径重复上传
        abs_paths = list(dict.fromkeys(abs_paths))

        logger.info(f"{trace} 图片路径检查: total={len(path_checks)}, valid={len(abs_paths)}")
        logger.debug(f"{trace} 图片路径明细: {path_checks}")

        if not abs_paths:
            logger.warning(f"{trace} 图片文件不存在或路径无效")
            return False

        # 1) 先尝试点击可能的上传入口，促使页面渲染 file input
        click_selectors = [
            'text=上传图片',
            'text=添加图片',
            'text=上传',
            'text=选择图片',
            'button:has-text("上传")',
            '[class*="upload"]',
            '[class*="Upload"]',
            '[data-testid*="upload"]'
        ]
        for selector in click_selectors:
            try:
                el = await self.page.query_selector(selector)
                if el:
                    await el.click(timeout=1000)
                    await self.page.wait_for_timeout(300)
                    logger.info(f"{trace} 上传入口点击成功: selector={selector}")
                    break
                logger.debug(f"{trace} 上传入口未命中: selector={selector}")
            except Exception:
                logger.debug(f"{trace} 上传入口点击异常: selector={selector}", exc_info=True)
                continue

        # 2) 在 page + 所有 frame 中查找 file input
        all_frames = [self.page.main_frame] + self.page.frames
        input_selectors = [
            'input[type="file"]',
            'input[accept*="image"]',
            '[class*="upload"] input[type="file"]',
            '[class*="Upload"] input[type="file"]'
        ]

        for frame in all_frames:
            frame_url = frame.url or ""
            for selector in input_selectors:
                try:
                    handles = await frame.query_selector_all(selector)
                    logger.debug(
                        f"{trace} 上传控件扫描: frame={frame_url}, selector={selector}, count={len(handles)}"
                    )
                except Exception:
                    logger.debug(
                        f"{trace} 上传控件扫描异常: frame={frame_url}, selector={selector}",
                        exc_info=True
                    )
                    continue

                for file_input in handles:
                    try:
                        await file_input.set_input_files(abs_paths)
                        logger.info(
                            f"{trace} 已选择 {len(abs_paths)} 张图片 "
                            f"(frame={frame_url}, selector={selector})"
                        )
                        return True
                    except Exception:
                        logger.debug(
                            f"{trace} set_input_files 失败: frame={frame_url}, selector={selector}",
                            exc_info=True
                        )
                        continue

        await self._debug_upload_controls(trace=trace)
        logger.warning(f"{trace} 未找到可用的图片上传控件，请检查小红书页面结构是否变更")
        return False

    async def _wait_publish_editor_ready(self, trace: str = "[publish:-]", timeout_ms: int = 20000) -> bool:
        """上传图片后等待编辑区渲染完成。"""
        # 上传完成后给页面一个基础渲染窗口，避免立刻探测误判
        await self.page.wait_for_timeout(1200)

        selectors = [
            'textarea[placeholder="填写标题会有更多赞哦"]',
            'input[placeholder="填写标题会有更多赞哦"]',
            '[data-placeholder="输入正文描述，真诚有价值的分享予人温暖"]',
            'div[data-placeholder*="输入正文描述"]',
            'textarea[placeholder*="标题"]',
            'input[placeholder*="标题"]',
            'div[contenteditable="true"]',
        ]

        deadline = asyncio.get_event_loop().time() + (timeout_ms / 1000.0)
        attempt = 0
        while asyncio.get_event_loop().time() < deadline:
            attempt += 1
            for selector in selectors:
                try:
                    node = await self.page.query_selector(selector)
                    if node:
                        logger.info(
                            f"{trace} 编辑区已就绪 (selector={selector}, attempt={attempt})"
                        )
                        return True
                except Exception:
                    logger.debug(
                        f"{trace} 编辑区探测异常 (selector={selector}, attempt={attempt})",
                        exc_info=True
                    )
            await self.page.wait_for_timeout(500)

        logger.warning(f"{trace} 等待编辑区超时: {timeout_ms}ms")
        return False

    def _resolve_image_path(self, raw_path: str) -> tuple[Optional[Path], List[str]]:
        """将前端传来的图片路径解析为项目内绝对路径。"""
        if not raw_path:
            return None, []

        value = str(raw_path).strip()
        parsed = urlparse(value)
        candidate_str = parsed.path if parsed.scheme in ("http", "https") else value
        candidate_str = candidate_str.replace("\\", "/")

        candidates: List[Path] = []

        # 绝对路径直查
        p = Path(candidate_str)
        if p.is_absolute():
            candidates.append(p)

        # 常见前端路径：/api/images/task_x/1.png -> output/task_x/1.png
        if candidate_str.startswith("/api/images/"):
            rel = candidate_str[len("/api/images/"):]
            candidates.append(self.project_root / "output" / rel)
        elif candidate_str.startswith("api/images/"):
            rel = candidate_str[len("api/images/"):]
            candidates.append(self.project_root / "output" / rel)

        # 常见前端路径：/output/task_x/1.png 或 output/task_x/1.png
        if candidate_str.startswith("/output/"):
            candidates.append(self.project_root / candidate_str.lstrip("/"))
            # 历史记录图片实际存储在 history 目录，兼容 /output 前缀
            candidates.append(self.project_root / "history" / candidate_str[len("/output/"):])
        elif candidate_str.startswith("output/"):
            candidates.append(self.project_root / candidate_str)
            candidates.append(self.project_root / "history" / candidate_str[len("output/"):])

        # 其他相对路径：优先项目根目录，再尝试当前工作目录
        if not p.is_absolute():
            normalized_rel = candidate_str.lstrip("/")
            candidates.append(self.project_root / normalized_rel)
            candidates.append(Path.cwd() / normalized_rel)

        tried_candidates: List[str] = []
        dedup: List[Path] = []
        seen = set()
        for c in candidates:
            key = str(c)
            if key in seen:
                continue
            seen.add(key)
            dedup.append(c)

        for candidate in dedup:
            try:
                resolved = candidate.resolve(strict=False)
            except Exception:
                resolved = candidate
            tried_candidates.append(str(resolved))
            if resolved.exists():
                return resolved, tried_candidates

        return None, tried_candidates

    async def _debug_upload_controls(self, trace: str = "[publish:-]"):
        """调试输出：记录当前页面可见的上传相关控件，便于快速适配"""
        try:
            logger.info(f"{trace} 开始采集上传控件调试信息...")
            frames = [self.page.main_frame] + self.page.frames
            for idx, frame in enumerate(frames):
                frame_url = frame.url or ''
                try:
                    file_inputs = await frame.query_selector_all('input[type="file"]')
                except Exception:
                    file_inputs = []
                logger.info(f"{trace} [debug] frame#{idx} url={frame_url} file_inputs={len(file_inputs)}")

                # 上传相关文本按钮
                text_snippet = await frame.evaluate("""
                    () => {
                        const keywords = ['上传', '添加图片', '选择图片', '图文', '发布'];
                        const nodes = Array.from(document.querySelectorAll('button,div,span,a,label'));
                        const hits = [];
                        for (const n of nodes) {
                            const t = (n.textContent || '').trim();
                            if (!t) continue;
                            if (keywords.some(k => t.includes(k))) {
                                hits.push({
                                    text: t.slice(0, 40),
                                    tag: n.tagName,
                                    cls: (n.className || '').toString().slice(0, 120)
                                });
                            }
                            if (hits.length >= 20) break;
                        }
                        return hits;
                    }
                """)
                if text_snippet:
                    logger.info(f"{trace} [debug] frame#{idx} keyword_nodes={text_snippet}")
        except Exception as e:
            logger.warning(f"{trace} 上传控件调试采集失败: {e}")

    async def _fill_title(self, title: str, trace: str = "[publish:-]") -> bool:
        """填写标题"""
        # 尝试多种选择器
        title_selectors = [
            'textarea[placeholder="填写标题会有更多赞哦"]',
            'input[placeholder="填写标题会有更多赞哦"]',
            'textarea[placeholder*="标题"]',
            'input[placeholder*="标题"]',
            'input[class*="title"]',
            'textarea[class*="title"]',
            '[contenteditable="true"][class*="title"]',
            'div[placeholder*="标题"]'
        ]
        
        for selector in title_selectors:
            title_input = await self.page.query_selector(selector)
            if title_input:
                try:
                    await title_input.fill(title)
                except Exception:
                    logger.debug(f"{trace} 标题 fill 失败，改用键盘输入 (selector={selector})", exc_info=True)
                    await title_input.click()
                    await self.page.keyboard.press('Control+A')
                    await self.page.keyboard.type(title)
                logger.info(f"{trace} 标题已填写 (selector={selector}, len={len(title)})")
                return True
            logger.debug(f"{trace} 标题输入框未命中: selector={selector}")
        
        logger.warning(f"{trace} 未找到标题输入框")
        return False

    async def _fill_content(self, content: str, trace: str = "[publish:-]") -> bool:
        """填写正文"""
        content_selectors = [
            '[data-placeholder="输入正文描述，真诚有价值的分享予人温暖"]',
            'div[data-placeholder*="输入正文描述"]',
            'div[contenteditable="true"]',
            'textarea[placeholder*="正文"]',
            '[class*="content"] [contenteditable="true"]',
            '[class*="editor"]'
        ]
        
        for selector in content_selectors:
            content_input = await self.page.query_selector(selector)
            if content_input:
                try:
                    # contenteditable 节点通常不支持 fill，优先键盘输入
                    is_editable = await content_input.get_attribute('contenteditable')
                    if is_editable == 'true':
                        raise RuntimeError("contenteditable_use_keyboard")
                    await content_input.fill(content)
                except Exception:
                    logger.debug(f"{trace} 正文 fill 失败，改用键盘输入 (selector={selector})", exc_info=True)
                    await content_input.click()
                    await self.page.keyboard.press('Control+A')
                    await self.page.keyboard.type(content)
                logger.info(f"{trace} 正文已填写 (selector={selector}, len={len(content)})")
                return True
            logger.debug(f"{trace} 正文输入区域未命中: selector={selector}")
        
        logger.warning(f"{trace} 未找到正文输入框")
        return False

    async def _add_tags(self, tags: List[str], trace: str = "[publish:-]"):
        """添加标签"""
        logger.info(f"{trace} 开始添加标签: count={len(tags)}")
        # 兼容新版“小红书创作平台”标签弹窗入口
        open_tag_selectors = [
            'button:has-text("添加话题")',
            'button:has-text("添加标签")',
            'button:has-text("新建标签")',
            'text=新建标签',
            '.d-modal-header:has-text("新建标签")',
            '[class*="d-modal-header"]:has-text("新建标签")'
        ]
        for selector in open_tag_selectors:
            try:
                hit = await self.page.query_selector(selector)
                if hit:
                    await hit.click(timeout=1000)
                    await self.page.wait_for_timeout(300)
                    logger.info(f"{trace} 标签入口点击成功: selector={selector}")
                    break
            except Exception:
                logger.debug(f"{trace} 标签入口点击异常: selector={selector}", exc_info=True)

        tag_input_selectors = [
            'input[placeholder*="添加标签"]',
            'input[placeholder*="话题"]',
            'input[placeholder*="搜索"]',
            'input[class*="tag"]',
        ]

        # 小红书标签格式：#标签名
        for tag in tags:
            if not tag or not str(tag).strip():
                logger.debug(f"{trace} 跳过空标签: {tag}")
                continue
            tag_text = f"#{tag}"
            added = False

            # 先尝试“标签输入框 + 回车确认”
            for selector in tag_input_selectors:
                try:
                    tag_input = await self.page.query_selector(selector)
                    if not tag_input:
                        continue
                    await tag_input.click()
                    try:
                        await tag_input.fill(tag)
                    except Exception:
                        await self.page.keyboard.press('Control+A')
                        await self.page.keyboard.type(tag)
                    await self.page.keyboard.press('Enter')
                    await self.page.wait_for_timeout(250)
                    logger.info(f"{trace} 已添加标签(输入框): {tag} (selector={selector})")
                    added = True
                    break
                except Exception:
                    logger.debug(
                        f"{trace} 标签输入失败: tag={tag}, selector={selector}",
                        exc_info=True
                    )

            if added:
                continue

            # 回退到正文末尾追加
            content_area = await self.page.query_selector('div[contenteditable="true"]')
            if content_area:
                await content_area.click()
                await self.page.keyboard.press('End')
                await content_area.press('Enter')
                await content_area.type(tag_text)
                logger.info(f"{trace} 已添加标签(正文追加): {tag}")
                continue

            logger.warning(f"{trace} 未找到标签输入控件或正文区域，标签添加中止")
            return

    async def _click_publish(self, trace: str = "[publish:-]") -> bool:
        """点击发布按钮"""
        publish_selectors = [
            'button:has-text("发布")',
            'button[class*="publish"]',
            'div:has-text("发布")'
        ]
        
        for selector in publish_selectors:
            publish_btn = await self.page.query_selector(selector)
            if publish_btn:
                await publish_btn.click()
                await self.page.wait_for_timeout(3000)
                logger.info(f"{trace} 已点击发布按钮 (selector={selector})")
                return True
            logger.debug(f"{trace} 发布按钮未命中: selector={selector}")
        
        logger.warning(f"{trace} 未找到发布按钮")
        return False

    async def _get_note_info(self, trace: str = "[publish:-]") -> Dict[str, Any]:
        """获取发布的笔记信息"""
        try:
            # 等待页面跳转或出现成功提示
            await self.page.wait_for_timeout(2000)
            
            # 获取当前 URL
            current_url = self.page.url
            
            # 尝试提取笔记 ID
            note_id = None
            if 'note/' in current_url or 'explore/' in current_url:
                match = re.search(r'note/([a-zA-Z0-9]+)', current_url)
                if match:
                    note_id = match.group(1)
                else:
                    match = re.search(r'explore/([a-zA-Z0-9]+)', current_url)
                    if match:
                        note_id = match.group(1)
            
            # 构建笔记链接
            note_url = f"https://www.xiaohongshu.com/explore/{note_id}" if note_id else current_url
            logger.info(f"{trace} 发布后页面信息: current_url={current_url}, note_id={note_id or 'unknown'}")
            
            return {
                'note_id': note_id or 'unknown',
                'url': note_url
            }
        except Exception as e:
            logger.error(f"{trace} 获取笔记信息失败: {e}")
            return {
                'note_id': 'unknown',
                'url': ''
            }


def get_publisher(cookies_path: Optional[str] = None) -> XiaohongshuPublisher:
    """获取发布器实例"""
    return XiaohongshuPublisher(cookies_path)
