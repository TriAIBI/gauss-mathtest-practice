import streamlit as st
from main import GaussState, graph

st.set_page_config(page_title="📚 Gauss Math Practice", layout="centered")
st.title("📚 Gauss 수학 문제 풀이")

# Session State 초기화
if "state" not in st.session_state:
    st.session_state.state = {
        "grade": 7,
        "problem_bank": [],
        "current_question": None,
        "answered_count": 0,
        "correct_count": 0,
        "score": 0,
        "last_answer": None,
        "step": "idle",
    }

if "session_started" not in st.session_state:
    st.session_state.session_started = False

if "feedback" not in st.session_state:
    st.session_state.feedback = None

# 사이드바
with st.sidebar:
    st.header("⚙️ 설정")
    grade = st.radio(
        "학년 선택", [7, 8],
        index=0 if st.session_state.state.get("grade", 7) == 7 else 1
    )

    if st.button("⏹️ stop", use_container_width=True):
        st.session_state.state["step"] = "done"
        st.session_state.session_started = False
        st.session_state.feedback = "⏹️ 사용자가 stop을 눌러 세션을 종료했습니다."
        st.rerun()

# 🚀 새 세션 시작
if st.button("🚀 새 세션 시작", use_container_width=True):
    state: GaussState = {
        "grade": grade,
        "problem_bank": [],
        "current_question": None,
        "answered_count": 0,
        "correct_count": 0,
        "score": 0,
        "last_answer": None,
        "step": "init",
    }
    # init
    state = graph.invoke(state, config={"recursion_limit": 10})
    # load
    state["step"] = "load"
    state = graph.invoke(state, config={"recursion_limit": 10})
    # select (첫 문제)
    state["step"] = "select"
    state = graph.invoke(state, config={"recursion_limit": 10})

    st.session_state.state = state
    st.session_state.session_started = True
    st.session_state.feedback = None
    st.rerun()

# ========= 메인 영역 =========
state: GaussState = st.session_state.state
step = state.get("step", "idle")
bank = state.get("problem_bank", [])
answered = state.get("answered_count", 0)
total = len(bank)

if step == "done" or not st.session_state.session_started:
    # 세션 종료 또는 아직 시작 안 함
    if total > 0 and answered >= total:
        # 모든 문제를 다 푼 상태라면 요약 출력
        st.balloons()
        st.markdown("## 🎉 모든 문제를 풀었습니다!")

        col1, col2, col3 = st.columns(3)
        col1.metric("최종 점수", f"{state.get('score', 0)}점")
        col2.metric("정답 수", state.get("correct_count", 0))
        col3.metric("풀이 수", state.get("answered_count", 0))

        correct = state.get("correct_count", 0)
        accuracy = (correct / answered * 100) if answered > 0 else 0.0
        st.markdown(f"### 정답률: {accuracy:.1f}%")

        st.divider()
        if st.button("🔄 다시 시작", use_container_width=True):
            # 세션 상태를 완전히 초기화
            st.session_state.state = {
                "grade": st.session_state.state.get("grade", 7),
                "problem_bank": [],
                "current_question": None,
                "answered_count": 0,
                "correct_count": 0,
                "score": 0,
                "last_answer": None,
                "step": "idle",
            }
            st.session_state.session_started = False
            st.session_state.feedback = None
            st.rerun()
    else:
        # 아직 시작 안 했거나, 중간에 stop으로 종료한 경우
        if st.session_state.feedback:
            st.info(st.session_state.feedback)
        else:
            st.info("👈 왼쪽에서 학년을 선택하고 '새 세션 시작'을 눌러주세요.")
else:
    # 아직 진행 중
    if answered < total:
        current_q = bank[answered]

        st.progress(
            (answered / total) if total > 0 else 0.0,
            text=f"문제 {answered + 1} / {total}",
        )

        st.markdown(f"### 문제 {answered + 1}")
        st.markdown(f"**{current_q['text']}**")
        st.divider()

        st.markdown("**선택지를 클릭하세요:**")

        col1, col2 = st.columns(2)
        col3, col4, col5 = st.columns([1, 1, 1])

        choices_map = {
            "A": (col1, 0),
            "B": (col2, 1),
            "C": (col3, 2),
            "D": (col4, 3),
            "E": (col5, 4),
        }

        for answer_label, (col, idx) in choices_map.items():
            choice_text = current_q["choices"][idx]

            if col.button(choice_text, key=f"{answered}_{answer_label}", use_container_width=True):
                # LangGraph에 채점 요청
                state["last_answer"] = answer_label
                state["step"] = "check"
                state = graph.invoke(state, config={"recursion_limit": 10})

                # check 결과에 따라 select/done
                if state["step"] == "select":
                    state = graph.invoke(state, config={"recursion_limit": 10})

                st.session_state.state = state

                # 피드백
                is_correct = (answer_label == current_q["correct"])
                if is_correct:
                    st.session_state.feedback = "✅ 정답입니다!"
                else:
                    st.session_state.feedback = (
                        f"❌ 오답입니다. 정답은 **{current_q['correct']}**입니다."
                    )

                st.rerun()

        if st.session_state.feedback:
            st.divider()
            if "✅" in st.session_state.feedback:
                st.success(st.session_state.feedback, icon="✅")
            else:
                st.error(st.session_state.feedback, icon="❌")
    else:
        # 문제 소진되었는데 아직 step이 done으로 안 바뀐 경우
        state["step"] = "done"
        st.session_state.state = state
        st.session_state.session_started = False
        st.rerun()