#!/usr/bin/env python3
"""
R004 규칙 테스트 - 한글 인코딩 오류 검출
"""

from backend.src.core.rule_validator import RuleValidator

def test_r004_rule():
    """R004 규칙 테스트"""
    
    # 테스트 데이터 - 한글 깨짐과 잘못된 인식 사례들
    test_data = {
        "elements": [
            {
                "id": "test1",
                "content": {"text": "경제헙력개발구(GOEECCD0)"},  # 한글 깨짐 패턴
                "category": {"label": "ParaText"}
            },
            {
                "id": "test2", 
                "content": {"text": "ABCDEF1234"},  # 연속 대문자 패턴
                "category": {"label": "ParaText"}
            },
            {
                "id": "test3",
                "content": {"text": "정상적인 한글 텍스트입니다"},  # 정상 텍스트
                "category": {"label": "ParaText"}
            },
            {
                "id": "test4",
                "content": {"text": "bcdfghjklmnp"},  # 자음이 많은 의심스러운 영어
                "category": {"label": "ParaText"}
            },
            {
                "id": "test5",
                "content": {"text": "SomethingWrongCD0"},  # CD 패턴
                "category": {"label": "ParaText"}
            },
            {
                "id": "test6",
                "content": {"text": "TestEEPattern"},  # EE 패턴
                "category": {"label": "ParaText"}
            }
        ]
    }
    
    validator = RuleValidator()
    issues = validator.validate_all_rules(test_data, "test_r004.json")
    
    print("🔍 R004 규칙 테스트 결과")
    print(f"총 {len(issues)}개 이슈 발견\n")
    
    r004_issues = [issue for issue in issues if issue.issue_id.startswith('R004')]
    
    print(f"R004 관련 이슈: {len(r004_issues)}개")
    for issue in r004_issues:
        print(f"  - {issue.issue_id}: {issue.description}")
        print(f"    요소 ID: {issue.element_id}")
        print(f"    문제 텍스트: {issue.current_value}")
        print()

if __name__ == "__main__":
    test_r004_rule()
