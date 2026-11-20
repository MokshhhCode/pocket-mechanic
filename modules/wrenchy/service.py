import os
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from config import Config
from database.connection import get_db_connection
from modules.sensor.manager import fetch_telemetry_for_motorcycle

try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False

class WrenchyAIService:
    """
    Conversational Motorcycle Diagnostic Assistant - Wrenchy AI.
    Integrates OpenAI backend API with structured vehicle context injection,
    and includes an offline expert diagnostic engine fallback.
    """

    @staticmethod
    def get_or_create_conversation(user_id: int, motorcycle_id: int,
                                  conversation_id: Optional[str] = None) -> str:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                if conversation_id:
                    cursor.execute(
                        """
                        SELECT conversation_id FROM chatbot_conversations
                        WHERE conversation_id = %s AND user_id = %s AND motorcycle_id = %s
                        """,
                        (conversation_id, user_id, motorcycle_id)
                    )
                    row = cursor.fetchone()
                    if row:
                        return row['conversation_id']

                # Create new conversation
                new_id = f"conv_{uuid.uuid4().hex[:12]}"
                cursor.execute(
                    """
                    INSERT INTO chatbot_conversations (conversation_id, user_id, motorcycle_id, title)
                    VALUES (%s, %s, %s, 'Motorcycle Health Consultation')
                    """,
                    (new_id, user_id, motorcycle_id)
                )
                return new_id
        finally:
            conn.close()

    @staticmethod
    def get_conversation_history(conversation_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT message_id, conversation_id, sender, message_text, payload_json, timestamp
                    FROM chatbot_messages
                    WHERE conversation_id = %s
                    ORDER BY message_id ASC
                    LIMIT %s
                    """,
                    (conversation_id, limit)
                )
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def build_vehicle_context(user_id: int, motorcycle_id: int) -> Dict[str, Any]:
        """Gathers only necessary context: motorcycle specs, latest telemetry, and open tickets."""
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # User info
                cursor.execute("SELECT full_name FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone() or {"full_name": "Rider"}

                # Motorcycle & specs
                cursor.execute(
                    """
                    SELECT m.*, mv.variant_name, mv.cooling_type, mv.brake_type, mv.final_drive_type,
                           mv.fuel_delivery_type, ms.*, mm.name as model_name, mfg.name as mfg_name
                    FROM motorcycles m
                    LEFT JOIN motorcycle_variants mv ON m.variant_id = mv.variant_id
                    LEFT JOIN motorcycle_specifications ms ON mv.variant_id = ms.variant_id
                    LEFT JOIN motorcycle_models mm ON mv.model_id = mm.model_id
                    LEFT JOIN manufacturers mfg ON mm.manufacturer_id = mfg.manufacturer_id
                    WHERE m.motorcycle_id = %s AND m.user_id = %s
                    """,
                    (motorcycle_id, user_id)
                )
                bike = cursor.fetchone() or {}

                # Active tickets
                cursor.execute(
                    """
                    SELECT ticket_id, issue_title, severity, status, description, recommended_action
                    FROM diagnostic_tickets
                    WHERE motorcycle_id = %s AND status NOT IN ('Resolved')
                    ORDER BY ticket_id DESC LIMIT 3
                    """,
                    (motorcycle_id,)
                )
                open_tickets = cursor.fetchall()
        finally:
            conn.close()

        # Telemetry
        telemetry = fetch_telemetry_for_motorcycle(motorcycle_id, persist=False)

        return {
            "user_name": user.get("full_name", "Rider"),
            "bike": bike,
            "open_tickets": open_tickets,
            "telemetry": telemetry.get("readings", {}),
            "anomalies": telemetry.get("anomalies", []),
            "telemetry_status": telemetry.get("status", "ONLINE")
        }

    @classmethod
    def generate_response(cls, user_id: int, motorcycle_id: int, conversation_id: str,
                          user_message: str) -> Dict[str, Any]:
        conv_id = cls.get_or_create_conversation(user_id, motorcycle_id, conversation_id)
        ctx = cls.build_vehicle_context(user_id, motorcycle_id)
        bike = ctx["bike"]

        # Persist user message
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chatbot_messages (conversation_id, sender, message_text)
                    VALUES (%s, 'USER', %s)
                    """,
                    (conv_id, user_message)
                )
        finally:
            conn.close()

        history = cls.get_conversation_history(conv_id, limit=10)

        # Attempt OpenAI API if key configured
        openai_key = os.getenv("OPENAI_API_KEY", "").strip() or Config.OPENAI_API_KEY.strip()
        assistant_reply = None
        suggested_action = None

        if openai_key and _openai_available:
            try:
                assistant_reply, suggested_action = cls._call_openai(user_message, history, ctx, openai_key)
            except Exception as e:
                # Log error and fall back gracefully to local expert engine
                print(f"[Wrenchy AI] OpenAI API exception: {e}. Activating local expert fallback.")
                assistant_reply = None

        if not assistant_reply:
            assistant_reply, suggested_action = cls._local_expert_engine(user_message, ctx)

        # Persist assistant reply
        payload = json.dumps({"suggested_action": suggested_action}) if suggested_action else None
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO chatbot_messages (conversation_id, sender, message_text, payload_json)
                    VALUES (%s, 'WRENCHY', %s, %s)
                    """,
                    (conv_id, assistant_reply, payload)
                )
                cursor.execute(
                    """
                    UPDATE chatbot_conversations
                    SET last_message_at = CURRENT_TIMESTAMP
                    WHERE conversation_id = %s
                    """,
                    (conv_id,)
                )
        finally:
            conn.close()

        return {
            "conversation_id": conv_id,
            "reply": assistant_reply,
            "suggested_action": suggested_action,
            "context_summary": {
                "bike_name": f"{bike.get('mfg_name', '')} {bike.get('model_name', 'Motorcycle')}".strip(),
                "telemetry_status": ctx.get("telemetry_status")
            }
        }

    @staticmethod
    def _call_openai(user_message: str, history: List[Dict[str, Any]], ctx: Dict[str, Any],
                     api_key: str):
        client = OpenAI(api_key=api_key)
        bike = ctx["bike"]
        readings = ctx["telemetry"]
        anomalies = ctx["anomalies"]
        tickets = ctx["open_tickets"]

        system_prompt = f"""
