import streamlit as tf
import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="운명의 사다리 타기 챗봇 🪜", page_icon="🪜", layout="centered")
st.title("🪜 운명의 사다리 타기 챗봇")
st.caption("참가자와 항목을 알려주면 사다리 타기 결과를 공정하게 만들어 드립니다!")

# 2. Streamlit Secrets에서 API 키 불러오기 및 클라이언트 초기화
if "GEMINI_API_KEY" not in st.secrets:
    st.error("🚨 Streamlit Secrets에 'GEMINI_API_KEY'가 설정되지 않았습니다. 설정을 확인해주세요.")
    st.stop()

try:
    # google-genai SDK의 새로운 초기화 방식
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"클라이언트 초기화 중 오류가 발생했습니다: {e}")
    st.stop()

# 3. 채팅 기록(Session State) 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "안녕하세요! 사다리 타기 챗봇입니다. 🪜\n"
                       "**'참가자 이름들'**과 **'당첨/벌칙 항목들'**을 말씀해주시면 사다리를 태워 드릴게요!\n\n"
                       "예시) 홍길동, 김철수, 이영희 / 꽝, 커피사기, 치킨사기"
        }
    ]

# 4. 기존 채팅 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 사용자 입력 받기
if user_input := st.chat_input("메시지를 입력하세요... (예: 밥값 내기 사다리 타자!)"):
    
    # 사용자 메시지 화면에 표시 및 세션 저장
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # AI 응답 생성 과정 시각화
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # 대화 맥락 유지를 위해 시스템 프롬프트와 이전 대화 기록 가공
            # gemini-2.5-flash-lite는 텍스트 기반 대화에 매우 빠르고 효율적입니다.
            system_instruction = (
                "너는 친절하고 재치 있는 '사다리 타기 및 조추첨 전문가' 챗봇이야. "
                "사용자가 참가자와 항목(벌칙, 상품 등)을 주면, 무작위로 공정하게 사다리 타기 결과를 매칭해줘. "
                "결과를 보여줄 때는 텍스트로 간단한 사다리 모양(예: |--| )을 그려주거나 시각적으로 재미있게 꾸며서 표현해줘. "
                "만약 입력이 부족하면 어떤 정보가 더 필요한지 친절하게 물어봐줘."
            )
            
            # API 호출에 맞는 형태로 메시지 이력 변환
            contents = []
            for msg in st.session_state.messages:
                # API 규격에 맞게 role 매핑 (assistant -> model)
                role = "model" if msg["role"] == "assistant" else "user"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                ))
            
            # API 호출
            response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                )
            )
            
            # 결과 출력 및 저장
            ai_response = response.text
            message_placeholder.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
        except APIError as ae:
            # 구글 API 관련 에러 처리
            error_msg = f"⚠️ Gemini API 오류가 발생했습니다: {ae.message}"
            message_placeholder.error(error_msg)
        except Exception as e:
            # 기타 일반 에러 처리
            error_msg = f"⚠️ 알 수 없는 오류가 발생했습니다: {str(e)}"
            message_placeholder.error(error_msg)
