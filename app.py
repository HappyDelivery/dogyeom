import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import re
import os

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="도겸이의 학습 도우미",
    page_icon="🐣",
    layout="centered"
)

# --- 2. CSS 스타일 ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    h1 { color: #FFD700 !important; text-align: center; font-family: 'Comic Sans MS', sans-serif; }
    .stButton > button {
        width: 100%; border-radius: 30px; font-weight: bold;
        background: linear-gradient(45deg, #FFBD45, #FFD54F);
        color: black; height: 3.5em; font-size: 1.3rem !important; border: none;
    }
    .answer-text { 
        line-height: 2.5; font-size: 1.4rem; color: #ffffff;
        background: #1e2129; padding: 25px; border-radius: 20px; border-left: 5px solid #FFBD45;
        margin-bottom: 20px;
    }
    .eng-box {
        background-color: #2E3440; padding: 20px; border-radius: 20px; border: 2px dashed #81A1C1;
        margin: 20px 0; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. [핵심] 모델 진단 및 연결 함수 ---
def configure_and_get_model():
    # 1. API 키 가져오기
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("🚫 API 키가 없어요! Streamlit 'Secrets' 설정을 확인해주세요.")
        return None

    # 2. 구글 설정
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"🚫 API 키 설정 중 오류: {str(e)}")
        return None

    # 3. 사용 가능한 모델 목록 조회 (여기가 성공해야 진짜 연결된 것)
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            st.error("🚫 이 API 키로 사용할 수 있는 모델이 하나도 없어요. (혹시 키가 만료되었나요?)")
            return None

        # 4. 가장 적합한 모델 선택 (Flash 우선)
        # models/gemini-1.5-flash 또는 gemini-1.5-flash 등을 찾음
        best_model = None
        for m in available_models:
            if 'flash' in m:
                best_model = m
                break
        
        if not best_model:
            best_model = available_models[0] # 없으면 아무거나 첫 번째

        return best_model

    except Exception as e:
        # 여기가 중요! 에러의 진짜 이유를 보여줍니다.
        st.error("🚫 구글 서버와 연결 실패!")
        st.code(f"에러 내용: {str(e)}")
        st.info("💡 팁: '400 Bad Request'는 API 키 오류, '429'는 사용량 초과입니다.")
        return None

# --- 4. 기타 기능 ---
def play_eng_audio(text):
    clean_text = re.sub(r'[^a-zA-Z\s]', '', text).strip()
    if clean_text:
        try:
            tts = gTTS(text=clean_text, lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            st.audio(fp, format='audio/mp3')
        except: pass

# --- 5. UI 메인 ---
st.title("🐣 도겸이의 학습 도우미 ✏️")

with st.container():
    subject = st.selectbox("어떤 공부인가요?", ["영어 🅰️", "수학 🔢", "국어 📖", "기타 🌈"])
    uploaded_file = st.file_uploader("📸 사진을 보여줄까요?", type=["jpg", "png", "jpeg"])
    user_question = st.text_input("궁금한 걸 적어주세요!", placeholder="예: apple이 뭐야?")

    system_instruction = f"""
    당신은 '도겸'이라는 초등학교 2학년 학생의 AI 단짝 친구입니다.
    1. 답변은 짧게 끊어서, 줄바꿈을 자주 하세요.
    2. 영어는 [ENG]단어[/ENG] 형태로 쓰세요.
    3. 다정한 말투(~했어?)를 쓰세요.
    """

if st.button("도겸이 궁금증 해결! 🚀", use_container_width=True):
    if user_question or uploaded_file:
        status = st.empty()
        status.info("🔍 AI 친구를 찾는 중...")
        
        # 모델 연결 시도
        model_name = configure_and_get_model()
        
        if model_name:
            try:
                status.info(f"✨ {model_name} 모델과 연결 성공! 생각하는 중...")
                
                model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)
                inputs = []
                if user_question: inputs.append(user_question)
                if uploaded_file: inputs.append(Image.open(uploaded_file))
                
                response = model.generate_content(inputs)
                answer = response.text
                
                status.empty()
                st.balloons()
                
                tab1, tab2 = st.tabs(["🎈 도겸이의 대답", "🔍 상세 보기"])
                with tab1:
                    parts = re.split(r'(\[ENG\].*?\[/ENG\])', answer, flags=re.DOTALL)
                    for part in parts:
                        if part.startswith('[ENG]'):
                            eng_text = part.replace('[ENG]', '').replace('[/ENG]', '')
                            st.markdown(f'<div class="eng-box"><b>🎧 영어 듣기</b>', unsafe_allow_html=True)
                            play_eng_audio(eng_text)
                            st.markdown(f'<span style="font-size: 1.8rem; color: #88C0D0;"><b>{eng_text}</b></span></div>', unsafe_allow_html=True)
                        elif part.strip():
                            st.markdown(f'<div class="answer-text">{part.strip()}</div>', unsafe_allow_html=True)
                with tab2:
                    st.success(f"연결된 모델: {model_name}")
                    st.code(answer)
                    
            except Exception as e:
                status.empty()
                st.error("앗! 답변을 만드는 도중에 문제가 생겼어요.")
                st.code(str(e))
    else:
        st.warning("질문이나 사진을 입력해주세요!")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>도겸이를 위한 특별한 학습 도우미 ❤️</div>", unsafe_allow_html=True)
