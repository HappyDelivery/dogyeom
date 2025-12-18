import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. 페이지 및 기본 설정 ---
st.set_page_config(
    page_title="2학년 공부 짝꿍",
    page_icon="🐥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. Custom CSS (가독성 향상) ---
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
    
    /* 답변 영역 폰트 크기 및 간격 조정 */
    .answer-box {
        line-height: 1.8;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. API Key 및 모델 설정 ---
def configure_genai():
    api_key = None
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    if not api_key:
        with st.sidebar:
            api_key = st.text_input("API Key 입력", type="password")
    if not api_key:
        st.warning("🚨 선생님을 부르려면 열쇠(Key)가 필요해요.")
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

# --- 4. 메인 UI 구성 ---
st.title("🐥 2학년 공부 짝꿍")
st.markdown('<p class="subtitle">한 줄씩 차근차근 설명해 줄게요!<br>궁금한 것을 물어보세요.</p>', unsafe_allow_html=True)

configure_genai()

with st.container():
    subject = st.selectbox(
        "어떤 공부를 하고 있나요? 📚",
        ["수학 (덧셈, 뺄셈, 구구단)", "국어 (받아쓰기, 읽기)", "영어 (ABC, 단어)", "슬기로운 생활", "기타"],
        index=0
    )
    uploaded_file = st.file_uploader("📸 문제 사진을 올려주세요", type=["jpg", "jpeg", "png", "webp"])
    image_display = Image.open(uploaded_file) if uploaded_file else None
    if image_display:
        st.image(image_display, caption="친구의 질문 사진", use_container_width=True)

    user_question = st.text_area("글로 물어봐도 돼요 ✏️", placeholder="예: 구구단 3단이 어려워요!", height=100)

    with st.expander("🔒 설정 메뉴"):
        model_options = get_available_models()
        selected_model = st.selectbox("AI 모델", model_options, index=0)
        temperature = st.slider("창의성", 0.0, 1.0, 0.3)

        # --- [수정 포인트] 개조식 답변 유도를 위한 시스템 프롬프트 ---
        system_prompt = f"""
        당신은 초등학교 2학년 아이들을 위한 '친절한 AI 짝꿍'입니다.
        아이들이 읽기 편하도록 모든 답변을 **개조식(짧은 줄바꿈과 기호 사용)**으로 작성해야 합니다.

        [출력 규칙 - 필독!]
        1. **줄바꿈을 아주 자주 하세요.** 한 문장이 끝나면 무조건 줄을 바꿉니다.
        2. **기호 사용:** 숫자 번호(1., 2.)나 예쁜 기호(✅, ⭐, 📍)를 사용하여 내용을 나누세요.
        3. **강조:** 가장 중요한 단어나 정답은 **굵게(Bold)** 표시하세요.
        4. **간격:** 설명의 묶음 사이에는 빈 줄을 하나 더 넣어서 시원하게 보이게 하세요.

        [과목별 가이드]
        - 수학: 식을 한 줄에 다 쓰지 말고, 한 단계씩 줄을 바꿔서 보여주세요.
        - 영어: 발음은 [대괄호] 안에 한글로 적고, 단어 뜻은 딱 **하나**만 쉽게 알려주세요.
        - 말투: "~해요", "~란다" 등 다정한 말투를 유지하세요.

        [답변 구조 예시]
        칭찬 한마디 🎈
        
        ✅ **정답: 00이에요!**
        
        📍 **풀이 순서:**
        1. 첫 번째는 ~~
        2. 두 번째는 ~~
        
        🌟 **짝꿍의 꿀팁!**
        - ~~하면 더 쉬워요!
        """

# --- 5. 응답 생성 ---
submit_btn = st.button("알려줘! 🚀", use_container_width=True)

if submit_btn:
    if not user_question and not uploaded_file:
        st.warning("질문을 입력해 주세요! 😉")
    else:
        try:
            with st.spinner("짝꿍이 생각 중... ✨"):
                model = genai.GenerativeModel(model_name=selected_model, system_instruction=system_prompt)
                content_input = [user_question] if user_question else []
                if image_display: content_input.append(image_display)
                
                response = model.generate_content(content_input, generation_config=genai.types.GenerationConfig(temperature=temperature))
                result_text = response.text

            st.balloons()
            st.success("대답이 도착했어! 🎉")
            
            tab1, tab2 = st.tabs(["🎈 짝꿍의 설명", "👀 부모님 확인용"])
            
            with tab1:
                # 텍스트를 div로 감싸 스타일 적용
                st.markdown(f'<div class="answer-box">{result_text}</div>', unsafe_allow_html=True)
                st.info("💡 이해가 잘 되었나요? 또 궁금한 게 있으면 물어보세요!")
                
            with tab2:
                st.code(result_text, language='markdown')

        except Exception as e:
            st.error(f"오류가 났어요! 다시 시도해 볼까요? 💦 ({e})")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888; font-size: 0.8rem;'>2학년 친구들을 위한 AI 짝꿍 ❤️</div>", unsafe_allow_html=True)
