"""
小红书相关 API 路由

包括：
- 登录状态检查
- 扫码登录
- 发布笔记
- 内容调优
"""

import asyncio
import logging
import threading
import uuid
from flask import Blueprint, jsonify, request
from backend.utils.title_utils import truncate_title

logger = logging.getLogger(__name__)


_async_loop = None
_async_loop_thread = None
_async_loop_lock = threading.Lock()


def _ensure_async_loop():
    """确保存在一个长期运行的事件循环，避免每次请求 asyncio.run 破坏 Playwright 状态"""
    global _async_loop, _async_loop_thread
    with _async_loop_lock:
        if _async_loop and _async_loop.is_running():
            return _async_loop

        _async_loop = asyncio.new_event_loop()

        def _run_loop():
            asyncio.set_event_loop(_async_loop)
            _async_loop.run_forever()

        _async_loop_thread = threading.Thread(target=_run_loop, daemon=True, name='xhs-async-loop')
        _async_loop_thread.start()
        return _async_loop


def _run_async(coro):
    """在线程安全的长期事件循环中执行协程并返回结果"""
    loop = _ensure_async_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


def create_xiaohongshu_blueprint():
    """创建小红书 API 蓝图"""
    xiaohongshu_bp = Blueprint('xiaohongshu', __name__)
    
    # 存储服务实例
    auth_service = None
    refine_service = None
    
    @xiaohongshu_bp.route('/auth/status', methods=['GET'])
    def get_auth_status():
        """获取登录状态"""
        nonlocal auth_service
        if auth_service is None:
            from backend.services.auth import get_auth_service
            auth_service = get_auth_service()
        
        status = auth_service.get_status()
        return jsonify(status)
    
    @xiaohongshu_bp.route('/auth/login', methods=['POST'])
    def start_login():
        """开始扫码登录"""
        nonlocal auth_service
        if auth_service is None:
            from backend.services.auth import get_auth_service
            auth_service = get_auth_service()
        
        # 启动登录（异步）
        result = _run_async(auth_service.start_login())
        return jsonify(result)
    
    @xiaohongshu_bp.route('/auth/login/check', methods=['GET'])
    def check_login():
        """检查登录状态"""
        nonlocal auth_service
        if auth_service is None:
            return jsonify({
                'logged_in': False,
                'message': '未启动登录流程'
            })
        
        result = _run_async(auth_service.check_login())
        return jsonify(result)
    
    @xiaohongshu_bp.route('/auth/login/complete', methods=['POST'])
    def complete_login():
        """等待登录完成"""
        nonlocal auth_service
        if auth_service is None:
            return jsonify({
                'success': False,
                'message': '未启动登录流程'
            })
        
        timeout = request.json.get('timeout', 120) if request.json else 120
        result = _run_async(auth_service.complete_login(timeout))
        
        # 登录完成后关闭浏览器
        if result.get('success'):
            _run_async(auth_service.close())
        
        return jsonify(result)
    
    @xiaohongshu_bp.route('/auth/logout', methods=['POST'])
    def logout():
        """退出登录"""
        nonlocal auth_service
        if auth_service is None:
            from backend.services.auth import get_auth_service
            auth_service = get_auth_service()
        
        result = _run_async(auth_service.logout())
        return jsonify(result)
    
    @xiaohongshu_bp.route('/publish', methods=['POST'])
    def publish_note():
        """发布笔记"""
        data = request.json or {}
        publish_id = data.get('publish_id') or str(uuid.uuid4())[:8]
        
        title = truncate_title(data.get('title', ''))
        content = data.get('content', '')
        image_paths = data.get('image_paths', [])
        tags = data.get('tags', [])

        logger.info(
            f"[publish:{publish_id}] 收到发布请求 "
            f"(title_len={len(title)}, content_len={len(content)}, "
            f"images={len(image_paths)}, tags={len(tags)})"
        )
        logger.debug(f"[publish:{publish_id}] image_paths={image_paths}")
        logger.debug(f"[publish:{publish_id}] tags={tags}")
        
        if not title:
            logger.warning(f"[publish:{publish_id}] 标题为空，拒绝发布")
            return jsonify({
                'success': False,
                'error': '标题不能为空'
            })
        
        if not image_paths:
            logger.warning(f"[publish:{publish_id}] 图片列表为空，拒绝发布")
            return jsonify({
                'success': False,
                'error': '请选择至少一张图片'
            })
        
        from backend.services.xiaohongshu import get_publisher
        publisher = get_publisher()
        
        async def do_publish():
            logger.info(f"[publish:{publish_id}] 开始初始化发布器")
            await publisher.initialize()
            result = await publisher.publish(title, content, image_paths, tags, trace_id=publish_id)
            # 调试友好：发布失败时保留浏览器现场，便于人工排查
            if result.get('success'):
                logger.info(f"[publish:{publish_id}] 发布成功，关闭浏览器")
                await publisher.close()
            else:
                logger.warning(f"[publish:{publish_id}] 发布失败，保留浏览器窗口用于排查")
            return result
        
        result = _run_async(do_publish())
        logger.info(f"[publish:{publish_id}] 发布请求结束 success={result.get('success')}")
        return jsonify(result)
    
    @xiaohongshu_bp.route('/refine/title', methods=['POST'])
    def refine_title():
        """优化标题"""
        data = request.json or {}
        original_title = data.get('title', '')
        
        if not original_title:
            return jsonify({
                'success': False,
                'error': '标题不能为空'
            })
        
        nonlocal refine_service
        if refine_service is None:
            from backend.services.refine import get_refine_service
            refine_service = get_refine_service()
        
        result = refine_service.refine_title(original_title)
        return jsonify(result)
    
    @xiaohongshu_bp.route('/refine/content', methods=['POST'])
    def refine_content():
        """优化正文"""
        data = request.json or {}
        original_content = data.get('content', '')
        
        if not original_content:
            return jsonify({
                'success': False,
                'error': '正文不能为空'
            })
        
        nonlocal refine_service
        if refine_service is None:
            from backend.services.refine import get_refine_service
            refine_service = get_refine_service()
        
        result = refine_service.refine_content(original_content)
        return jsonify(result)
    
    @xiaohongshu_bp.route('/refine/all', methods=['POST'])
    def refine_all():
        """批量优化标题和正文"""
        data = request.json or {}
        original_title = data.get('title', '')
        original_content = data.get('content', '')
        
        if not original_title and not original_content:
            return jsonify({
                'success': False,
                'error': '标题和正文不能同时为空'
            })
        
        nonlocal refine_service
        if refine_service is None:
            from backend.services.refine import get_refine_service
            refine_service = get_refine_service()
        
        result = refine_service.refine_all(original_title, original_content)
        return jsonify(result)
    
    return xiaohongshu_bp
