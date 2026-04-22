import os
import uuid
import base64
import asyncio
import re
import random
import io
import pdfplumber
import edge_tts
from gtts import gTTS
from fastapi import FastAPI, WebSocket, UploadFile, File, Form, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import urllib.request
from dotenv import load_dotenv

# --- NEW SDK IMPORTS ---
from google import genai
from google.genai import types

# --- CONFIGURATION ---
load_dotenv()
API_KEY = "AIzaSyCIU8075NLBL0orO7THVP4q4yMmmqljjj0"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for robustness in dev/prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- IN-MEMORY SESSION STORE ---
sessions: Dict[str, "InterviewSession"] = {}

def clean_text_for_tts(text: str) -> str:
    text = re.sub(r'\*', '', text)
    text = re.sub(r'#', '', text)
    return text.strip()


class InterviewSession:
    def __init__(self, resume_text: str, jd_text: str):
        self.resume_text = resume_text
        self.jd_text = jd_text
        self.transcript = []
        self.question_count = 0
        self.max_questions = 10 
        
        # Simple default voice configuration
        self.voice_id = "en-US-AriaNeural" # Clear, professional female voice
        self.backup_tld = "us"
        
        self.client = genai.Client(api_key=API_KEY)

        # --- UPDATED PROMPT: TEACHER EVALUATION ---
        self.system_instruction = f"""
        You are an expert Educational Recruiter. Your role is to test the candidate's (the user's) ability to teach, explain complex topics, and simplify them so effectively that a small child could understand. You are also strictly evaluating their communication clarity, patience, and English fluency.
        
        CONTEXT:
        RESUME: {self.resume_text[:3000]}
        SUBJECT/ROLE CONTEXT: {self.jd_text[:1500]}
        
        INTERVIEW STRUCTURE:
        0. Introduction: Welcome the candidate, introduce yourself as the recruiter, and ask them for a brief introduction.
        1. The Simplification Test: Pick a complex topic from their resume or the provided context and ask them to explain it as if you were a 7-year-old child.
        2. Roleplay / Cross-Questioning: Act like the confused 7-year-old student. Ask a naive or silly follow-up question based on their explanation to test their patience, analogies, and ability to pivot their teaching style.
        3. Teaching Methodology: Ask how they assess if a student has actually internalized a concept versus just rote memorizing it. 
        4. Fluency & Scenario: Present a brief classroom scenario (e.g., a student not paying attention or a difficult parent) and ask how they would handle the communication.
        5. Conclusion: End the interview politely.
        
        RULES:
        - ONE question at a time.
        - Be concise and conversational (spoken style).
        - Do not break character. 
        - If user says "TIME_IS_UP_SIGNAL", conclude immediately.
        """

        self.chat = self.client.aio.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.7 
            )
        )

    async def get_next_response(self, user_input: str = None, is_silence_trigger: bool = False, is_time_up: bool = False):
        if is_time_up:
            prompt = "Time is up. Briefly thank the candidate and end the interview."
            response = await self.chat.send_message(prompt)
            return clean_text_for_tts(response.text), True 

        if self.question_count >= self.max_questions:
            return "The interview is now over. I will generate your feedback.", True 

        if is_silence_trigger:
            prompt = "The candidate is silent. As the recruiter, politely nudge them to answer."
        else:
            if self.question_count == 0 and not user_input:
                prompt = "Start the interview. Introduce yourself briefly."
            else:
                prompt = f"""
                Candidate Answer: "{user_input}"
                Instructions: Evaluate the answer. Cross-question if needed, acting as a student if appropriate. Otherwise ask the next question. Keep your response short and conversational.
                """

        response = await self.chat.send_message(prompt)
        ai_text = clean_text_for_tts(response.text)
        
        self.question_count += 1
        
        self.transcript.append(f"User: {user_input if user_input else '[SILENCE]'}")
        self.transcript.append(f"AI (Recruiter): {ai_text}")
        
        is_finished = "interview is now over" in ai_text.lower() or "time is up" in ai_text.lower()
        
        return ai_text, is_finished

    async def generate_feedback(self):
        prompt = """
        Based on the entire transcript, provide detailed feedback as a Lead Educator evaluating this teaching candidate.
        Structure:
        1. **Ability to Simplify Concepts**: Did they use good analogies? Could a child understand them?
        2. **Communication & English Fluency**: Assess their grammar, tone, clarity, and pacing.
        3. **Teaching Methodology**: How well did they handle cross-questions and assess understanding?
        4. **Areas for Improvement**: Specific constructive criticism.
        5. **Overall Teaching Score (0-100%)**
        6. **FINAL REMARKS**
        """
        response = await self.chat.send_message(prompt)
        return clean_text_for_tts(response.text)

