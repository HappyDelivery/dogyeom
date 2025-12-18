import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import re

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="도겸이의 학습 도우미",
    page_icon="🐣",
    layout="centered"
)

# --- 2. CSS 스타일 (네이버 사전 + 아이들 맞춤형) ---
st.markdown("""
<style>
    .stApp { background-color: #121212; color: #fff; }
    
    /* 제목 */
    h1 { color: #FFD700 !important; font-family: 'Comic Sans MS', sans-serif; text-align: center; margin-bottom: 10px; }
    
    /* 과목 선택 라디오 버튼 (가로형) */
    .stRadio [role=radiogroup] {
        justify-content: center;
        gap: 10px;
        font-size: 1.2rem;
    }
    
    /* 실행 버튼 */
    .stButton > button {
        width: 100%; border-radius: 15px; font-weight: bold;
        background: linear-gradient(90deg, #03C75A, #02b350);
        color: white; height: 3.5em; font-size: 1.2rem !important; border: none;
        margin-top: 15px;
    }
    
    /* 설명 박스 (채팅 스타일) */
    .chat-box {
        background-color: #2b2b2b;
        color: #e0e0e0;
        padding: 25px;
        border-radius: 20px;
        line-height: 2.0;
        font-size: 1.3rem;
        margin-bottom: 20px;
        border-left: 5px solid #FFD700;
    }
    
    /* [영어 전용] 사전 카드 */
    .dic-card {
        background-color: #1e1e1e;
        border: 2px solid #03C75A;
        border-radius: 15px;
        padding: 25px;
        margin-top: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .dic-title { font-size: 0.9rem; color: #03C75A; margin-bottom: 5px; font-weight: bold; }
    .dic-english { font-size: 2.2rem; font-weight: bold; color: #fff; margin-bottom: 5px; }
    .dic-pronoun { font-size: 1.1rem; color: #aaa; margin-bottom: 15px; }
    .dic-meaning { font-size: 1.5rem; font-weight: bold; color: #FFD700; border-top: 1px solid #444; padding-top: 15px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. 모델 연결 함수 (안정성 강화) ---
def get_model_response(prompt, inputs):
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        return None, "API 키가 없습니다. Secrets 설정을 확인해주세요."
    
    genai.configure(api_key=api_key)
    
    # 연결 가능한 모델을 순서대로 시도
    candidates = [
        "gemini-1.5-flash", 
        "gemini-pro", 
        "models/gemini-1.5-flash", 
        "gemini-1.0-pro"
    ]
    
    last_error = ""
    for model_name in candidates:
        try:
            model = genai.GenerativeModel(model_name)
            # 실제 생성 시도
            response = model.generate_content(inputs)
            return response.text, None # 성공 시 텍스트 반환, 에러는 None
        except Exception as e:
            last_error = str(e)
            continue # 실패하면 다음 모델 시도
            
    return None, f"모든 AI 모델 연결 실패 ({last_error})"

# --- 4. 오디오 생성 ---
def generate_audio(text):
    if not text: return None
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

# --- 5. UI 메인 ---
st.title("🐣 도겸이의 학습 도우미 ✏️")

# 과목 선택 (가로형 버튼으로 변경)
subject = st.radio(
    "어떤 공부를 할까요?",
    ["영어 🅰️", "수학 🔢", "국어 📖", "기타 🌈"],
    horizontal=True, # 가로로 배치
    index=1 # 기본값 수학으로 설정
)

with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        user_question = st.text_input("궁금한 내용을 적어봐!", placeholder="예: 135*125 계산해줘")
    with col2:
        uploaded_file = st.file_uploader("📷", type=["jpg", "png"], label_visibility="collapsed")

    # --- 프롬프트 설정 ---
    base_prompt = """
    당신은 초등학교 2학년 '도겸'이의 다정한 AI 튜터입니다.
    어려운 단어는 피하고, "~해요", "~란다" 처럼 친절하게 설명하세요.
    보기 편하게 줄바꿈을 자주 하세요.
    """
    
    system_instruction = base_prompt
    
    if "영어" in subject:
        system_instruction += """
        [영어 설명 규칙]
        1. 질문에 대해 한국어로 먼저 친절하게 설명하세요.
        2. 마지막에 **핵심 단어나 문장**을 아래 형식으로 만드세요.
        
        ///DIC_START///
        영어문장
        한국어발음
        한국어뜻
        ///DIC_END///
        """
    elif "수학" in subject:
        system_instruction += """
        [수학 설명 규칙]
        1. 정답만 알려주지 말고, **풀이 과정을 단계별로** 보여주세요.
        2. 곱셈 같은 계산은 세로셈 형태로 보여주거나, 숫자를 쪼개서 쉽게 설명하세요.
        3. 예: 135 * 125 라면, 100을 곱하고 20을 곱하고... 하는 식으로요.
        """
    else:
        system_instruction += """
        [설명 규칙]
        1. 재미있는 예시를 들어서 설명하세요.
        2. 이모지를 많이 사용하세요.
        """

# --- 실행 로직 ---
if st.button("도겸이 궁금증 해결! 🔍", use_container_width=True):
    if user_question or uploaded_file:
        with st.spinner("짝꿍이 생각하고 있어요... 🧠"):
            # 입력 데이터 구성 (시스템 프롬프트 + 사용자 입력)
            input_content = [system_instruction]
            if user_question: input_content.append(user_question)
            if uploaded_file: input_content.append(Image.open(uploaded_file))
            
            # 모델 호출 (함수 내부에서 에러 처리)
            response_text, error_msg = get_model_response(system_instruction, input_content)
            
            if error_msg:
                # 에러 발생 시 여기서 종료 (변수 미정의 오류 방지)
                st.error("🚫 문제가 생겼어요.")
                st.info(f"이유: {error_msg}")
            else:
                # 성공 시에만 결과 처리
                explanation = response_text
                card_data = None
                
                # 영어일 경우 사전 데이터 분리
                if "영어" in subject and "///DIC_START///" in response_text:
                    pattern = r"///DIC_START///(.*?)///DIC_END///"
                    match = re.search(pattern, response_text, re.DOTALL)
                    if match:
                        explanation = response_text.replace(match.group(0), "").strip()
                        lines = match.group(1).strip().split('\n')
                        card_data = [line.strip() for line in lines if line.strip()]
                
                # --- 화면 출력 ---
                # 1. 기본 설명
                if explanation:
                    st.markdown(f'<div class="chat-box">{explanation}</div>', unsafe_allow_html=True)
                
                # 2. 영어 사전 카드
                if card_data and len(card_data) >= 3:
                    eng_text = card_data[0]
                    pronoun = card_data[1]
                    meaning = card_data[2]
                    
                    st.markdown(f"""
                    <div class="dic-card">
                        <div class="dic-title">Today's English</div>
                        <div class="dic-english">{eng_text}</div>
                        <div class="dic-pronoun">[{pronoun}]</div>
                    """, unsafe_allow_html=True)
                    
                    audio_fp = generate_audio(eng_text)
                    if audio_fp:
                        st.audio(audio_fp, format='audio/mp3')
                    
                    st.markdown(f"""
                        <div class="dic-meaning">{meaning}</div>
                    </div>
                    """, unsafe_allow_html=True)

    else:
        st.warning("질문을 입력하거나 사진을 올려주세요!")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #555;'>도겸이를 위한 AI 단짝 친구 🐣</div>", unsafe_allow_html=True)
