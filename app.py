import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import re

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="2학년 공부 짝꿍", page_icon="🐥", layout="centered")

# --- 2. Custom CSS (아이들을 위한 왕글자 스타일) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    .stButton > button {
        width: 100%; border-radius: 25px; font-weight: bold;
        background-color: #FFBD45; color: black; height: 3.5em; font-size: 1.3rem !important;
    }
    /* 2학년 아이들이 읽기 편하게 글자 크기와 줄 간격을 대폭 늘림 */
    .answer-text { 
        line-height: 2.8; 
        font-size: 1.4rem; 
        word-break: keep-all;
        margin-bottom: 25px;
        color: #fefefe;
    }
    .eng-box {
        background-color: #262730; padding: 20px; 
        border-radius: 20px; border: 3px solid #FFBD45;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. [핵심] 에러 없는 모델 탐색 함수 ---
def initialize_ai():
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("API Key가 없어요! Secrets를 확인해주세요.")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    try:
        # 현재 내 API 키로 쓸 수 있는 모델들을 싹 다 훑어봅니다.
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 1순위: flash (빠름), 2순위: pro (똑똑함)
        for target in ["gemini-1.5-flash", "gemini-1.0-pro", "gemini-pro"]:
            for model_path in available_models:
                if target in model_path:
                    return model_path
        return available_models[0] # 아무거나 되는 거 첫 번째꺼
    except Exception as e:
        # 목록 가져오기 실패 시 가장 표준적인 이름 반환
        return "gemini-1.5-flash"

# --- 4. 영어 발음 듣기 기능 ---
def play_eng_audio(text):
    # 영어만 남기기
    clean_text = re.sub(r'[^a-zA-Z\s]', '', text).strip()
    if clean_text:
        tts = gTTS(text=clean_text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3')

# --- 5. UI 메인 섹션 ---
st.title("🐥 2학년 공부 짝꿍")

# AI 초기화
model_path = initialize_ai()

with st.container():
    subject = st.selectbox("어떤 공부인가요?", ["영어", "수학", "국어", "기타"], index=0)
    uploaded_file = st.file_uploader("📸 사진을 보여줄래요?", type=["jpg", "png", "jpeg"])
    user_question = st.text_input("궁금한 걸 적어주세요!", placeholder="예: apple이 뭐야?")

    # 2학년 맞춤형 시스템 프롬프트 (가독성 명령 강화)
    system_instruction = f"""
    당신은 초등학교 2학년 아이들의 '친절한 짝꿍'입니다.
    
    [필수 규칙]
    1. 모든 답변은 10자 내외의 아주 짧은 문장으로 쓰세요.
    2. 문장마다 줄바꿈을 3번씩 하세요 (글자 사이를 아주 넓게).
    3. 영어 문장이 나오면 앞뒤에 [ENG]를 꼭 붙이세요. (예: [ENG]Apple[/ENG])
    4. "~해요", "~란다" 처럼 다정하게 말하세요.
    """

if st.button("짝꿍아 알려줘! 🚀", use_container_width=True):
    if user_question or uploaded_file:
        try:
            with st.spinner("짝꿍이 생각 중... 💭"):
                model = genai.GenerativeModel(model_name=model_path, system_instruction=system_instruction)
                
                inputs = []
                if user_question: inputs.append(user_question)
                if uploaded_file: inputs.append(Image.open(uploaded_file))
                
                response = model.generate_content(inputs)
                answer = response.text

            st.balloons()
            
            # --- 결과 화면 ---
            tab1, tab2 = st.tabs(["🎈 짝꿍의 대답", "🔍 엄마/아빠용"])
            
            with tab1:
                # [ENG] 태그를 찾아서 발음 버튼과 함께 출력
                parts = re.split(r'(\[ENG\].*?\[/ENG\])', answer, flags=re.DOTALL)
                
                for part in parts:
                    if part.startswith('[ENG]'):
                        eng_text = part.replace('[ENG]', '').replace('[/ENG]', '')
                        st.markdown(f'<div class="eng-box"><b>🎧 영어 발음 듣기:</b><br>', unsafe_allow_html=True)
                        play_eng_audio(eng_text)
                        st.markdown(f'<span style="font-size: 1.5rem; color: #FFBD45;"><b>{eng_text}</b></span></div>', unsafe_allow_html=True)
                    else:
                        if part.strip():
                            st.markdown(f'<div class="answer-text">{part.strip()}</div>', unsafe_allow_html=True)
            
            with tab2:
                st.write(f"사용된 모델: {model_path}")
                st.code(answer)

        except Exception as e:
            st.error(f"앗! 다시 한 번만 눌러볼래? 💦\n(에러: {str(e)})")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>2학년 친구들을 위해 목소리 내는 AI 짝꿍 ❤️</div>", unsafe_allow_html=True)