You are Wrenchy AI, an intelligent, professional motorcycle mechanic assistant inside the Pocket Mechanic application.
Your role is to help the rider understand symptoms, mechanical maintenance, technical specifications, and diagnostic findings for their motorcycle.

SELECTED MOTORCYCLE CONTEXT:
- Rider: {ctx['user_name']}
- Motorcycle: {bike.get('mfg_name', '')} {bike.get('model_name', 'Motorcycle')} ({bike.get('manufacturing_year', 2023)})
- Engine: {bike.get('displacement_cc', 350)} cc, {bike.get('cooling_type', 'Air')}-cooled, {bike.get('fuel_delivery_type', 'Fuel Injection')}
- Transmission: {bike.get('num_gears', 5)}-speed, {bike.get('final_drive_type', 'Chain')} drive
- Brakes: {bike.get('brake_type', 'Dual Disc')}, ABS: {bike.get('abs_type', 'Dual Channel')}
- Recommended Oil: {bike.get('oil_grade', '15W-50')}, Capacity: {bike.get('oil_capacity_l', 2.0)} L
- Recommended Tyres: Front {bike.get('front_tyre_psi', 29)} PSI, Rear {bike.get('rear_tyre_psi', 33)} PSI
- Recommended Chain Slack: {bike.get('chain_slack_mm', '25-30 mm')}
- Service Interval: Every {bike.get('service_interval_km', 5000)} km

LIVE TELEMETRY READINGS:
{json.dumps(readings, indent=2)}
Flagged Anomalies: {anomalies if anomalies else "None - Nominal"}

ACTIVE DIAGNOSTIC TICKETS:
{json.dumps(tickets, default=str) if tickets else "No open tickets"}

