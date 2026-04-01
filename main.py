from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Optional


class Question(TypedDict):
    id: str
    text: str
    choices: List[str]
    correct: str
    year: int
    grade: int


class GaussState(TypedDict, total=False):
    grade: int
    problem_bank: List[Question]
    current_question: Optional[Question]
    answered_count: int
    correct_count: int
    score: int
    last_answer: Optional[str]
    step: str  # "init" | "load" | "select" | "check" | "idle" | "done"


# ========== Tools ==========

def load_problems_from_past_contests(grade: int) -> List[Question]:
    dummy_questions: List[Question] = [
        {
            "id": "2024-G7-Q1",
            "text": "What is 2 + 3?",
            "choices": ["A) 4", "B) 5", "C) 6", "D) 7", "E) 8"],
            "correct": "B",
            "year": 2024,
            "grade": grade,
        },
        {
            "id": "2024-G7-Q2",
            "text": "What is 10 - 4?",
            "choices": ["A) 5", "B) 6", "C) 7", "D) 8", "E) 9"],
            "correct": "B",
            "year": 2024,
            "grade": grade,
        },
        {
            "id": "2024-G7-Q3",
            "text": "What is 5 × 6?",
            "choices": ["A) 25", "B) 30", "C) 35", "D) 40", "E) 45"],
            "correct": "B",
            "year": 2024,
            "grade": grade,
        },
          {
            "id": "2025-G7-04",
            "text": "If each of 12 friends gives $5, in total how much do they give to the charity?",
            "choices": ["$17", "$50", "$60", "$70", "$125"],
            "correct": "C",
            "year": 2025,
            "grade": grade
        },
        {
            "id": "2025-G7-05",
            "text": "A regular hexagon is divided into 6 triangles having equal area. If 1 of these triangles is shaded, what fraction of the area of the hexagon is shaded?",
            "choices": ["1/2", "1/3", "1/4", "1/5", "1/6"],
            "correct": "E",
            "year": 2025,
            "grade": grade
        },
        {
            "id": "2025-G8-09",
            "text": "If June 1 is a Tuesday, what day of the week is June 30?",
            "choices": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "correct": "C",
            "year": 2025,
            "grade": grade
        }
    ]
    return dummy_questions


# ========== Node Functions (항상 한 step만) ==========

def init_session(state: GaussState) -> GaussState:
    """세션 초기화"""
    grade = state.get("grade", 7)
    return {
        "grade": grade,
        "problem_bank": [],
        "current_question": None,
        "answered_count": 0,
        "correct_count": 0,
        "score": 0,
        "last_answer": None,
        "step": "load",
    }


def load_past_contests_node(state: GaussState) -> GaussState:
    """문제 은행 로드"""
    grade = state["grade"]
    problems = load_problems_from_past_contests(grade)
    return {
        **state,
        "problem_bank": problems,
        "step": "select",
    }


def select_question(state: GaussState) -> GaussState:
    """다음 문제 선택"""
    idx = state.get("answered_count", 0)
    bank = state.get("problem_bank", [])

    if idx < len(bank):
        q = bank[idx]
        next_step = "idle"  # UI에서 답 기다리는 상태
    else:
        q = None
        next_step = "done"

    return {
        **state,
        "current_question": q,
        "step": next_step,
    }


def check_answer(state: GaussState) -> GaussState:
    """정답 확인"""
    q = state.get("current_question")
    last = state.get("last_answer")

    if not q or not last:
        # 이상 상태면 그대로 idle로
        return {
            **state,
            "step": "idle",
        }

    correct = q["correct"]
    is_correct = (last == correct)

    answered = state.get("answered_count", 0) + 1
    correct_cnt = state.get("correct_count", 0) + (1 if is_correct else 0)
    score = state.get("score", 0) + (10 if is_correct else 0)

    bank = state.get("problem_bank", [])
    has_more = answered < len(bank)

    return {
        **state,
        "answered_count": answered,
        "correct_count": correct_cnt,
        "score": score,
        "current_question": None,
        "last_answer": None,
        "step": "select" if has_more else "done",
    }


# ========== Routing ==========

def route_from_start(state: GaussState):
    step = state.get("step", "init")
    if step == "init":
        return "init_session"
    if step == "load":
        return "load_past_contests"
    if step == "select":
        return "select_question"
    if step == "check":
        return "check_answer"
    # idle/done -> 할 거 없음
    return END


graph_builder = StateGraph(GaussState)

graph_builder.add_node("init_session", init_session)
graph_builder.add_node("load_past_contests", load_past_contests_node)
graph_builder.add_node("select_question", select_question)
graph_builder.add_node("check_answer", check_answer)

graph_builder.add_conditional_edges(
    START,
    route_from_start,
    {
        "init_session": "init_session",
        "load_past_contests": "load_past_contests",
        "select_question": "select_question",
        "check_answer": "check_answer",
        END: END,
    },
)

# 각 노드는 자기 일만 하고 END로
graph_builder.add_edge("init_session", END)
graph_builder.add_edge("load_past_contests", END)
graph_builder.add_edge("select_question", END)
graph_builder.add_edge("check_answer", END)

graph = graph_builder.compile()