import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import re
import time

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="2학년 공부 짝꿍", page_icon="🐥", layout="centered")

# --- 2. Custom CSS (더 커진 글씨와 부드러운 디자인) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    .stButton > button {
        width: 100%; border-radius: 30px; font-weight: bold;
        background-color: #FFBD45; color: black; height: 3.5em; font-size: 1.3rem !important;
        border: none; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }
    .answer-text { 
        line-height: 2.8; 
        font-size: 1.5rem; 
        word-break: keep-all;
        margin-bottom: 30px;
        color: #ffffff;
        background: #1e2129;
        padding: 20px;
        border-radius: 15px;
    }
    .eng-box {
        background-color: #262730; padding: 20px; 
        border-radius: 20px; border: 3px solid #FFBD45;
        margin: 20px 0;
        text-align: center;
    }
    h1 { color: #FFBD45 !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. 모델 설정 (에러 방지 핵심 로직) ---
def get_model():
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("열쇠(API KEY)가 없어요! 설정창을 확인해주세요.")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # 무료 버전에서 가장 할당량이 넉넉한 모델명을 고정합니다.
    # 접두어 'models/'를 붙여서 404 에러를 원천 방지합니다.
    return "models/gemini-1.5-flash"

# --- 4. 영어 발음 듣기 기능 ---
def play_eng_audio(text):
    clean_text = re.sub(r'[^a-zA-Z\s]', '', text).strip()
    if clean_text:
        try:
            tts = gTTS(text=clean_text, lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            st.audio(fp, format='audio/mp3')
        except:
            pass

# --- 5. 메인 UI ---
st.title("🐥 2학년 공부 짝꿍")

with st.container():
    subject = st.selectbox("어떤 공부인가요?", ["영어", "수학", "국어", "기타"])
    uploaded_file = st.file_uploader("📸 사진을 찍어서 보여줄까요?", type=["jpg", "png", "jpeg"])
    user_question = st.text_input("궁금한 걸 적어주세요!", placeholder="예: apple이 뭐야?")

    # 2학년 맞춤형 초간결 프롬프트
    system_instruction = f"""
    당신은 초등학교 2학년 아이의 가장 친한 친구입니다.
    
    [답변 규칙]
    1. 아주 짧은 문장으로 대답하세요.
    2. 문장마다 줄을 3번 바꾸세요 (글자 사이를 아주 넓게).
    3. 영어는 반드시 [ENG]문장[/ENG] 이렇게 써주세요.
    4. 친절하고 다정한 말투를 쓰세요 (~해요, ~란다).
    """

if st.button("짝꿍아 알려줘! 🚀", use_container_width=True):
    if user_question or uploaded_file:
        try:
            with st.spinner("짝꿍이 생각 중이에요... 10초만 기다려줘! ✨"):
                model_name = get_model()
                model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)
                
                inputs = []
                if user_question: inputs.append(user_question)
                if uploaded_file: inputs.append(Image.open(uploaded_file))
                
                response = model.generate_content(inputs)
                answer = response.text

            st.balloons()
            
            tab1, tab2 = st.tabs(["🎈 짝꿍의 대답", "🔍 전체 내용"])
            
            with tab1:
                parts = re.split(r'(\[ENG\].*?\[/ENG\])', answer, flags=re.DOTALL)
                for part in parts:
                    if part.startswith('[ENG]'):
                        eng_text = part.replace('[ENG]', '').replace('[/ENG]', '')
                        st.markdown(f'<div class="eng-box"><b>🎧 발음 들어보기</b>', unsafe_allow_html=True)
                        play_eng_audio(eng_text)
                        st.markdown(f'<span style="font-size: 1.8rem; color: #FFBD45;"><b>{eng_text}</b></span></div>', unsafe_allow_html=True)
                    else:
                        if part.strip():
                            st.markdown(f'<div class="answer-text">{part.strip()}</div>', unsafe_allow_html=True)
            
            with tab2:
                st.code(answer)

        except Exception as e:
            # 429 에러(할당량 초과) 발생 시 아이들에게 보여줄 친절한 메시지
            if "429" in str(e):
                st.error("앗! AI 짝꿍이 너무 열심히 공부해서 지금 조금 졸리대요. 😴")
                st.info("1분만 쉬었다가 다시 물어봐 줄래? 금방 일어날게! ✨")
            else:
                st.error("앗! 다시 한 번만 '알려줘!' 버튼을 눌러볼래? 💦")
                st.caption(f"상세 에러: {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>2학년 친구들의 똑똑한 짝꿍 ❤️</div>", unsafe_allow_html=True)
