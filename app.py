import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import re
import time

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="도겸이의 학습 도우미",
    page_icon="🐣",
    layout="centered"
)

# --- 2. CSS 스타일 (채팅풍 설명 + 네이버 사전 스타일) ---
st.markdown("""
<style>
    .stApp { background-color: #121212; color: #fff; }
    
    /* 제목 및 헤더 */
    h1 { color: #FFD700 !important; font-family: 'Comic Sans MS', sans-serif; text-align: center; }
    
    /* 버튼 스타일 */
    .stButton > button {
        width: 100%; border-radius: 12px; font-weight: bold;
        background: linear-gradient(90deg, #03C75A, #02b350); /* 네이버 그린 */
        color: white; height: 3.5em; font-size: 1.2rem !important; border: none;
    }
    
    /* 일반 설명 박스 (채팅 느낌) */
    .chat-box {
        background-color: #2b2b2b;
        color: #e0e0e0;
        padding: 20px;
        border-radius: 15px;
        line-height: 1.8;
        font-size: 1.2rem;
        margin-bottom: 20px;
        border-left: 5px solid #FFD700;
    }
    
    /* [영어 전용] 사전 카드 스타일 */
    .dic-card {
        background-color: #1e1e1e;
        border: 2px solid #03C75A;
        border-radius: 15px;
        padding: 25px;
        margin-top: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .dic-title { font-size: 0.9rem; color: #03C75A; margin-bottom: 5px; font-weight: bold; }
    .dic-english {
        font-size: 2.2rem; font-weight: bold; color: #fff; margin-bottom: 5px;
    }
    .dic-pronoun { font-size: 1.1rem; color: #aaa; margin-bottom: 15px; }
    .dic-meaning {
        font-size: 1.5rem; font-weight: bold; color: #FFD700;
        border-top: 1px solid #444; padding-top: 15px; margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. [핵심] 모델 자동 연결 함수 (순차 시도) ---
def get_working_model():
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("API 키가 없습니다. Secrets 설정을 확인해주세요.")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # 에러 방지를 위해 시도할 모델 이름 목록
    # 404 에러는 보통 접두사(models/) 유무나 버전 차이 때문이므로 여러 개를 다 찔러봅니다.
    candidate_models = [
        "gemini-1.5-flash",          # 최신 (접두사 없음)
        "gemini-1.5-pro",            # 고성능 (접두사 없음)
        "models/gemini-1.5-flash",   # 구버전 호환용
        "gemini-pro"                 # 가장 안정적인 구형
    ]
    
    for model_name in candidate_models:
        try:
            # 연결 테스트: 아주 짧은 생성을 시도해봅니다.
            model = genai.GenerativeModel(model_name)
            model.generate_content("Hi", generation_config={'max_output_tokens': 1})
            return model_name # 성공하면 이 이름 사용
        except:
            continue # 실패하면 다음 이름으로 시도
            
    # 다 실패했을 경우 (API 키 문제일 확률 높음)
    return None

# --- 4. 오디오 생성 함수 ---
def generate_audio(text):
    if not text: return None
    try:
        # 영어가 포함된 텍스트만 읽어주기
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

# --- 5. 메인 UI ---
st.title("🐣 도겸이의 학습 도우미 ✏️")

with st.container():
    # 1. 과목 선택 부활!
    subject = st.selectbox("어떤 공부인가요?", ["영어 🅰️", "수학 🔢", "국어 📖", "과학/사회 🌍"], index=0)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        user_question = st.text_input("궁금한 내용을 적어봐!", placeholder="예: apple이 뭐야? / 구구단 3단 알려줘")
    with col2:
        uploaded_file = st.file_uploader("📷", type=["jpg", "png"], label_visibility="collapsed")

    # --- 프롬프트 생성 로직 ---
    # 기본 프롬프트 (도겸이 페르소나)
    base_prompt = """
    당신은 초등학교 2학년 '도겸'이의 다정한 AI 튜터입니다.
    어려운 단어는 쓰지 말고, "~해요", "~란다" 처럼 친절하게 설명하세요.
    설명은 줄글로 길게 쓰지 말고, 보기 좋게 줄바꿈을 자주 하세요.
    """
    
    # 영어일 때만 '사전 카드' 포맷 요청
    if "영어" in subject:
        system_instruction = base_prompt + """
        [영어 설명 규칙]
        1. 먼저 질문에 대해 한국어로 친절하게 설명해주세요.
        2. 설명이 끝나면, 맨 마지막에 **핵심 단어나 문장**을 아래 형식으로 만들어주세요.
        
        ///DIC_START///
        영어문장
        한국어발음
        한국어뜻
        ///DIC_END///
        """
    else:
        # 다른 과목은 사전 카드 필요 없음
        system_instruction = base_prompt + """
        [설명 규칙]
        1. 수학: 사과, 사탕 같은 물건으로 비유해서 설명하세요.
        2. 국어/기타: 재미있는 예시를 들어주세요.
        3. 이모지를 많이 사용하세요.
        """

if st.button("도겸이 궁금증 해결! 🔍", use_container_width=True):
    if user_question or uploaded_file:
        try:
            with st.spinner("짝꿍이 생각하고 있어요... 🧠"):
                # 1. 작동하는 모델 찾기
                model_name = get_working_model()
                
                if not model_name:
                    st.error("🚫 모든 AI 모델 연결에 실패했어요. (API 키 문제이거나 구글 서버 점검 중)")
                else:
                    # 2. 모델 호출
                    model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)
                    
                    inputs = []
                    if user_question: inputs.append(user_question)
                    if uploaded_file: inputs.append(Image.open(uploaded_file))
                    
                    response = model.generate_content(inputs)
                    full_text = response.text
                    
                    # 3. 데이터 파싱 (영어 사전 카드 분리)
                    explanation = full_text
                    card_data = None
                    
                    # 영어 과목이고, 사전 태그가 있다면 분리
                    if "영어" in subject and "///DIC_START///" in full_text:
                        pattern = r"///DIC_START///(.*?)///DIC_END///"
                        match = re.search(pattern, full_text, re.DOTALL)
                        if match:
                            explanation = full_text.replace(match.group(0), "").strip()
                            lines = match.group(1).strip().split('\n')
                            card_data = [line.strip() for line in lines if line.strip()]

            # --- 결과 출력 화면 ---
            
            # (1) 기본 설명 (채팅 박스)
            if explanation:
                st.markdown(f'<div class="chat-box">{explanation}</div>', unsafe_allow_html=True)
            
            # (2) 영어 사전 카드 (데이터가 있을 때만 등장)
            if card_data and len(card_data) >= 3:
                eng_text = card_data[0]
                pronoun = card_data[1]
                meaning = card_data[2]
                
                # 카드 디자인 출력
                st.markdown(f"""
                <div class="dic-card">
                    <div class="dic-title">Today's English</div>
                    <div class="dic-english">{eng_text}</div>
                    <div class="dic-pronoun">[{pronoun}]</div>
                """, unsafe_allow_html=True)
                
                # 오디오 버튼 (카드 안에 넣기)
                audio_fp = generate_audio(eng_text)
                if audio_fp:
                    st.audio(audio_fp, format='audio/mp3')
                
                st.markdown(f"""
                    <div class="dic-meaning">{meaning}</div>
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            # 429(할당량 초과) 등 에러 처리
            if "429" in str(e):
                st.warning("AI 친구가 너무 많이 말을 해서 잠깐 쉬고 있어요. 1분만 기다려주세요! 😴")
            else:
                st.error("앗! 오류가 났어요. 💦")
                st.caption(f"Error detail: {e}")
    else:
        st.warning("질문을 입력해주세요!")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #555;'>도겸이를 위한 AI 단짝 친구 🐣</div>", unsafe_allow_html=True)
