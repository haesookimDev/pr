import os
import subprocess
from openai import OpenAI
from dotenv import load_dotenv
import argparse

# .env 파일에서 환경 변수 로드
load_dotenv()

def get_git_info(base_branch: str) -> dict:
    """Git 저장소에서 PR 메시지 생성에 필요한 정보를 수집합니다."""
    try:
        # 1. 현재 브랜치 이름 가져오기
        branch_name = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, check=True
        ).stdout.strip()

        # 2. 베이스 브랜치와의 커밋 로그 가져오기
        commit_logs = subprocess.run(
            ['git', 'log', f'{base_branch}..HEAD', '--oneline', '--pretty=format:%s'],
            capture_output=True, text=True, check=True
        ).stdout.strip()

        # 3. 베이스 브랜치와의 코드 변경 사항(diff) 가져오기
        code_diff = subprocess.run(
            ['git', 'diff', f'{base_branch}...HEAD'],
            capture_output=True, text=True, check=True
        ).stdout

        return {
            "branch_name": branch_name,
            "commit_logs": commit_logs,
            "code_diff": code_diff
        }
    except subprocess.CalledProcessError as e:
        print(f"Git 명령어 실행 중 오류가 발생했습니다: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Git이 설치되어 있지 않거나 경로에 없습니다. Git을 설치해주세요.")
        return None


def generate_pr_message(git_info: dict) -> str:
    """OPENAI API를 사용하여 PR 메시지를 생성합니다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "오류: GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요."

    client = OpenAI(api_key=api_key)

    # LLM에게 전달할 프롬프트
    prompt = f"""
        당신은 뛰어난 개발자로, Git 변경사항을 보고 명확하고 간결한 GitHub Pull Request 메시지를 한국어로 작성하는 전문가입니다.

        아래 제공되는 브랜치 이름, 커밋 로그, 그리고 코드 변경사항(diff)을 바탕으로 다음 형식에 맞춰 PR 메시지를 생성해주세요.

        **형식:**
        ### 제목
        [기능/수정] 한 줄로 핵심 변경 내용 요약

        ### 설명
        - 이 PR이 필요한 이유와 배경을 설명해주세요.
        - 어떤 문제를 해결하는지 작성해주세요.

        ### 주요 변경 사항
        - 코드 변경 사항을 구체적인 항목으로 나눠서 요약해주세요.

        ---

        **[입력 정보]**
        **브랜치 이름:**
        {git_info['branch_name']}

        **커밋 로그:**
        ```
        {git_info['commit_logs']}
        ```

        **코드 변경 사항(diff):**
        ```diff
        {git_info['code_diff']}
        ```
    """

    try:
        response = client.chat.completions.create(model='gpt-4.1-mini', messages=[{'role':'user', 'content':prompt}])
        return response.choices[0].message.content
    except Exception as e:
        return f"Gemini API 호출 중 오류가 발생했습니다: {e}"


if __name__ == "__main__":
    # PR을 보낼 대상 브랜치 (e.g., 'main', 'develop')
    parser = argparse.ArgumentParser(
        description="Git 변경사항을 기반으로 PR 메시지를 자동으로 생성합니다."
    )
    
    # 3. 'base_branch' 인자 추가. 위치 기반 인자이며, 필수가 아님(nargs='?').
    parser.add_argument(
        'base_branch', 
        type=str, 
        nargs='?',
        default='main', # 인자가 없으면 'main'을 기본값으로 사용
        help="비교의 기준이 될 베이스 브랜치 이름 (기본값: main)"
    )
    args = parser.parse_args()
    BASE_BRANCH = args.base_branch

    print(f"✅ 기준 브랜치: '{BASE_BRANCH}'")
    
    print("Git 정보를 수집 중입니다...")
    git_info = get_git_info(BASE_BRANCH)

    if git_info:
        # 정보가 너무 길 경우 일부만 표시
        print(f"브랜치: {git_info['branch_name']}")
        print(f"커밋 수: {len(git_info['commit_logs'].splitlines())}개")
        print("\nOPENAI API를 통해 PR 메시지를 생성합니다...")
        
        pr_message = generate_pr_message(git_info)
        
        print("\n" + "="*50)
        print("✨ 생성된 PR 메시지 ✨")
        print("="*50)
        print(pr_message)
        print("="*50)