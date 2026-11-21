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

        # Persist user message and update conversation title dynamically
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
                topic_title = user_message.strip()[:40] + ('...' if len(user_message.strip()) > 40 else '')
                cursor.execute(
                    """
                    UPDATE chatbot_conversations
                    SET title = CASE
                        WHEN title = 'Motorcycle Health Consultation' OR title IS NULL THEN %s
                        ELSE title
                    END,
                    last_message_at = CURRENT_TIMESTAMP
                    WHERE conversation_id = %s
                    """,
                    (topic_title, conv_id)
                )
        finally:
            conn.close()

        history = cls.get_conversation_history(conv_id, limit=10)

        # Check for Gemini or OpenAI API keys (env, config, or user settings in MySQL)
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        openai_key = os.getenv("OPENAI_API_KEY", "").strip() or Config.OPENAI_API_KEY.strip()

        if not gemini_key or not openai_key:
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT setting_key, setting_value FROM application_settings WHERE setting_key IN ('GEMINI_API_KEY', 'OPENAI_API_KEY') AND (user_id = %s OR user_id IS NULL) ORDER BY (user_id IS NOT NULL) ASC",
                        (user_id,)
                    )
                    rows = cursor.fetchall()
                    for r in rows:
                        val = (r['setting_value'] or '').strip()
                        if r['setting_key'] == 'GEMINI_API_KEY' and val and not gemini_key:
                            gemini_key = val
                        elif r['setting_key'] == 'OPENAI_API_KEY' and val and not openai_key:
                            openai_key = val
            except Exception:
                pass
            finally:
                conn.close()

        # Check if testing mode is active to preserve instant offline test runs
        from flask import current_app
        is_testing = False
        try:
            is_testing = current_app and current_app.config.get('TESTING')
        except Exception:
            pass

        assistant_reply = None
        suggested_action = None

        # 1. Attempt Gemini API if configured
        if gemini_key and not assistant_reply and not is_testing:
            try:
                assistant_reply, suggested_action = cls._call_gemini(user_message, history, ctx, gemini_key)
            except Exception as e:
                print(f"[Wrenchy AI] Gemini API call exception: {e}. Trying next provider...")
                assistant_reply = None

        # 2. Attempt OpenAI API if configured
        if openai_key and _openai_available and not assistant_reply and not is_testing:
            try:
                assistant_reply, suggested_action = cls._call_openai(user_message, history, ctx, openai_key)
            except Exception as e:
                print(f"[Wrenchy AI] OpenAI API exception: {e}. Activating local expert engine.")
                assistant_reply = None

        # 3. Comprehensive Local Expert Engine (Offline & Intelligent)
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

    @classmethod
    def _build_system_prompt(cls, ctx: Dict[str, Any]) -> str:
        bike = ctx.get("bike", {})
        mfg = bike.get("mfg_name") or bike.get("custom_make") or "Royal Enfield"
        model = bike.get("model_name") or bike.get("custom_model") or "Classic 350"
        user_name = ctx.get("user_name", "Rider")
        oil = bike.get("oil_grade", "15W-50")
        front_psi = bike.get("front_tyre_psi", 29)
        rear_psi = bike.get("rear_tyre_psi", 33)
        drive = bike.get("final_drive_type", "Chain")
        cooling = bike.get("cooling_type", "Air")
        disp_cc = bike.get("displacement_cc", 350)
        readings = ctx.get("telemetry", {})

        return (
            f"You are Wrenchy, the charismatic, deeply knowledgeable, and friendly AI motorcycle mechanic companion inside Pocket Mechanic. "
            f"You speak like an actual human friend and master mechanic—warm, engaging, and practical with relatable garage analogies. "
            f"Rider Name: {user_name}. "
            f"Active Motorcycle: {mfg} {model} ({disp_cc}cc, {cooling}-cooled, {drive} final drive, {oil} oil, {front_psi}/{rear_psi} PSI tyres). "
            f"Live Telemetry: Battery {readings.get('BAT_VOLT', 14.1)}V, Engine Temp {readings.get('ENG_TEMP', 85.0)}°C, Chain Slack {readings.get('CHAIN_SLACK', 27.0)}mm. "
            f"Answer questions on motorcycle modifications (belt drive conversions, exhausts, tyres, lights), mechanical engineering, road trip touring, riding technique, and maintenance with genuine motorcycle expertise. "
            f"Keep answers clear, well-structured in markdown, conversational, and direct."
        )

    @classmethod
    def _detect_suggested_action(cls, user_message: str) -> Optional[Dict[str, str]]:
        lower = user_message.lower()
        if any(w in lower for w in ["diagnose", "diagnostics", "check", "brake", "oil", "noise", "heat", "battery", "fault", "ticket"]):
            return {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Start Diagnostics for this Issue"}
        return None

    @classmethod
    def _call_gemini(cls, user_message: str, history: List[Dict[str, Any]], ctx: Dict[str, Any], api_key: str):
        import requests

        system_text = cls._build_system_prompt(ctx)

        contents = []
        for msg in history[-8:]:
            role = "user" if msg["sender"] == "USER" else "model"
            contents.append({"role": role, "parts": [{"text": msg["message_text"]}]})
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        payload = {
            "system_instruction": {
                "parts": [{"text": system_text}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000
            }
        }

        # Try active models in order of response speed & stability
        for model in ["gemini-3.1-flash-lite", "gemini-3.5-flash"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                resp = requests.post(url, json=payload, timeout=15)
                if resp.status_code == 200:
                    res_data = resp.json()
                    candidates = res_data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and parts[0].get("text"):
                            return parts[0]["text"], cls._detect_suggested_action(user_message)
            except Exception as e:
                print(f"[Wrenchy AI] Model {model} request error: {e}. Trying fallback...")
                continue

        raise RuntimeError("No available Gemini model returned a valid response")

    @classmethod
    def _call_openai(cls, user_message: str, history: List[Dict[str, Any]], ctx: Dict[str, Any], api_key: str):
        client = OpenAI(api_key=api_key)
        system_prompt = cls._build_system_prompt(ctx)

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-8:]:
            role = "user" if msg["sender"] == "USER" else "assistant"
            messages.append({"role": role, "content": msg["message_text"]})

        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        reply = response.choices[0].message.content
        return reply, cls._detect_suggested_action(user_message)

    @staticmethod
    def _local_expert_engine(user_message: str, ctx: Dict[str, Any]):
        """
        Intelligent offline conversational motorcycle expert system.
        Speaks in a warm, personable, human voice with comprehensive domain
        knowledge across riding, mechanics, road trips, maintenance, and diagnostics.
        """
        bike = ctx["bike"]
        readings = ctx["telemetry"]
        user_name = ctx.get("user_name", "Rider")
        first_name = user_name.split()[0] if user_name else "Rider"
        mfg = bike.get("mfg_name", "your motorcycle")
        model = bike.get("model_name", "motorcycle")
        cooling = bike.get("cooling_type", "Air")
        drive = bike.get("final_drive_type", "Chain")
        oil = bike.get("oil_grade", "15W-50 API SL")
        front_psi = bike.get("front_tyre_psi", 29)
        rear_psi = bike.get("rear_tyre_psi", 33)
        chain_slack = bike.get("chain_slack_mm", "25-30 mm")
        brakes = bike.get("brake_type", "Dual Disc")
        abs_type = bike.get("abs_type", "Dual Channel ABS")
        disp_cc = bike.get("displacement_cc", 350)

        msg = user_message.lower().strip()

        # ---------------------------------------------------------------------
        # 1. Warm Greetings & Casual Banter
        # ---------------------------------------------------------------------
        if any(msg == g or msg.startswith(f"{g} ") or msg.endswith(f" {g}") for g in [
            "hi", "hello", "hey", "howdy", "sup", "what's up", "good morning", "good evening", "good afternoon", "yo"
        ]):
            reply = (
                f"Hey {first_name}! Great to see you. How’s the **{mfg} {model}** treating you lately?\n\n"
                f"I'm here for whatever you need today — whether you want to chat about weekend road trips, "
                f"troubleshoot an odd noise or vibration, talk riding technique, or check your maintenance schedule. "
                f"What's on your mind?"
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 2. Identity, Persona & Capabilities
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["who are you", "what are you", "what can you do", "introduce yourself", "tell me about yourself", "how are you"]):
            reply = (
                f"I'm **Wrenchy** — think of me as your personal mechanic friend and riding companion living right inside Pocket Mechanic!\n\n"
                f"I grew up around motor oil, carburettor cleaner, and track days. Unlike a boring service manual, I speak human: "
                f"I love breaking down tricky mechanical concepts into everyday analogies, helping you plan road trips, "
                f"evaluating custom modifications, and keeping your **{mfg} {model}** running smooth and safe.\n\n"
                f"Here's what we can dive into anytime:\n"
                f"- **Modifications & Upgrades:** Belt drive conversions, exhaust slip-ons, wider tyres, aux lights, and remaps.\n"
                f"- **Mechanical Diagnostics:** Strange engine clicks, brake squeals, spongy clutch, or battery voltage drops.\n"
                f"- **Touring & Road Trips:** Packing essentials, tyre pressure adjustments for luggage, and toolkits.\n"
                f"- **Riding Dynamics:** Countersteering physics, cornering posture, and emergency braking.\n"
                f"- **OEM Factory Specs:** Verified tyre pressures ({front_psi}/{rear_psi} PSI), engine oil ({oil}), and chain slack ({chain_slack}).\n\n"
                f"Got a question or something you'd like to inspect?"
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 3. MODIFICATIONS: Belt Drive Conversion / Installation
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["belt drive", "belt conversion", "install belt", "convert to belt", "change to belt", "chain to belt", "belt system", "belt kit"]) or ("belt" in msg and any(k in msg for k in ["install", "convert", "possible", "can i", "kit", "upgrade", "mod", "fit", "put", "switch"])):
            reply = (
                f"### ⚙️ Belt Drive Conversion for {mfg} {model}\n\n"
                f"**Yes, you absolutely can!** There are reputable aftermarket belt-drive conversion kits manufactured specifically for the **{mfg} {model}** (both for Royal Enfield UCE and modern J-series platforms, as well as several other modern classics).\n\n"
                f"Here is the honest mechanic's breakdown of what you need to know before making the switch:\n\n"
                f"#### 🌟 The Big Advantages (Why Riders Love It):\n"
                f"1. **Whisper-Quiet & Silky Smooth:** Say goodbye to chain clatter, metal-on-metal backlash, and jerky on/off throttle transitions. Power delivery to the rear wheel becomes velvety smooth.\n"
                f"2. **Zero Mess & Minimal Upkeep:** No sticky chain lube flinging onto your clean chrome, rear rim, or spokes. No cleaning greasy muck every 500 km — just wash road dust off with plain water.\n"
                f"3. **Long Lifespan:** A high-grade carbon-fiber or Kevlar reinforced belt (like Gates Poly Chain or Continental) can easily last **40,000 to 50,000 km**, significantly outlasting a standard steel chain.\n\n"
                f"#### ⚠️ The Catches & Practical Considerations:\n"
                f"1. **Vulnerability to Stones & Gravel:** If a sharp pebble gets trapped between the rear pulley and the belt, it can pierce or snap the teeth. It's fantastic for paved highways and city commutes, but risky for rocky off-roading, river crossings, or rugged trails.\n"
                f"2. **Laser-Straight Alignment Required:** The swingarm and rear axle alignment must be 100% true. A misaligned belt will track to the pulley flange and shred its edge within a few thousand kilometres.\n"
                f"3. **Cost Factor:** A quality conversion kit (hard-anodized billet aluminum pulleys + Kevlar belt) costs considerably more than an OEM brass O-ring chain and sprocket set.\n"
                f"4. **Gear Ratio:** Ensure the kit preserves your stock primary ratio (matching your factory gearing) so your low-end acceleration and top-end cruising RPM aren't compromised.\n\n"
                f"**Wrenchy's Verdict:** If your {model} is primarily your daily commuter or a highway weekend cruiser and you hate messy chain maintenance, it's one of the best refinement mods you can do. But if you take it on gravel trails or remote expeditions where finding a replacement belt is impossible, stick with the trusty roller chain!"
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 4. MODIFICATIONS: Exhaust, Silencer & Slip-On Upgrades
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["exhaust", "slip on", "slip-on", "free flow", "decat", "baffle", "db killer", "loud exhaust", "silencer"]) and any(k in msg for k in ["install", "can i", "put", "change", "upgrade", "fit", "loud", "legal", "mod", "sound"]):
            reply = (
                f"### 💨 Aftermarket Exhaust & Silencer Guide for {mfg} {model}\n\n"
                f"Upgrading the exhaust on your **{model}** is one of the most tempting mods, but here is what happens mechanically:\n\n"
                f"- **Slip-on vs Full System:** A slip-on replaces only the rear muffler, preserving the catalytic converter and oxygen sensor. A full system or decat pipe removes the cat, saving weight but drastically changing backpressure.\n"
                f"- **The Backpressure Myth & Low-End Torque:** An overly free-flowing straight pipe reduces scavenging velocity at low RPM. On a long-stroke engine like the {model}, this often results in a **noticeable loss of low-end pull** in exchange for higher top-end noise.\n"
                f"- **Lean Fuel Mixture Alert:** Removing exhaust restriction leans out the air-fuel mixture. On modern Fuel-Injected (EFI) bikes, you should pair a free-flow exhaust with a booster plug (like FuelX) to prevent exhaust valve overheating.\n"
                f"- **RTO & Legal Decibel Limits:** Indian motor vehicle rules mandate a maximum sound level of **85-90 dB**. If you install a slip-on (like Red Rooster, Barrel, or AEW), **always keep the DB-killer (baffle) installed** to avoid challans and ear fatigue on long rides!"
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 5. MODIFICATIONS: Wider Tyres / Tyre Upsizing
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["wider tyre", "wider tire", "fat tyre", "fat tire", "upsize tyre", "upsize tire", "bigger tyre", "bigger tire", "140 section", "150 section"]) or (any(k in msg for k in ["tyre", "tire"]) and any(k in msg for k in ["wider", "fatter", "bigger", "upsize"])):
            reply = (
                f"### 🏍️ Tyre Upsizing Reality Check for {mfg} {model}\n\n"
                f"Putting a wider, beefier tyre on your **{model}** looks muscular, but here is the physics behind it:\n\n"
                f"1. **The Rim Pinching Problem:** Your stock rear wheel rim is engineered for a specific width (typically 120/80 or 140/70 depending on model). Squeezing an overly wide 140 or 150 tyre onto a narrow rim pinches the sidewalls inward, distorting the tread profile into a steep dome — **giving you LESS cornering contact patch, not more!**\n"
                f"2. **Sluggish Handling:** A heavier, wider rear tyre increases gyroscopic inertia. Flicking the bike through tight chicanes and filtering in city traffic will feel significantly heavier.\n"
                f"3. **Clearance Issues:** You risk the tyre rubbing against the swingarm, drive chain guard, or brake torque rod under full suspension compression.\n\n"
                f"**Wrenchy's Recommendation:** Stick to OEM sizing or at most go **one profile step wider** (e.g. 120/80 to 130/70) only if the tyre bead seats naturally on the rim. Prioritize sticky compound (like Apollo Tramplr or Michelin City Pro) over extra width!"
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 6. MODIFICATIONS: Spoke to Tubeless Conversion
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["convert to tubeless", "tube to tubeless", "spoke tubeless", "tubeless kit", "outex", "way2speed"]) or ("spoke" in msg and "tubeless" in msg):
            reply = (
                f"### 🛞 Spoke Wheel Tubeless Conversion for {mfg} {model}\n\n"
                f"Dealing with a sudden puncture on a heavy tube-type spoke wheel on the highway is every rider's nightmare. Here are your two options:\n\n"
                f"#### Option A: Rim Sealing Kits (Outex / Way2Speed)\n"
                f"- Specialized heat-resistant multi-layer tape and nipple seals cover the spoke nipples from inside the rim.\n"
                f"- **Pros:** Retains the classic spoke aesthetic; cost-effective.\n"
                f"- **Cons:** Must be installed with surgical precision (any spoke truing later breaks the seal and causes slow air leaks).\n\n"
                f"#### Option B: OEM Factory Alloy Wheel Swap (Recommended)\n"
                f"- Swap your spoke rims for genuine OEM factory alloy wheels designed for tubeless tyres.\n"
                f"- **Pros:** 100% airtight reliability, zero leak anxiety, handles hard impacts without bending spoke nipples, and repairable in 2 minutes with a standard puncture strip on the roadside!"
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 7. MODIFICATIONS: Auxiliary Lights & Fog Lamps
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["aux light", "aux lights", "fog light", "fog lights", "fog lamp", "fog lamps", "led headlight", "hazard light", "auxiliary light"]):
            reply = (
                f"### 💡 Auxiliary Lights & Electrical Load for {mfg} {model}\n\n"
                f"Night touring demands great visibility, but before mounting auxiliary LED pods on your **{model}**, respect the electrical math:\n\n"
                f"- **Alternator Stator Headroom:** Your motorcycle's stator alternator produces ~150W to 220W total. The ECU, fuel pump, ignition, and stock lights consume ~100W, leaving around **40W to 60W of spare capacity**.\n"
                f"- **Golden Rule of Wiring:** **NEVER splice into the stock OEM headlight or ignition wiring!** Always use an independent wiring harness with a **40A automotive relay**, an **inline 10A fuse**, and heavy-gauge wire running directly to the battery terminals.\n"
                f"- **Wattage Tip:** Opt for high-efficiency LED lights drawing **20W to 30W per pair** (like Maddog Scout or Baja Designs). Anything above 60W will slowly discharge your **{bike.get('battery_capacity_ah', 8.0)} Ah** battery during slow city riding!"
            )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Check Battery & Stator Voltage"}

        # ---------------------------------------------------------------------
        # 8. SYMPTOMS: Vibrations & Handlebar Wobble
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["vibrat", "wobble", "shaking", "handlebar shake", "buzzing", "speed wobble"]):
            reply = (
                f"### 🛠️ Vibration & Wobble Diagnostics for {mfg} {model}\n\n"
                f"Motorcycle vibrations generally fall into three distinct mechanical categories:\n\n"
                f"1. **RPM-Dependent Vibration (Engine/Chassis):** If the buzz happens at a specific engine RPM regardless of what gear you're in, check your **engine mounting bolts**. Over time, vibration backs out engine hanger bolts, causing the engine to resonate against the frame.\n"
                f"2. **Speed-Dependent Wobble (Wheels & Tyres):** If the handlebar wobbles between 60–80 km/h, check for **uneven tyre wear (cupping)**, missing wheel balancing weights, or a bent wheel rim.\n"
                f"3. **Drivetrain Surge:** A chain with **tight spots** (unevenly stretched links) will create a rhythmic pulse under your footpegs every time the tight spot rolls over the countershaft sprocket.\n\n"
                f"Check your handlebar bar-end weights as well — they act as harmonic dampeners that kill high-frequency numbness in your palms!"
            )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Start Chassis Vibration Diagnosis"}

        # ---------------------------------------------------------------------
        # 9. SYMPTOMS: Stalling When Hot
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["stalls when hot", "dies when hot", "cuts off when hot", "shuts off when hot", "hard start when hot", "stalling when hot"]) or (any(k in msg for k in ["stall", "shut off", "cut off", "die"]) and any(k in msg for k in ["hot", "heat", "warm"])):
            reply = (
                f"### 🌡️ Engine Stalling When Hot: Root Cause Analysis\n\n"
                f"If your **{model}** starts and idles great when cold, but stumbles, stalls, or refuses to restart once fully warmed up, check these three classic culprits:\n\n"
                f"1. **Tight Tappet / Valve Clearances:** As engine valves heat up, the metal valve stems expand. If your valve lash is set too tight, the exhaust valve can't fully seat when hot, causing **sudden loss of cylinder compression** at idle!\n"
                f"2. **Failing Stator Pulsar (Crank Position) Coil:** When the ignition pick-up coil gets hot, microscopic thermal cracks inside the copper windings expand and break the electrical circuit, cutting off spark until it cools down.\n"
                f"3. **Fuel Tank Cap Breather Clog (Vapor Lock):** If the tank vent hole is clogged with wax or debris, fuel leaving the tank creates a vacuum that starves the injector. *Pro tip:* When it stalls, pop the fuel filler cap open — if you hear a sharp *whoosh* of air, your cap breather is blocked!"
            )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Diagnose Engine Thermal State"}

        # ---------------------------------------------------------------------
        # 10. SYMPTOMS: Wrong Oil / Mixing Oils / JASO MA2
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["wrong oil", "mix oil", "mix synthetic", "overfill", "underfill", "too much oil", "low oil", "car oil"]) or ("oil" in msg and any(k in msg for k in ["wrong", "mix", "car", "overfill", "too much", "drain"])):
            reply = (
                f"### 🛢️ Oil Mistakes & What Actually Happens to Your Engine\n\n"
                f"Motorcycle lubrication is unique, and here is the truth on the common oil dilemmas for your **{model}**:\n\n"
                f"- **Using Car Engine Oil? (BIG DANGER):** Modern passenger car oils contain molybdenum friction modifiers designed to maximize fuel economy. In your motorcycle with a wet multi-plate clutch, these friction modifiers will **soak into the clutch plates and cause permanent slipping under acceleration!** Always demand **JASO MA / MA2** certified motorcycle oil.\n"
                f"- **Mixing Mineral & Synthetic:** In an emergency, mixing brands or blending semi-synthetic with full synthetic will NOT destroy your engine. Modern base oils are fully miscible. Just flush and renew with fresh **{oil}** at your earliest convenience.\n"
                f"- **Overfilling the Sight Glass:** Putting too much oil causes the spinning crankshaft counterweights to whip the oil into a frothy milkshake of air bubbles. Oil pumps cannot pump aerated foam, leading to starvation of the overhead camshaft!"
            )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Check Oil Specifications"}

        # ---------------------------------------------------------------------
        # 11. SYMPTOMS: Battery Draining Overnight (Parasitic Draw)
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["draining overnight", "battery dies overnight", "battery drain", "parasitic draw", "dies in morning"]) or ("battery" in msg and any(k in msg for k in ["drain", "dead in morning", "overnight", "discharging"])):
            reply = (
                f"### ⚡ Parasitic Battery Drain Diagnostics\n\n"
                f"If your battery drops flat overnight, your motorcycle has an unwanted electrical draw while the key is off:\n\n"
                f"1. **Aftermarket Accessories (90% of cases):** Hardwired USB phone chargers, GPS trackers, or illuminated hazard switches often draw 20–50 mA constantly even with the bike turned off.\n"
                f"2. **Faulty Rectifier Diode:** A blown diode in the regulator/rectifier unit allows current to leak backwards from the positive terminal into the alternator stator coils overnight.\n"
                f"3. **How to Test with a Multimeter:** Turn the key off. Disconnect the negative battery terminal and place a multimeter set to **DC Milliamps (mA)** in series between the battery post and cable. Normal key-off draw for your {model} should be **under 3.0 mA**!"
            )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Diagnose Battery & Voltage"}

        # ---------------------------------------------------------------------
        # 12. SYMPTOMS: Exhaust Smoke Colors
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["white smoke", "black smoke", "blue smoke", "smoke from exhaust", "exhaust smoke"]):
            reply = (
                f"### 💨 Reading Exhaust Smoke Like a Master Mechanic\n\n"
                f"The color of smoke coming from your motorcycle's tailpipe tells you exactly what is burning inside the cylinder:\n\n"
                f"- **Blue / Grey Smoke:** **Burning Engine Oil.** Oil is creeping into the combustion chamber past worn piston rings, a scored cylinder bore, or hardened valve stem oil seals. Check your sight glass immediately!\n"
                f"- **Black Smoke:** **Excessive Unburnt Fuel (Rich Mixture).** The engine is choking on fuel due to a clogged air filter, leaking fuel injector, or faulty oxygen sensor.\n"
                f"- **Thin White Vapor on Cold Mornings:** Pure condensation evaporating from the cold exhaust muffler. It should clear within 2–3 minutes of riding.\n"
                f"- **Thick White Sweet-Smelling Smoke (Liquid-Cooled bikes only):** Coolant burning in the cylinder head from a blown head gasket."
            )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Launch Exhaust & Engine Diagnostics"}

        # ---------------------------------------------------------------------
        # 13. COMPARISONS: Royal Enfield 350 Family
        # ---------------------------------------------------------------------
        if ("classic" in msg or "hunter" in msg or "meteor" in msg or "bullet" in msg) and any(k in msg for k in ["vs", "better", "difference", "compare", "which should", "which one"]):
            reply = (
                f"### 🏍️ Royal Enfield J-Platform 350 Lineup Compared\n\n"
                f"All four bikes share the same fantastic **349 cc counterbalanced J-series engine (20.2 bhp, 27 Nm torque)**, but each has a completely different personality:\n\n"
                f"1. **Classic 350:** The quintessential retro gentleman. 19-inch front and 18-inch rear wheels give it majestic high-speed stability and road presence. Upright, neutral riding posture with a springy sprung-rider seat feel.\n"
                f"2. **Hunter 350:** The urban street rebel. Shorter wheelbase, sharper rake angle, and agile 17-inch wheels drop 14 kg of curb weight. It dives into city corners like a modern streetfighter.\n"
                f"3. **Meteor 350:** The pure highway cruiser. Forward footpegs, sweeping handlebar, lower 765 mm seat height, and softer rear suspension make it effortless for eating up 500 km days.\n"
                f"4. **Bullet 350:** Pure heritage. Single-piece stepped bench seat, squared rear fender, and retro upright ergonomics.\n\n"
                f"**Verdict:** Pick Hunter for zippy city traffic, Meteor for relaxed highway cruising, and Classic for the timeless all-rounder look!"
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 14. Road Trips & Touring Guide
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["trip", "tour", "touring", "pack", "packing", "highway", "long ride", "luggage", "saddlebag", "road trip", "ladakh", "spiti"]):
            reply = (
                f"### 🏍️ Road Trip & Touring Guide for Your {model}\n\n"
                f"Nothing beats hitting the highway on two wheels, {first_name}! Before embarking on a long journey with your **{mfg} {model}**, here is the battle-tested checklist I swear by:\n\n"
                f"#### 1. Bike Preparation (The Pre-Flight)\n"
                f"- **Tyre Pressures:** With full luggage or a pillion, bump up your rear tyre pressure by **2 to 3 PSI** (aim for **{rear_psi + 2} PSI** rear, **{front_psi} PSI** front) to prevent sidewall overheating and tyre squirm.\n"
                f"- **Chain Service:** Clean and lube your {drive.lower()} drive thoroughly before departure, and verify slack (target: **{chain_slack}**).\n"
                f"- **Fluid Check:** Verify oil level in the sight glass (**{oil}**). Pack a small 500ml top-up bottle if touring over 1,500 km.\n\n"
                f"#### 2. Packing The Golden Rule\n"
                f"- **Low and Centred:** Heaviest tools, spares, and chain lube at the very bottom of your saddlebags, as close to the bike's centre of gravity as possible. Never mount heavy weight high up on a top rack!\n\n"
                f"#### 3. Emergency Kit You Should Never Leave Without\n"
                f"- Compact tubeless puncture repair kit + portable 12V/battery inflator.\n"
                f"- 8mm, 10mm, 12mm T-spanners, Allen keys, pliers, and heavy-duty zip ties.\n"
                f"- Spare clutch cable and fuse pack.\n\n"
                f"#### 4. Rider Stamina & Hydration\n"
                f"- Wear **foam earplugs**! Wind noise above 80 km/h causes brain fatigue much faster than physical riding.\n"
                f"- Take a 10-minute break every 90 minutes to stretch your hips and hydrate.\n\n"
                f"Where are you planning to ride next?"
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 15. How an Engine Works (Plain English)
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["how does an engine work", "how engine works", "four stroke", "4 stroke", "piston", "internal combustion", "cylinder"]):
            reply = (
                f"### ⚙️ How Your 4-Stroke Engine Works (In Plain English)\n\n"
                f"Under the tank of your **{mfg} {model}**, there is a **{disp_cc} cc** four-stroke combustion chamber. "
                f"You can remember how every four-stroke motorcycle engine breathes with the famous mechanic rhyme: "
                f"**Suck, Squeeze, Bang, Blow!**\n\n"
                f"1. **Suck (Intake Stroke):** The piston travels downward inside the cylinder. The intake valve opens, creating a vacuum that sucks in a fresh mist of atomised petrol and air.\n"
                f"2. **Squeeze (Compression Stroke):** The intake valve snaps shut. The piston rockets back upward, squeezing that air-fuel cocktail into a tiny, super-dense pocket at the top of the cylinder head.\n"
                f"3. **Bang (Power Stroke):** Right at the peak, the spark plug fires an electric spark. The fuel mixture detonates in a controlled fireball! The expanding gases violently shove the piston down — **this is where 100% of your motorcycle's power and acceleration comes from!**\n"
                f"4. **Blow (Exhaust Stroke):** The exhaust valve opens, and as the piston sweeps back up one last time, it pushes the spent burnt gases out through the exhaust header and muffler.\n\n"
                f"The connecting rod turns that up-and-down piston movement into spinning rotational force at the crankshaft, which sends power through the clutch, gearbox, and final drive to your rear tyre!"
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 16. Countersteering & Cornering Physics
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["countersteering", "counter steer", "corner", "cornering", "turn", "turning", "lean", "leaning", "knee down", "apex"]):
            reply = (
                f"### 🏁 The Magic of Countersteering & Cornering Physics\n\n"
                f"Countersteering sounds completely backward the first time you hear it, but every single two-wheeler rider does it instinctively above ~15 km/h:\n\n"
                f"> **To initiate a turn to the RIGHT, you gently push forward on the RIGHT handlebar grip!**\n\n"
                f"#### Why does this happen?\n"
                f"When you push the right handlebar forward, the front tyre momentarily steers slightly left. "
                f"Because the motorcycle's centre of gravity wants to keep travelling straight (inertia), the contact patch moves out from underneath the bike, causing the entire motorcycle to instantly and effortlessly tip into a lean to the right!\n\n"
                f"#### Wrenchy's Pro Cornering Tips for Your {model}:\n"
                f"1. **Look Where You Want to Go:** Your hands follow your eyes. Never stare at the gravel or the guardrail — turn your helmet and look through to the corner exit!\n"
                f"2. **Grip with Your Knees:** Anchor your lower body firmly to the tank. Keep your arms, wrists, and shoulders relaxed so your front suspension can respond to road imperfections.\n"
                f"3. **Smooth Roll-on:** Once you tip in and see your exit, smoothly roll on maintenance throttle to settle the rear suspension and track cleanly out of the apex."
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 17. Riding Gear (ATGATT)
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["gear", "helmet", "jacket", "gloves", "boots", "riding pants", "armor", "ece", "dot", "atgatt"]):
            reply = (
                f"### 🛡️ Motorcycle Gear Wisdom (Dress for the Slide, Not the Ride)\n\n"
                f"In the motorcycle community, we live by **ATGATT: All The Gear, All The Time**. "
                f"Tarmac at 60 km/h behaves like a giant belt sander. Here is how to pick genuine protective gear:\n\n"
                f"- **Helmet (Most Critical):** Always look for **ECE 22.06** certification. It tests for direct impacts, oblique rotational brain acceleration, and visor shatter resistance (much more rigorous than basic US DOT).\n"
                f"- **Riding Jacket:** Look for abrasion-resistant 600D Cordura or leather equipped with **CE Level 2** armor in the shoulders, elbows, and especially the back protector.\n"
                f"- **Riding Gloves:** Palms hit the road first by human reflex. Always wear full-gauntlet or reinforced short gloves with **scaphoid palm sliders** and hard knuckle protection.\n"
                f"- **Boots:** Regular sneakers or work boots rip right off in a crash. Purpose-built motorcycle boots have torsion bars that prevent your ankle from twisting sideways.\n\n"
                f"Good gear gives you massive confidence on the road because your mind isn't distracted by fear."
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 18. Drivetrain & Chain Maintenance (Carefully scoped!)
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["chain slack", "chain tight", "lube chain", "clean chain", "chain maintenance", "adjust chain", "chain noise", "loose chain"]) or (("chain" in msg or "sprocket" in msg) and not any(k in msg for k in ["belt", "install", "convert", "upgrade", "mod", "switch"])):
            if drive == "Chain":
                slack_val = readings.get("CHAIN_SLACK", 27.0)
                reply = (
                    f"### ⛓️ Drive Chain Health for {mfg} {model}\n\n"
                    f"Your bike uses an exposed roller chain final drive.\n\n"
                    f"- **OEM Slack Specification:** **{chain_slack}** (measured midway between sprockets with the bike on its stand).\n"
                    f"- **Current Simulated Slack:** **{slack_val} mm**.\n"
                    f"- **Wrenchy's Rule of Thumb:** Clean and lube every **500 km** (or immediately after riding in the rain). "
                    f"Always apply chain lube to the *inside* of the lower run right after a ride when the chain is warm so the lube penetrates into the O-rings."
                )
            elif drive == "Belt":
                reply = (
                    f"### ⚙️ Carbon Belt Drive on Your {model}\n\n"
                    f"Your bike features a belt drive! Zero chain lube, zero grease fling, and almost silent operation.\n\n"
                    f"- Inspect belt teeth for stone gouges or cracking every 5,000 km.\n"
                    f"- Never spray oil or petroleum solvents on the belt."
                )
            else:
                reply = (
                    f"### ⚙️ Enclosed Shaft Drive on Your {model}\n\n"
                    f"Your bike features an enclosed shaft and bevel gear final drive — virtually maintenance-free with no chain slack or lubrication worries."
                )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Diagnose Drivetrain"}

        # ---------------------------------------------------------------------
        # 19. Tyre Pressure & Cold Standards
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["tyre pressure", "tire pressure", "psi", "cold pressure"]) or (any(k in msg for k in ["tyre", "tire"]) and not any(k in msg for k in ["wider", "fatter", "upsize", "bigger", "tubeless", "install", "convert"])):
            reply = (
                f"### 🏍️ Tyre Pressures & Grip for Your {mfg} {model}\n\n"
                f"Tyres are the only two contact patches connecting you to the planet! Factory cold specs:\n\n"
                f"- **Front Tyre:** **{front_psi} PSI** (Size: {bike.get('front_tyre_size', 'Standard')})\n"
                f"- **Rear Tyre:** **{rear_psi} PSI** (Size: {bike.get('rear_tyre_size', 'Standard')})\n"
                f"- **Tyre Type:** {bike.get('tyre_type', 'Tubeless')}\n\n"
                f"**Why Cold Pressures Matter:** Riding heats the air inside the carcass and raises pressure by 3 to 4 PSI. Always check pressures in the morning before riding!"
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 20. Engine Oil Specifications & Capacities
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["oil grade", "oil spec", "oil capacity", "oil change interval", "which oil", "what oil"]) or ("oil" in msg and not any(k in msg for k in ["wrong", "mix", "car", "overfill", "leak"])):
            reply = (
                f"### 🛢️ Engine Oil Guide for {mfg} {model}\n\n"
                f"Motorcycle oil is special because it handles **three jobs simultaneously**: lubricating the piston & rings, cushioning high-pressure gearbox gears, and cooling the wet clutch!\n\n"
                f"- **Verified Factory Grade:** **{oil}**\n"
                f"- **Crankcase Capacity:** **{bike.get('oil_capacity_l', 2.0)} Litres**\n"
                f"- **Recommended Service Interval:** Every **{bike.get('service_interval_km', 5000)} km**\n"
                f"- **Synthetic vs Mineral:** Full synthetic oil maintains its viscosity grade under high engine temperatures far better than conventional mineral oil, giving smoother gear shifts and longer engine life.\n\n"
                f"Always check oil level with the bike upright on level ground, not resting on the side stand."
            )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Check Oil Specifications"}

        # ---------------------------------------------------------------------
        # 21. Brakes & Pad Wear Diagnostics
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["brake", "stopping", "squeak", "squeal", "spongy", "pad", "shoe", "rotor", "abs", "bleeding"]):
            pad_val = readings.get("BRAKE_PAD_WEAR", 4.5)
            reply = (
                f"### 🛑 Braking System Assessment for {mfg} {model}\n\n"
                f"Your motorcycle is equipped with **{brakes}** backed by **{abs_type}**.\n\n"
                f"- **Current Friction Thickness:** **{pad_val} mm** (OEM service limit: **2.0 mm**).\n"
                f"- **Brake Fluid:** Hydraulic circuit uses **{bike.get('brake_fluid_type', 'DOT 4')}** (service renewal every {bike.get('brake_fluid_interval_km', 10000)} km).\n"
                f"- **Squeaking or Squealing?** Usually caused by glazed friction material from overheating, brake dust buildup, or missing anti-squeal shims.\n"
                f"- **Spongy Lever Feel?** Indicates tiny air bubbles in the hydraulic lines or moisture-contaminated brake fluid. A simple bleed restores crisp bite.\n\n"
                f"> ⚠️ **Safety Notice:** Brakes are your primary lifeline. If your lever pulls all the way to the grip or pad friction material is near 2.0 mm, arrange immediate replacement."
            )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Diagnose Braking System"}

        # ---------------------------------------------------------------------
        # 22. Thermal & Temperature Diagnostics
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["overheat", "hot", "temperature", "temp", "smoke", "coolant", "radiator", "fins"]):
            temp_val = readings.get("ENG_TEMP", 85.0)
            if "Liquid" in cooling:
                reply = (
                    f"### 🌡️ Thermal Diagnostics for Your {mfg} {model}\n\n"
                    f"Your {model} uses a **liquid-cooled** thermal management system. Current simulated cylinder head temperature is **{temp_val} °C**.\n\n"
                    f"- **Nominal Operating Range:** Between **82 °C and 98 °C**.\n"
                    f"- **Inspection Points:** Check coolant expansion reservoir level (50:50 ethylene glycol and distilled water). Ensure the radiator fan kicks in automatically when stationary in heavy traffic.\n"
                    f"- **Safety Alert:** Never open the radiator pressure cap while the engine is warm!"
                )
            else:
                reply = (
                    f"### 🌡️ Thermal Dissipation for Your {mfg} {model}\n\n"
                    f"Your {model} relies on an **{cooling}-cooled** setup. Current simulated engine temperature is **{temp_val} °C**.\n\n"
                    f"- **How It Stays Cool:** Air-cooled engines rely on forward airflow over cylinder cooling fins, plus circulating engine oil acting as a liquid heat sink.\n"
                    f"- **Oil Spec:** Verified factory oil grade is **{oil}** (capacity: {bike.get('oil_capacity_l', 2.0)} L).\n"
                    f"- **Garage Advice:** Keep cylinder fins clean of road mud, and avoid extended idling at standstill on hot afternoons."
                )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Run Thermal Diagnosis"}

        # ---------------------------------------------------------------------
        # 23. Battery & Starting Diagnostics
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["battery", "start", "starting", "crank", "voltage", "volt", "electric", "dead battery", "stator"]):
            volt_val = readings.get("BAT_VOLT", 14.1)
            reply = (
                f"### ⚡ Electrical System & Battery Health for {mfg} {model}\n\n"
                f"Your bike uses a **{bike.get('battery_voltage', 12.0)}V {bike.get('battery_capacity_ah', 8.0)}Ah {bike.get('battery_type', 'Maintenance-Free')}** battery.\n\n"
                f"- **Current System Voltage:** **{volt_val} V**.\n"
                f"- **Key Diagnostics:** Key-off resting should be **12.6 V to 12.8 V**; running charging voltage should rise to **13.8 V – 14.4 V**.\n"
                f"- **Clicking Noise on Start?** Almost always indicates battery voltage collapsing under starter motor draw."
            )
            return reply, {"action": "NAVIGATE_TO_DIAGNOSTICS", "label": "Diagnose Electrical System"}

        # ---------------------------------------------------------------------
        # 24. Humor, Jokes & Motorcycle Trivia
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["joke", "funny", "trivia", "fact", "bored", "laugh"]):
            reply = (
                f"Haha, here’s a classic garage joke for you, {first_name}!\n\n"
                f"**Why do motorcycles make terrible house pets?**\n"
                f"*Because every time you take them out, they want to go 120 km/h, drink petrol, and wake up all the neighbours!*\n\n"
                f"**Did you know this fun trivia?**\n"
                f"The very first internal combustion motorcycle ever built was the *Daimler Reitwagen* in 1885. It had wooden wheels, a wooden frame, and produced a grand total of **0.5 horsepower**!\n\n"
                f"Compare that to your **{mfg} {model}** with **{disp_cc} cc** of pure engineering today. We've come a long way!"
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 25. Gratitude & Friendly Sign-Off
        # ---------------------------------------------------------------------
        if any(k in msg for k in ["thank", "thanks", "appreciate", "good job", "awesome", "cool", "helpful", "great"]):
            reply = (
                f"You're very welcome, {first_name}! That's what I'm here for.\n\n"
                f"Take care of your **{mfg} {model}**, keep the shiny side up and the rubber side down on the asphalt, "
                f"and hit me up whenever you want to inspect something or plan your next ride! 🏍️💨"
            )
            return reply, None

        # ---------------------------------------------------------------------
        # 26. Dynamic Conversational Fallback
        # ---------------------------------------------------------------------
        reply = (
            f"Hey {first_name}! I hear you on that. As your personal mechanic for the **{mfg} {model}**, "
            f"I keep a close eye on your motorcycle's verified factory specs, upgrades, and live telemetry.\n\n"
            f"Right now, your simulated telemetry status is **{ctx.get('telemetry_status', 'ONLINE')}**, "
            f"battery is sitting at **{readings.get('BAT_VOLT', 14.1)} V**, and engine temp is **{readings.get('ENG_TEMP', 85.0)} °C**.\n\n"
            f"Feel free to ask me anything in plain English:\n"
            f"- *'Can I install a belt drive conversion on my bike?'*\n"
            f"- *'How do I prep my motorcycle for a 1,000 km road trip?'*\n"
            f"- *'What causes spongy brakes or clutch slip?'*\n"
            f"- *'Can I put a free-flow exhaust or wider tyres?'*\n\n"
            f"What would you like to explore next?"
        )
        return reply, None
