"""
创意风暴相关 API 路由
"""

import logging
from flask import Blueprint, jsonify, request

from backend.services.brainstorm import get_brainstorm_service

logger = logging.getLogger(__name__)


def create_brainstorm_blueprint():
    brainstorm_bp = Blueprint("brainstorm", __name__)

    @brainstorm_bp.route("/brainstorm/chat", methods=["POST"])
    def brainstorm_chat():
        try:
            data = request.get_json() or {}
            messages = data.get("messages") or []
            user_input = (data.get("user_input") or "").strip()
            if not user_input:
                return jsonify({"success": False, "error": "user_input 不能为空"}), 400

            service = get_brainstorm_service()
            result = service.chat(messages, user_input)
            return jsonify(result), 200
        except Exception as e:
            logger.exception("brainstorm chat error")
            return jsonify({"success": False, "error": str(e)}), 500

    @brainstorm_bp.route("/brainstorm/compose", methods=["POST"])
    def brainstorm_compose():
        try:
            data = request.get_json() or {}
            messages = data.get("messages") or []
            if not messages:
                return jsonify({"success": False, "error": "messages 不能为空"}), 400

            service = get_brainstorm_service()
            result = service.compose(messages)
            status = 200 if result.get("success") else 500
            return jsonify(result), status
        except Exception as e:
            logger.exception("brainstorm compose error")
            return jsonify({"success": False, "error": str(e)}), 500

    return brainstorm_bp

