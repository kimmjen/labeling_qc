# 라벨링 품질 검수 도구

JSON 형식의 라벨링 결과 파일을 검수하고 품질을 개선하는 전문 도구입니다.

## 주요 기능

### 🔍 품질 검증
- **R001**: 빈 텍스트 검증
- **R002**: 라벨 타입 일관성 검증
- **R003**: 제목 패턴 검증
- **R004**: 날짜 형식 검증
- **R005**: 테이블 구조 검증
- **R006**: 순서 일관성 검증
- **R007**: 중복 요소 검증
- **R008**: 금지된 라벨 검증
- **R009**: 특정 텍스트 라벨 검증 ('원문', '번역문', '본문' → ParaText)
- **R010**: 날짜 패턴 라벨 검증

### 🔧 자동 수정
- 라벨 타입 자동 변경
- 불필요한 요소 제거
- 요소 순서 재정렬
- 테이블 구조 최적화

### 📊 품질 보고
- 상세한 이슈 분석
- 수정 전후 비교
- 통계 및 시각화

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. CLI 사용
```bash
# 단일 파일 검수
python cli/cli_tool.py sample.json --validate

# 자동 수정 포함
python cli/cli_tool.py sample.json --fix

# 디렉토리 일괄 검수
python cli/cli_tool.py data_folder/ --validate --report report.json
```

### 3. 웹 인터페이스 사용
```bash
python web/app.py
```
브라우저에서 `http://localhost:5000` 접속

## 프로젝트 구조

```
labeling_qc/
├── src/
│   ├── core/
│   │   ├── quality_controller.py  # 메인 컨트롤러
│   │   ├── rule_validator.py      # 검증 규칙
│   │   └── rule_fixer.py          # 자동 수정
│   ├── models/
│   │   └── quality_issue.py       # 이슈 데이터 모델
│   └── utils/
├── cli/
│   └── cli_tool.py               # 명령행 도구
├── web/
│   ├── app.py                    # 웹 앱
│   └── templates/                # HTML 템플릿
├── requirements.txt              # 의존성 목록
└── README.md                     # 이 파일
```

## 검증 규칙 상세

### R009: 특정 텍스트 라벨 검증
- **대상**: "원문", "번역문", "본문" 텍스트
- **권장 라벨**: ParaText
- **자동 수정**: 가능

### R010: 날짜 패턴 라벨 검증
- **패턴**: 
  - 2021년 2월 3일
  - 2021. 2. 3
  - 2021-02-03
  - 2021. 2. 3 작성
- **권장 라벨**: Date
- **자동 수정**: 가능

## API 사용 예시

```python
from backend.src.core import QualityController
from pathlib import Path

# 컨트롤러 초기화
controller = QualityController()

# 파일 검증
issues = controller.validate_file(Path("sample.json"))
print(f"발견된 이슈: {len(issues)}개")

# 자동 수정
fixed_issues = controller.auto_fix_file(Path("sample.json"))
print(f"수정 후 남은 이슈: {len(fixed_issues)}개")
```

## 라이센스

이 프로젝트는 내부 사용을 위한 품질 검수 도구입니다.
