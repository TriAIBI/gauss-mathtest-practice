import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict
import re

# URLs
G7_URL = "https://cemc.uwaterloo.ca/sites/default/files/documents/2025/2025Gauss7Contest.html"
G8_URL = "https://cemc.uwaterloo.ca/sites/default/files/documents/2025/2025Gauss8Contest.html"
SOL_URL = "https://cemc.uwaterloo.ca/sites/default/files/documents/2025/2025GaussSolution.html"

def debug_preview(html: str):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    with open("gauss_2025_g7_raw.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Saved gauss_2025_g7_raw.txt")

def fetch_html(url: str) -> str:
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text



def parse_contest_questions(html: str, grade: int) -> List[Dict]:
    """
    2025 Gauss Grade 7/8 Contest HTML 전체 텍스트에서
    Q1~Q25 문제문과 선택지를 파싱해서 Question 리스트로 만든다.

    - text: '번호. ... 선택지들 ...' 중, 선택지 앞까지
    - choices: 'A) ...' ~ 'E) ...'
    - correct: 빈 문자열 (나중에 solutions에서 채움)
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    full_text = soup.get_text("\n", strip=True)

    # Part A/B/C 이후의 문제들만 대상으로 하기 위해 'Part A:'부터 끝까지 자름
    m = re.search(r"Part A: Each correct answer is worth 5\.", full_text)
    if m:
        full_text = full_text[m.start():]

    # 패턴:
    # *   1.
    #     문제문 ...
    #     *   (  A  ) 선택지1
    #     *   (  B  ) 선택지2
    #     ...
    # 이런 식이라, 텍스트 기반으로
    # "번호.\n... A) ...\n... B) ...\n... E) ..." 을 잡는 전략을 사용.
    #
    # 우선, 줄 단위로 나눔
    lines = full_text.splitlines()

    questions: List[Dict] = []
    i = 0
    q_index = 1

    while i < len(lines) and q_index <= 25:
        line = lines[i].strip()
        # "1." / "2." 처럼 번호 줄 찾기
        if re.fullmatch(rf"{q_index}\.", line):
            # 문제 시작
            qnum = q_index
            q_lines = []
            choices = []

            i += 1
            # 문제문을 읽다가 선택지 패턴을 만나면 choices 수집으로 전환
            # 선택지 줄은 대략 "(  A  ) ..." 형태의 줄이거나,
            # "A" 단독 줄 뒤에 텍스트가 나오는 등 다양한 변형이 있을 수 있어
            # 여기서는 가장 단순한 "(  A  )" 형태를 중심으로 처리.
            while i < len(lines):
                l = lines[i].strip()

                # 선택지 시작 패턴: "(  A  )" 또는 "A)" 류
                m_choice = re.match(r"\(\s*([A-E])\s*\)", l)
                if m_choice:
                    # 이 줄 또는 다음 줄에 choice 텍스트가 있을 수 있음
                    label = m_choice.group(1)
                    choice_text = l[m_choice.end():].strip()
                    # 만약 바로 뒤에 텍스트가 없으면, 다음 줄을 choice 텍스트로 사용
                    if not choice_text and i + 1 < len(lines):
                        i += 1
                        choice_text = lines[i].strip()
                    choices.append(f"{label}) {choice_text}")
                    i += 1
                    # 이후 줄들에서 B~E까지 같은 방식으로 수집
                    while len(choices) < 5 and i < len(lines):
                        l2 = lines[i].strip()
                        m2 = re.match(r"\(\s*([A-E])\s*\)", l2)
                        if not m2:
                            i += 1
                            continue
                        label2 = m2.group(1)
                        text2 = l2[m2.end():].strip()
                        if not text2 and i + 1 < len(lines):
                            i += 1
                            text2 = lines[i].strip()
                        choices.append(f"{label2}) {text2}")
                        i += 1
                    break
                else:
                    # 아직 선택지 시작 전이면 문제문에 포함
                    q_lines.append(l)
                    i += 1

            # 문제문 합치기
            q_text = " ".join(q_lines).strip()

            questions.append(
                {
                    "id": f"2025-G{grade}-Q{qnum}",
                    "text": q_text,
                    "choices": choices,
                    "correct": "",  # 나중에 solutions에서 채움
                    "year": 2025,
                    "grade": grade,
                }
            )

            q_index += 1
        else:
            i += 1

    return questions


def parse_solutions(html: str) -> Dict[str, str]:
    """
    Solutions HTML에서 각 문항의 정답 (A~E)을 추출.
    예: '1. (C)', '2. (B)' 형식 등을 기반으로 파싱.
    반환: {"Q1": "C", "Q2": "B", ...}
    """
    soup = BeautifulSoup(html, "html.parser")
    answers: Dict[str, str] = {}

    # 실제 문서에서는 보통 'Answers' 섹션에
    # '1. (C)  2. (B) ...' 같은 형식으로 나옵니다.
    # 그 부분을 찾은 뒤, 숫자와 괄호 속 문자를 정규식으로 뽑아내면 됩니다.

    import re

    # 텍스트 전체에서 '1. (C)' 같은 패턴 찾기 (예시)
    text = soup.get_text(" ", strip=True)
    # 예: 1. (C) 2. (B) ... 형태 가정
    pattern = r"(\d+)\.\s*\(([A-E])\)"
    for match in re.finditer(pattern, text):
        q_num = match.group(1)
        ans = match.group(2)
        answers[f"Q{q_num}"] = ans

    return answers


def merge_questions_and_answers(
    questions: List[Dict],
    answers: Dict[str, str],
    grade: int,
) -> List[Dict]:
    merged: List[Dict] = []
    for q in questions:
        # q["id"] = "2025-G7-Q1" 형태라고 가정
        # 문제번호만 빼서 answers["Q1"]를 찾는다.
        qid: str = q["id"]
        # 마지막 "-Q숫자" 부분 추출
        qnum = qid.split("-")[-1]  # "Q1"
        correct = answers.get(qnum, "")
        merged.append(
            {
                **q,
                "correct": correct,
            }
        )
    return merged


def main():
    # 1) HTML 가져오기
    g7_html = fetch_html(G7_URL)
    g8_html = fetch_html(G8_URL)
    sol_html = fetch_html(SOL_URL)

    # 2) 문제 파싱 (HTML 구조에 맞게 parse_contest_questions 구현 필요)
    g7_questions = parse_contest_questions(g7_html, grade=7)
    g8_questions = parse_contest_questions(g8_html, grade=8)

    # 3) 정답 파싱
    answers = parse_solutions(sol_html)

    # 4) 정답 병합
    g7_merged = merge_questions_and_answers(g7_questions, answers, grade=7)
    g8_merged = merge_questions_and_answers(g8_questions, answers, grade=8)

    # 5) JSON으로 저장
    with open("gauss_2025_g7.json", "w", encoding="utf-8") as f:
        json.dump(g7_merged, f, ensure_ascii=False, indent=2)

    with open("gauss_2025_g8.json", "w", encoding="utf-8") as f:
        json.dump(g8_merged, f, ensure_ascii=False, indent=2)

    print("Saved gauss_2025_g7.json and gauss_2025_g8.json")


    debug_preview(g7_html)
    
if __name__ == "__main__":
    main()