"""
Chat History Routes
====================
API endpoints for managing chat history.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, ChatMessage, User
from datetime import datetime
import uuid

history_bp = Blueprint('history', __name__)


@history_bp.route('/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Get chat history for the current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        session_id = request.args.get('session_id')
        limit = request.args.get('limit', 50, type=int)
        
        # Build query
        query = ChatMessage.query.filter_by(user_id=current_user_id)
        
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        # Order by timestamp and limit
        messages = query.order_by(ChatMessage.timestamp.asc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in messages],
            'count': len(messages)
        }), 200
        
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/history', methods=['POST'])
@jwt_required()
def save_chat_message():
    """Save a chat message to history"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'message' not in data or 'sender' not in data:
            return jsonify({
                'success': False,
                'error': 'message and sender are required'
            }), 400
        
        # Create new message
        message = ChatMessage(
            user_id=current_user_id,
            message=data['message'],
            sender=data['sender'],
            model_used=data.get('model_used'),
            session_id=data.get('session_id'),
            timestamp=datetime.utcnow()
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': message.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving chat message: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/history/batch', methods=['POST'])
@jwt_required()
def save_chat_messages_batch():
    """Save multiple chat messages at once"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'messages' not in data:
            return jsonify({
                'success': False,
                'error': 'messages array is required'
            }), 400
        
        session_id = data.get('session_id', str(uuid.uuid4()))
        saved_messages = []
        
        for msg_data in data['messages']:
            message = ChatMessage(
                user_id=current_user_id,
                message=msg_data['message'],
                sender=msg_data['sender'],
                model_used=msg_data.get('model_used'),
                session_id=session_id,
                timestamp=datetime.fromisoformat(msg_data['timestamp']) if msg_data.get('timestamp') else datetime.utcnow()
            )
            db.session.add(message)
            saved_messages.append(message)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'messages': [msg.to_dict() for msg in saved_messages],
            'count': len(saved_messages)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving chat messages batch: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/history/sessions', methods=['GET'])
@jwt_required()
def get_chat_sessions():
    """Get list of chat sessions for the user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get unique session IDs with their first and last message timestamps
        sessions = db.session.query(
            ChatMessage.session_id,
            db.func.min(ChatMessage.timestamp).label('started_at'),
            db.func.max(ChatMessage.timestamp).label('last_message_at'),
            db.func.count(ChatMessage.id).label('message_count')
        ).filter(
            ChatMessage.user_id == current_user_id,
            ChatMessage.session_id.isnot(None)
        ).group_by(
            ChatMessage.session_id
        ).order_by(
            db.desc('last_message_at')
        ).all()
        
        return jsonify({
            'success': True,
            'sessions': [{
                'session_id': s.session_id,
                'started_at': s.started_at.isoformat() if s.started_at else None,
                'last_message_at': s.last_message_at.isoformat() if s.last_message_at else None,
                'message_count': s.message_count
            } for s in sessions]
        }), 200
        
    except Exception as e:
        print(f"Error getting chat sessions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/history/session/<session_id>', methods=['DELETE'])
@jwt_required()
def delete_chat_session(session_id):
    """Delete all messages in a session"""
    try:
        current_user_id = get_jwt_identity()
        
        deleted = ChatMessage.query.filter_by(
            user_id=current_user_id,
            session_id=session_id
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'deleted_count': deleted
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting chat session: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@history_bp.route('/history/clear', methods=['DELETE'])
@jwt_required()
def clear_chat_history():
    """Clear all chat history for the user"""
    try:
        current_user_id = get_jwt_identity()
        
        deleted = ChatMessage.query.filter_by(user_id=current_user_id).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'deleted_count': deleted
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing chat history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