BEHAVIOURAL & SAFETY RULES:
1. Always tailor advice specifically to the verified specs of this {bike.get('model_name', 'motorcycle')}. Never give generic advice when model specs apply (e.g., if air-cooled, do not mention coolant; if belt/shaft drive, do not mention chain lube).
2. Distinguish clearly between confirmed sensor faults, suspected wear, and user-reported symptoms.
3. NEVER claim to have physically inspected a component.
4. If the issue involves brakes, tyres, steering, or engine overheating, include a clear safety caution and recommend physical inspection.
5. Offer to launch a formal diagnostic session or create a ticket if an issue is suspected.
6. Tone: Friendly, knowledgeable, authoritative yet approachable. Keep answers concise, actionable, and formatted in clean markdown.
"""

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-8:]:
            role = "user" if msg["sender"] == "USER" else "assistant"
            messages.append({"role": role, "content": msg["message_text"]})

        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )
        reply = response.choices[0].message.content

        suggested_action = None
        lower_msg = user_message.lower()
        if any(w in lower_msg for w in ["diagnose", "diagnostics", "check", "brake", "oil", "noise", "heat", "battery"]):
            suggested_action = {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Start Diagnostics for this Issue"}

        return reply, suggested_action

    @staticmethod
    def _local_expert_engine(user_message: str, ctx: Dict[str, Any]):
        """Intelligent offline motorcycle expert diagnostic system."""
        bike = ctx["bike"]
        readings = ctx["telemetry"]
        mfg = bike.get("mfg_name", "your motorcycle")
        model = bike.get("model_name", "bike")
        cooling = bike.get("cooling_type", "Air")
        drive = bike.get("final_drive_type", "Chain")
        oil = bike.get("oil_grade", "15W-50 API SL")
        front_psi = bike.get("front_tyre_psi", 29)
        rear_psi = bike.get("rear_tyre_psi", 33)
        chain_slack = bike.get("chain_slack_mm", "25-30 mm")
        brakes = bike.get("brake_type", "Dual Disc")

        msg = user_message.lower()

        # Engine overheating / thermal
        if any(k in msg for k in ["overheat", "hot", "temperature", "temp", "smoke", "coolant", "radiator"]):
            temp_val = readings.get("ENG_TEMP", 85.0)
            if "Liquid" in cooling:
                reply = (
                    f"### 🌡️ Thermal Diagnostics for {mfg} {model}\n\n"
                    f"Your {model} features a **liquid-cooled** powertrain. Current simulated cylinder temperature is **{temp_val} °C**.\n\n"
                    f"- **Recommended Spec:** Standard operating range is between 80 °C and 100 °C.\n"
                    f"- **Inspection Points:** Check the coolant expansion reservoir level (50:50 ethylene glycol mix) and verify the radiator radiator electric fan kicks on at ~98 °C.\n"
                    f"- **Safety Notice:** Never open the radiator cap while the engine is hot."
                )
            else:
                reply = (
                    f"### 🌡️ Engine Temperature Analysis for {mfg} {model}\n\n"
                    f"Your {model} is **{cooling}-cooled**. Current simulated head temperature is **{temp_val} °C**.\n\n"
                    f"- **Characteristics:** Air-cooled engines rely heavily on forward airflow and engine oil circulation for thermal dissipation.\n"
                    f"- **Oil Specification:** Verified oil grade is **{oil}** (capacity: {bike.get('oil_capacity_l', 2.0)} L).\n"
                    f"- **Recommended Check:** Ensure cylinder head cooling fins are clean and verify engine oil is topped up to the upper sight glass mark."
                )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Run Thermal Diagnosis"}

        # Brake issues
        elif any(k in msg for k in ["brake", "stopping", "squeak", "squeal", "spongy", "pad", "shoe"]):
            pad_val = readings.get("BRAKE_PAD_WEAR", 4.5)
            reply = (
                f"### 🛑 Braking System Assessment for {mfg} {model}\n\n"
                f"Your bike is configured with **{brakes}** with **{bike.get('abs_type', 'ABS')}**.\n\n"
                f"- **Current Friction Thickness:** **{pad_val} mm** (OEM service replacement limit: **2.0 mm**).\n"
                f"- **Fluid Specification:** Hydraulic circuit requires **{bike.get('brake_fluid_type', 'DOT 4')}** renewed every {bike.get('brake_fluid_interval_km', 10000)} km.\n"
                f"- **Diagnosis:** If experiencing squealing or reduced lever bite, inspect pads for glazed friction material or contaminated brake rotors.\n\n"
                f"> ⚠️ **Safety Caution:** Brakes are a critical safety system. If lever feels spongy or pads are below 2.0 mm, arrange immediate replacement."
            )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Diagnose Braking System"}

        # Battery / electrical / starting
        elif any(k in msg for k in ["battery", "start", "starting", "crank", "voltage", "volt", "electric"]):
            volt_val = readings.get("BAT_VOLT", 14.1)
            reply = (
                f"### ⚡ Electrical & Battery Health for {mfg} {model}\n\n"
                f"Your bike uses a **{bike.get('battery_voltage', 12.0)}V {bike.get('battery_capacity_ah', 8.0)}Ah {bike.get('battery_type', 'Maintenance-Free')}** battery.\n\n"
                f"- **Live System Voltage:** **{volt_val} V**.\n"
                f"- **Nominal Standards:** Resting key-off voltage should be >12.6 V; running charging voltage should stabilize between 13.8 V and 14.5 V.\n"
                f"- **Troubleshooting:** Voltage below 12.0 V indicates insufficient alternator stator charge or aged battery plates."
            )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Diagnose Electrical System"}

        # Chain / Drivetrain
        elif any(k in msg for k in ["chain", "slack", "belt", "shaft", "drive", "sprocket"]):
            if drive == "Chain":
                slack_val = readings.get("CHAIN_SLACK", 27.0)
                reply = (
                    f"### ⛓️ Drivetrain Slack & Lubrication for {mfg} {model}\n\n"
                    f"Your motorcycle is equipped with a **Chain Final Drive**.\n\n"
                    f"- **Verified Chain Slack Spec:** **{chain_slack}**.\n"
                    f"- **Current Simulated Slack:** **{slack_val} mm**.\n"
                    f"- **Maintenance Action:** Clean with dedicated chain cleaner (no harsh solvents) and apply O-ring compatible chain lube every 500-800 km."
                )
            elif drive == "Belt":
                reply = (
                    f"### ⚙️ Drive Belt Inspection for {mfg} {model}\n\n"
                    f"Your {model} is equipped with a **Carbon Belt Drive**.\n\n"
                    f"- **Key Advantage:** Belts do **not** require oil, grease, or chain lubrication.\n"
                    f"- **Inspection:** Inspect belt teeth for cracking, stone imbedding, or edge fraying."
                )
            else:
                reply = (
                    f"### ⚙️ Shaft Final Drive for {mfg} {model}\n\n"
                    f"Your {model} features an enclosed **Shaft Drive & Bevel Gearbox**.\n\n"
                    f"- **Maintenance:** No chain slack adjustment or chain lube is required.\n"
                    f"- **Inspection:** Inspect final drive housing for oil seal weeping and renew hypoid gear oil as per schedule."
                )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Diagnose Drivetrain"}

        # Tyre pressure
        elif any(k in msg for k in ["tyre", "tire", "pressure", "psi", "puncture"]):
            reply = (
                f"### 🏍️ Tyre Pressure Specifications for {mfg} {model}\n\n"
                f"Verified cold tyre pressures for your {model}:\n\n"
                f"- **Front Tyre:** **{front_psi} PSI** (Size: {bike.get('front_tyre_size', 'Standard')})\n"
                f"- **Rear Tyre:** **{rear_psi} PSI** (Size: {bike.get('rear_tyre_size', 'Standard')})\n"
                f"- **Tyre Type:** {bike.get('tyre_type', 'Tubeless')}\n\n"
                f"Always measure pressures when tyres are cold (before riding) for accurate readings."
            )
            return reply, None

        # General greeting / fallback
        else:
            reply = (
                f"Hello {ctx['user_name']}! I'm **Wrenchy**, your personal mechanic for the **{mfg} {model}**.\n\n"
                f"I have full access to your motorcycle's verified factory specifications, current telemetry, and maintenance records.\n\n"
                f"You can ask me about:\n"
                f"- Unusual mechanical symptoms, noises, or vibrations\n"
                f"- Engine oil, coolant, and brake fluid specifications\n"
                f"- Tyre pressures and chain slack limits\n"
                f"- Live telemetry assessment or diagnostic ticket history\n\n"
                f"What would you like me to inspect today?"
            )
            return reply, None
