# Labeling QC Validation Tools

라벨링 품질 검수를 위한 V2/V3 모델 비교 및 분석 도구 모음입니다.

## 📁 프로젝트 구조

```
Validate/
├── 📊 데이터 파일
│   ├── filesforabstract.zip           # 146개 ZIP 파일 컨테이너
│   ├── responses_v2.csv               # V2 모델 결과
│   ├── responses_v3.csv               # V3 모델 결과
│   ├── complete_validation_results.csv # 전체 분석 결과 (상세)
│   └── simplified_validation_results.csv # 간소화된 분석 결과
│
├── 🔧 분석 도구
│   ├── analyze_validate.py            # 기본 구조 분석
│   ├── analyze_json_labels.py         # JSON 라벨 분석
│   ├── complete_analyzer.py           # 전체 데이터 분석기 (메인)
│   ├── create_simplified_csv.py       # 간소화된 결과 생성
│   └── validation_tool.py             # 개별 파일 검증
│
├── 📈 리포트 도구
│   ├── final_report_simple.py         # 최종 분석 리포트 생성
│   ├── final_analysis_report.txt      # 생성된 분석 리포트
│   └── result_formatter.py            # 결과 포맷터
│
└── 📋 기타
    ├── analyze_multiple_samples.py    # 다중 샘플 분석
    ├── final_report.py               # pandas 버전 리포트
    └── validation_results.csv        # 초기 검증 결과
```

## 🎯 주요 기능

### 1. 데이터 구조 분석
- **ZIP-in-ZIP 구조** 자동 처리
- **CSV-JSON ID 매핑** 로직
- **KINX 번호 기반** 파일 매칭

### 2. V2/V3 모델 비교
- **라벨링 결과 비교**: ID 리스트 차이 분석
- **카테고리 분석**: ParaText, ListText 분류
- **품질 개선 측정**: 추가/삭제/변경된 라벨 추적

### 3. 요약 타겟 식별
- **ParaText**: 요약 대상으로 사용할 텍스트 (P:개수)
- **ListText**: 일반 텍스트 (L:개수)
- **자동 분류**: category.label + category.type 조합

## 🚀 사용법

### 1. 전체 분석 실행
```bash
python complete_analyzer.py
```
**결과**: `complete_validation_results.csv` (146개 파일 상세 분석)

### 2. 간소화된 결과 생성
```bash
python create_simplified_csv.py
```
**결과**: `simplified_validation_results.csv` (핵심 컬럼만)

### 3. 최종 리포트 생성
```bash
python final_report_simple.py
```
**결과**: `final_analysis_report.txt` (비즈니스 인사이트)

### 4. 기본 구조 분석
```bash
python analyze_validate.py
```
**결과**: ZIP/CSV 구조 및 매칭 상태

## 📊 분석 결과 요약

### 전체 통계 (146개 파일)
- ✅ **JSON 로드 성공**: 144개 (98.6%)
- 📈 **V2→V3 개선**: +58개 ID 증가 (+20.3%)
- 🎯 **요약 대상**: ParaText +2개 증가
- 📝 **일반 텍스트**: ListText +56개 증가

### 품질 개선 현황
- 🔄 **변화 있는 파일**: 49개 (33.6%)
- ⬆️ **ID 증가 파일**: 39개
- ⬇️ **ID 감소 파일**: 5개 (검토 필요)
- 📋 **V3 비어있는 파일**: 2개 (V2: 15개)

## 📋 CSV 출력 형식

### 간소화 버전 (`simplified_validation_results.csv`)
```csv
source_file,v2_output,v2_result_summary,v2_paratext_count,v2_listtext_count,
v3_output,v3_result_summary,v3_paratext_count,v3_listtext_count,json_loaded
```

### 상세 버전 (`complete_validation_results.csv`)
위 컬럼 + 추가 분석 데이터 (kinx_number, has_difference, v2_only_ids, v3_only_ids 등)

## 🔍 데이터 파이프라인

```
filesforabstract.zip
    └── visualcontent-KINX{number}_TP.zip
        └── visualinfo/{number}_visualinfo.json
            └── elements[].category.label + category.type
                ├── ParaText + PARAGRAPH → 요약 대상
                ├── ListText + LIST → 일반 텍스트
                └── 기타 조합 → 분류 외

responses_v2.csv / responses_v3.csv
    └── output_text (ID 리스트)
        └── JSON elements ID와 매핑
```

## ⚙️ 기술 스택

- **Python 3.x**: 기본 런타임
- **zipfile**: ZIP-in-ZIP 처리
- **csv**: CSV 파일 처리
- **json**: JSON 데이터 파싱
- **io.BytesIO**: 메모리 기반 파일 처리 (디스크 I/O 충돌 방지)

## 🎯 비즈니스 인사이트

### V3 모델 도입 권장사항
1. ✅ **전체적 품질 향상**: 20.3% ID 증가로 더 세밀한 라벨링
2. ✅ **요약 정확도 개선**: ParaText 식별 안정성 유지 + 2개 증가
3. ⚠️ **점진적 도입**: 5개 ID 감소 파일 원인 분석 후 적용

### 품질 관리 방향
- 기존 `labeling_qc` 도구와 연계한 지속적 품질 검증
- V2→V3 전환 시 단계적 적용 및 모니터링
- JSON 파싱 실패 2개 파일 원인 조사 필요

## 🔗 연계 시스템

이 도구들은 메인 `labeling_qc` 프로젝트와 연계하여 사용할 수 있습니다:

```
labeling_qc/
├── src/core/quality_controller.py  # 기존 품질 검수
├── cli/cli_tool.py                # CLI 인터페이스  
├── web/app.py                     # 웹 인터페이스
└── Validate/                      # V2/V3 비교 도구 (이 폴더)
```

## 📞 문의 및 기여

- 개발자: GitHub Copilot
- 프로젝트: labeling_qc
- 목적: 라벨링 품질 검수 및 V2/V3 모델 성능 비교

---

*Last updated: 2025-09-16*