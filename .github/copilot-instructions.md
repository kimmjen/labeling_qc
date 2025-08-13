<!-- 라벨링 품질 검수 전용 프로젝트 -->

- [x] Verify that the copilot-instructions.md file in the .github directory is created.
- [x] Clarify Project Requirements - 라벨링 품질 검수 전용 Python 프로젝트
- [x] Scaffold the Project - 완료: 프로젝트 구조 및 핵심 파일 생성
- [x] Customize the Project - 완료: 검수 규칙 및 자동 수정 로직 구현
- [x] Install Required Extensions - 완료: Flask 등 필요 패키지 설치
- [x] Compile the Project - 완료: 모든 모듈 정상 로드 확인
- [x] Create and Run Task - 완료: CLI 및 비교 도구 실행 성공
- [x] Launch the Project - 완료: 실제 데이터로 검수 비교 완료
- [x] Ensure Documentation is Complete - 완료: README.md 및 상세 문서 작성

## 프로젝트 완성 현황
✅ **라벨링 품질 검수 도구 완성**
- CLI 도구: 단일/일괄 검수, 자동 수정, 비교 기능
- 웹 인터페이스: Flask 기반 업로드 및 검수
- ZIP 자동 처리: 압축 파일 자동 추출 및 JSON 검색
- 비교 분석: 자동 검수 vs 수동 검수 비교 및 정확도 측정
- 검증 규칙: R001~R010 포함 10가지 품질 규칙
- 실제 테스트: 190개 이슈 자동 검출, 90% 정확도 달성

## 프로젝트 개요
라벨링 품질 검수(Quality Control) 전용 도구
- JSON 파일의 라벨링 결과 검증
- 품질 문제 자동 탐지
- 수정 제안 및 자동 수정
- 품질 리포트 생성
