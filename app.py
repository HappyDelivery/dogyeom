import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io

# --- 1. 페이지 및 기본 설정 ---
st.set_page_config(
    page_title="2학년 공부 짝꿍",
    page_icon="🐥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. Custom CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    .stButton > button {
        width: 100%; border-radius: 20px; height: 3.5em;
        font-size: 1.2rem !important; font-weight: bold;
        background-color: #FFBD45; color: black; border: none;
    }
    h1 { font-size: 1.8rem !important; text-align: center; color: #FFBD45 !important; }
    .subtitle { text-align: center; color: #ddd; font-size: 1.0rem; margin-bottom: 2rem; }
    .answer-box { line-height: 1.8; font-size: 1.1rem; padding: 10px; }
    
    /* 오디오 플레이어 스타일 */
    audio { width: 100%; margin-top: 10px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- [신규] 3. 음성 생성 함수 (TTS) ---
def text_to_speech(text):
    # 한국어와 영어를 섞어서 읽어줍니다.
    tts = gTTS(text=text, lang='ko')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp

# --- 4. API Key 및 모델 설정 ---
def configure_genai():
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        with st.sidebar:
            api_key = st.text_input("API Key 입력", type="password")
    if not api_key:
        st.warning("🚨 열쇠(Key)를 먼저 입력해 주세요.")
        st.stop()
    genai.configure(api_key=api_key)
    return True

def get_available_models():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        models.sort(key=lambda x: 'flash' not in x)
        return models
    except:
        return ["models/gemini-1.5-flash"]

# --- 5. 메인 UI 구성 ---
st.title("🐥 2학년 공부 짝꿍")
st.markdown('<p class="subtitle">설명을 귀로도 들을 수 있어요!<br>궁금한 것을 물어보세요.</p>', unsafe_allow_html=True)

configure_genai()

with st.container():
    subject = st.selectbox(
        "어떤 공부를 하고 있나요? 📚",
        ["영어 (ABC, 단어)", "수학 (덧셈, 뺄셈, 구구단)", "국어 (받아쓰기, 읽기)", "슬기로운 생활", "기타"],
        index=0
    )
    uploaded_file = st.file_uploader("📸 문제 사진을 올려주세요", type=["jpg", "jpeg", "png", "webp"])
    image_display = Image.open(uploaded_file) if uploaded_file else None
    if image_display:
        st.image(image_display, caption="친구의 질문 사진", use_container_width=True)

    user_question = st.text_area("글로 물어봐도 돼요 ✏️", placeholder="예: Apple이 무슨 뜻이야?", height=100)

    with st.expander("🔒 설정 메뉴"):
        model_options = get_available_models()
        selected_model = st.selectbox("AI 모델", model_options, index=0)
        temperature = st.slider("창의성", 0.0, 1.0, 0.3)

        system_prompt = f"""
        당신은 초등학교 2학년 아이들을 위한 '친절한 AI 짝꿍'입니다.
        
        [출력 규칙]
        1. 개조식(짧은 줄바꿈과 기호 사용)으로 답변하세요.
        2. 영어 단어나 문장이 나오면 반드시 한글로 발음을 적어주세요. 예: Apple [애-플]
        3. 소리 내어 읽어줄 것이므로 너무 복잡한 기호는 피하세요.
        """

# --- 6. 응답 생성 및 음성 출력 ---
submit_btn = st.button("알려줘! 🚀", use_container_width=True)

if submit_btn:
    if not user_question and not uploaded_file:
        st.warning("질문을 입력해 주세요! 😉")
    else:
        try:
            with st.spinner("짝꿍이 생각하고 목소리를 준비 중... ✨"):
                model = genai.GenerativeModel(model_name=selected_model, system_instruction=system_prompt)
                content_input = [user_question] if user_question else []
                if image_display: content_input.append(image_display)
                
                response = model.generate_content(content_input)
                result_text = response.text
                
                # 음성 데이터 생성
                audio_fp = text_to_speech(result_text)

            st.balloons()
            
            tab1, tab2 = st.tabs(["🎈 짝꿍의 설명 듣기", "👀 눈으로 보기"])
            
            with tab1:
                st.success("스피커를 켜보세요! 🎧")
                # 오디오 플레이어 자동 표시
                st.audio(audio_fp, format='audio/mp3')
                st.markdown(f'<div class="answer-box">{result_text}</div>', unsafe_allow_html=True)
                
            with tab2:
                st.code(result_text, language='markdown')

        except Exception as e:
            st.error(f"오류가 났어요! 💦 ({e})")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888; font-size: 0.8rem;'>2학년 친구들을 위한 목소리 내는 AI 짝꿍 ❤️</div>", unsafe_allow_html=True)
