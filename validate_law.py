#!/usr/bin/env python3
"""
법령 데이터 검증 테스트
"""

import json
from pathlib import Path
from src.core.rule_validator import RuleValidator

def main():
    # 검증기 초기화
    validator = RuleValidator()
    
    # 실제 law.json 파일 로드
    law_file = Path("check/law.json")
    
    if not law_file.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {law_file}")
        return
    
    with open(law_file, 'r', encoding='utf-8') as f:
        law_data = json.load(f)
    
    # 규칙 검증 실행
    print(f"\n=== {law_file.name} 검증 결과 ===")
    print(f"총 요소 수: {len(law_data.get('elements', []))}개")
    
    issues = validator.validate_all_rules(law_data, str(law_file))
    
    # 결과 출력
    if issues:
        print(f"\n발견된 이슈: {len(issues)}개")
        
        # 규칙별로 분류
        rule_groups = {}
        for issue in issues:
            rule_id = issue.rule_id
            if rule_id not in rule_groups:
                rule_groups[rule_id] = []
            rule_groups[rule_id].append(issue)
        
        for rule_id, rule_issues in rule_groups.items():
            print(f"\n📋 {rule_id} 규칙: {len(rule_issues)}개 이슈")
            for issue in rule_issues[:5]:  # 처음 5개만 표시
                print(f"  {issue}")
            if len(rule_issues) > 5:
                print(f"  ... 외 {len(rule_issues) - 5}개 더")
    else:
        print("✅ 이슈가 발견되지 않았습니다.")

if __name__ == "__main__":
    main()