# --- 3-LAYER AUDIO GENERATION ---
async def generate_audio_stream(text: str, voice_id: str, backup_tld: str) -> str:
    """
    1. EdgeTTS (Best, Male/Female) - Timeout 10s
    2. gTTS Accented (Reliable, always Female) - Timeout 10s
    3. gTTS US Standard (Ultimate Backup)
    """
    
    # --- LAYER 1: EdgeTTS (High Quality) ---
    try:
        communicate = edge_tts.Communicate(text, voice_id)
        mp3_data = b""
        
        async def run_edge():
            nonlocal mp3_data
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    mp3_data += chunk["data"]
        
        await asyncio.wait_for(run_edge(), timeout=5.0)
        
        if len(mp3_data) > 0:
            print("✅ EdgeTTS Success")
            return base64.b64encode(mp3_data).decode("utf-8")
            
    except asyncio.TimeoutError:
        print("⚠️ Layer 1 (EdgeTTS) TIMEOUT - Server was too slow.")
    except Exception as e:
        print(f"⚠️ Layer 1 (EdgeTTS) Error: {str(e)}")

    # --- LAYER 3: gTTS (Standard US - Failsafe) ---
    try:
        print("🔄 Falling back to Standard US gTTS...")
        def run_gtts_std():
            fp = io.BytesIO()
            tts = gTTS(text=text, lang='en', tld='us')
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()

        gtts_data = await asyncio.to_thread(run_gtts_std)
        return base64.b64encode(gtts_data).decode("utf-8")
        
    except Exception as e:
        print(f"❌ ALL AUDIO LAYERS FAILED: {str(e)}")
        return "" 

# --- API ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "active"}

@app.post("/upload-context")
async def upload_context(
    resume: UploadFile = File(None), 
    resume_text: str = Form(None), 
    jd: str = Form(...)
):
    final_resume_text = ""
    if resume:
        with pdfplumber.open(resume.file) as pdf:
            for page in pdf.pages:
                final_resume_text += page.extract_text() or ""
    elif resume_text:
        final_resume_text = resume_text

    session_id = str(uuid.uuid4())
    sessions[session_id] = InterviewSession(final_resume_text, jd)
    return {"session_id": session_id}

@app.websocket("/ws/interview/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    if session_id not in sessions:
        await websocket.close(code=4004, reason="Session not found")
        return

    session = sessions[session_id]
    
    # --- KEEP ALIVE PINGER (PREVENT SLEEP) ---
    async def keep_alive_ping():
        while True:
            await asyncio.sleep(60)
            try:
                port = int(os.getenv("PORT", 8000))
                reader, writer = await asyncio.open_connection("127.0.0.1", port)
                writer.write(b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass 

    ping_task = asyncio.create_task(keep_alive_ping())

    try:
        # Initial Question
        ai_text, _ = await session.get_next_response(user_input=None)
        
        # Audio Gen
        audio_b64 = await generate_audio_stream(ai_text, session.voice_id, session.backup_tld)
        
        await websocket.send_json({"type": "audio", "data": audio_b64, "text": ai_text})

        # Loop
        while True:
            data = await websocket.receive_json()
            user_text = data.get("text")
            msg_type = data.get("type") 
            
            is_silence = (msg_type == 'silence_timeout')
            is_time_up = (msg_type == 'time_up')

            ai_text, is_finished = await session.get_next_response(
                user_text, 
                is_silence_trigger=is_silence, 
                is_time_up=is_time_up
            )
            
            audio_b64 = await generate_audio_stream(ai_text, session.voice_id, session.backup_tld)

            if is_finished:
                await websocket.send_json({"type": "audio", "data": audio_b64, "text": ai_text})
                
                feedback_text = await session.generate_feedback()
                await websocket.send_json({
                    "type": "feedback", 
                    "text": feedback_text, 
                    "is_finished": True
                })
                break
            else:
                await websocket.send_json({"type": "audio", "data": audio_b64, "text": ai_text})

    except WebSocketDisconnect:
        if session_id in sessions: del sessions[session_id]
        print(f"Session {session_id} disconnected")
    finally:
        ping_task.cancel()