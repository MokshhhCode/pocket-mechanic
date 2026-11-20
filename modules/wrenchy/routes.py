from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from database.connection import get_db_connection
from modules.wrenchy.service import WrenchyAIService

wrenchy_bp = Blueprint('wrenchy', __name__)

@wrenchy_bp.route('/wrenchy')
@login_required
def index():
    bike_id = session.get('active_motorcycle_id')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT m.motorcycle_id, mm.name as model_name, mfg.name as mfg_name
                FROM motorcycles m
                LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                LEFT JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                LEFT JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                WHERE m.user_id = %s AND m.is_active = TRUE
                """,
                (current_user.id,)
            )
            bikes = cursor.fetchall()
            if not bike_id and bikes:
                bike_id = bikes[0]['motorcycle_id']
                session['active_motorcycle_id'] = bike_id

            current_bike = next((b for b in bikes if b['motorcycle_id'] == bike_id), None)

            # Get conversations
            cursor.execute(
                """
                SELECT conversation_id, title, last_message_at
                FROM chatbot_conversations
                WHERE user_id = %s AND motorcycle_id = %s
                ORDER BY last_message_at DESC
                """,
                (current_user.id, bike_id)
            )
            conversations = cursor.fetchall()
    finally:
        conn.close()

    conv_id = request.args.get('conv_id')
    if not conv_id and conversations:
        conv_id = conversations[0]['conversation_id']
    elif not conv_id:
        conv_id = WrenchyAIService.get_or_create_conversation(current_user.id, bike_id)

    history = WrenchyAIService.get_conversation_history(conv_id)

    return render_template(
        'wrenchy/chat.html',
        bikes=bikes,
        current_bike=current_bike,
        conversations=conversations,
        active_conv_id=conv_id,
        history=history
    )

@wrenchy_bp.route('/api/wrenchy/chat', methods=['POST'])
@login_required
def chat():
    data = request.json or {}
    user_message = data.get('message', '').strip()
    bike_id = int(data.get('motorcycle_id') or session.get('active_motorcycle_id') or 1)
    conv_id = data.get('conversation_id')

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    response = WrenchyAIService.generate_response(
        user_id=current_user.id,
        motorcycle_id=bike_id,
        conversation_id=conv_id,
        user_message=user_message
    )
    return jsonify(response)

@wrenchy_bp.route('/api/wrenchy/history/<conversation_id>', methods=['GET'])
@login_required
def get_history(conversation_id):
    history = WrenchyAIService.get_conversation_history(conversation_id)
    return jsonify(history)
