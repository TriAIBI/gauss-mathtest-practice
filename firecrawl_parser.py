# firecrawl_parser.py

import re
from typing import List, Dict, TypedDict
import json


class Question(TypedDict):
    id: str
    text: str
    choices: List[str]
    correct: str
    year: int
    grade: int


def parse_questions_from_firecrawl(
    fc_json: Dict,
    year: int,
    grade: int,
) -> List[Question]:
    """
    Firecrawl로 얻은 contest 페이지 JSON(fc_json)에서
    문제문 + 선택지를 찾아 Question 리스트로 만든다.

    전제:
    - blocks: [ {type: "paragraph"/"heading"/"list", ...}, ... ]
    - 문제문: paragraph (또는 heading+paragraph 조합)
    - 선택지: list.items 5개
    """
    blocks = fc_json.get("blocks", [])
    questions: List[Question] = []

    current_stem_lines: List[str] = []
    q_index = 1

    for block in blocks:
        btype = block.get("type")

        if btype in ("heading", "paragraph"):
            text = block.get("text", "").strip()
            if not text:
                continue

            # Part A/B/C 같은 헤딩은 무시, 문제문만 누적
            # 예: "Part A: ..." 는 건너뛰고, 그 아래 paragraph부터 문제문으로
            if text.startswith("Part A") or text.startswith("Part B") or text.startswith("Part C"):
                # 파트 헤딩이면, 지금까지 누적된 stem은 폐기
                current_stem_lines = []
                continue

            # 일반 문단이면 현재 문제문의 일부로 누적
            current_stem_lines.append(text)

        elif btype == "list":
            items = block.get("items", [])
            # 선택지 5개 이상인 리스트를 만나면, 지금까지 누적된 stem을 문제로 보고 Question 생성
            if len(items) >= 3:
                if not current_stem_lines:
                    # stem 없이 list만 나오면 스킵
                    continue

                stem_text = " ".join(current_stem_lines).strip()
                # 선택지 앞에 A)~E) 레이블 붙이기
                labels = ["A", "B", "C", "D", "E"]
                choices = []
                for idx, choice_text in enumerate(items[:5]):
                    # Firecrawl이 text 필드를 사용한다면: choice_text = item["text"]
                    choices.append(f"{labels[idx]}) {choice_text}")

                qid = f"{year}-G{grade}-Q{q_index}"
                questions.append(
                    Question(
                        id=qid,
                        text=stem_text,
                        choices=choices,
                        correct="",  # 나중에 solutions에서 채움
                        year=year,
                        grade=grade,
                    )
                )
                q_index += 1
                current_stem_lines = []  # 다음 문제를 위해 초기화

        # 다른 타입(code, image 등)은 무시
        else:
            continue

    return questions


def parse_answers_from_firecrawl(fc_json: Dict) -> Dict[str, str]:
    """
    Firecrawl로 얻은 solution 페이지 JSON에서
    각 문항의 정답(A~E)을 추출해 {"Q1": "C", ...} 형태로 반환.
    """
    blocks = fc_json.get("blocks", [])
    # 전체 텍스트 합치기
    texts = []
    for b in blocks:
        t = b.get("text", "")
        if t:
            texts.append(t)
    full_text = "\n".join(texts)

    answers: Dict[str, str] = {}

    # 예: "1. C", "1) C", "1. (C)" 등 다양한 패턴이 있을 수 있으므로 조금 넓게
    pattern = r"(\d+)\s*[\.\)]\s*\(?([A-E])\)?"
    for m in re.finditer(pattern, full_text):
        qnum = m.group(1)  # "1"
        letter = m.group(2)  # "C"
        answers[f"Q{qnum}"] = letter

    return answers



def merge_questions_answers(
    questions: List[Question],
    answers: Dict[str, str],
) -> List[Question]:
    merged: List[Question] = []
    for q in questions:
        qid = q["id"]  # 예: "2025-G7-Q1"
        qnum = qid.split("-")[-1]  # "Q1"
        correct = answers.get(qnum, "")
        merged.append(
            Question(
                id=q["id"],
                text=q["text"],
                choices=q["choices"],
                correct=correct,
                year=q["year"],
                grade=q["grade"],
            )
        )
    return merged


def save_questions_to_json(questions: List[Question], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)


def main():
    # 1) Firecrawl로 미리 생성해 둔 JSON 파일 읽기 (contest, solution)
    with open("firecrawl_gauss7_2025_contest.json", "r", encoding="utf-8") as f:
        fc_g7_contest = json.load(f)

    with open("firecrawl_gauss_2025_solution.json", "r", encoding="utf-8") as f:
        fc_solution = json.load(f)

    # 2) 문제 파싱
    g7_questions = parse_questions_from_firecrawl(fc_g7_contest, year=2025, grade=7)

    # 3) 정답 파싱
    answers = parse_answers_from_firecrawl(fc_solution)

    # 4) 병합
    g7_merged = merge_questions_answers(g7_questions, answers)

    # 5) JSON 저장
    save_questions_to_json(g7_merged, "gauss_2025_g7.json")

    print(f"saved {len(g7_merged)} questions to gauss_2025_g7.json")


if __name__ == "__main__":
    main()       