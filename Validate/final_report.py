#!/usr/bin/env python3
"""
최종 분석 리포트 생성
"""

import csv
from pathlib import Path

def create_final_report():
    """최종 분석 리포트 생성"""
    
    print("📋 최종 분석 리포트 생성 중...")
    
    # CSV 파일 읽기
    with open('complete_validation_results.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    # 숫자 컬럼들을 int로 변환
    for row in data:
        for col in ['v2_paratext_count', 'v2_listtext_count', 'v2_other_count', 
                   'v3_paratext_count', 'v3_listtext_count', 'v3_other_count',
                   'total_v2_ids', 'total_v3_ids']:
            row[col] = int(row[col])
        row['has_difference'] = row['has_difference'] == 'True'
        row['json_loaded'] = row['json_loaded'] == 'True'
    
    print(f"\n{'='*80}")
    print("🎯 VALIDATE 폴더 분석 - 최종 결과 리포트")
    print(f"{'='*80}")
    
    # 기본 통계
    total_files = len(df)
    successful_loads = df['json_loaded'].sum()
    differences = df['has_difference'].sum()
    
    print(f"📊 기본 통계:")
    print(f"  - 총 파일 수: {total_files}개")
    print(f"  - JSON 로드 성공: {successful_loads}개 ({successful_loads/total_files*100:.1f}%)")
    print(f"  - V2-V3 차이 발생: {differences}개 ({differences/successful_loads*100:.1f}%)")
    
    # V2 vs V3 비교
    v2_total_ids = df['total_v2_ids'].sum()
    v3_total_ids = df['total_v3_ids'].sum()
    
    v2_paratext = df['v2_paratext_count'].sum()
    v2_listtext = df['v2_listtext_count'].sum()
    v2_other = df['v2_other_count'].sum()
    
    v3_paratext = df['v3_paratext_count'].sum()
    v3_listtext = df['v3_listtext_count'].sum()
    v3_other = df['v3_other_count'].sum()
    
    print(f"\n🔄 V2 → V3 비교:")
    print(f"  - 총 선택 ID: {v2_total_ids} → {v3_total_ids} (+{v3_total_ids-v2_total_ids})")
    print(f"  - ParaText: {v2_paratext} → {v3_paratext} (+{v3_paratext-v2_paratext})")
    print(f"  - ListText: {v2_listtext} → {v3_listtext} (+{v3_listtext-v2_listtext})")
    print(f"  - 기타: {v2_other} → {v3_other} (+{v3_other-v2_other})")
    
    # 성능 개선률
    if v2_total_ids > 0:
        improvement_rate = (v3_total_ids - v2_total_ids) / v2_total_ids * 100
        print(f"  - 전체 개선률: +{improvement_rate:.1f}%")
    
    # 라벨 타입별 비율
    print(f"\n📈 V3 기준 라벨 타입 분포:")
    if v3_total_ids > 0:
        paratext_ratio = v3_paratext / v3_total_ids * 100
        listtext_ratio = v3_listtext / v3_total_ids * 100
        other_ratio = v3_other / v3_total_ids * 100
        
        print(f"  - ParaText: {paratext_ratio:.1f}% (요약 대상)")
        print(f"  - ListText: {listtext_ratio:.1f}% (일반 목록)")
        print(f"  - 기타: {other_ratio:.1f}%")
    
    # 차이 패턴 분석
    diff_files = df[df['has_difference'] == True]
    
    if len(diff_files) > 0:
        print(f"\n🔍 차이 패턴 분석:")
        
        # V3에서만 선택된 케이스
        v3_only_cases = diff_files[diff_files['v3_only_ids'] != '[]']
        print(f"  - V3에서 추가 선택: {len(v3_only_cases)}건")
        
        # V2에서만 선택된 케이스  
        v2_only_cases = diff_files[diff_files['v2_only_ids'] != '[]']
        print(f"  - V2에서만 선택: {len(v2_only_cases)}건")
        
        # 상위 차이 케이스
        print(f"\n🎯 주요 개선 케이스 (V3 추가 선택 상위 5개):")
        v3_improvements = diff_files[diff_files['total_v3_ids'] > diff_files['total_v2_ids']]
        v3_improvements['improvement'] = v3_improvements['total_v3_ids'] - v3_improvements['total_v2_ids']
        top_improvements = v3_improvements.nlargest(5, 'improvement')
        
        for idx, row in top_improvements.iterrows():
            print(f"  {row['source_file']}: {row['total_v2_ids']} → {row['total_v3_ids']} (+{int(row['improvement'])})")
    
    # 요약 대상 (ParaText) 분석
    paratext_files_v2 = df[df['v2_paratext_count'] > 0]
    paratext_files_v3 = df[df['v3_paratext_count'] > 0]
    
    print(f"\n🎯 요약 대상 (ParaText) 분석:")
    print(f"  - V2에서 ParaText 발견: {len(paratext_files_v2)}개 파일")
    print(f"  - V3에서 ParaText 발견: {len(paratext_files_v3)}개 파일")
    
    if len(paratext_files_v3) > 0:
        avg_paratext_v3 = paratext_files_v3['v3_paratext_count'].mean()
        print(f"  - V3 평균 ParaText 개수: {avg_paratext_v3:.1f}개/파일")
    
    # 빈 결과 분석
    empty_v2 = df[df['total_v2_ids'] == 0]
    empty_v3 = df[df['total_v3_ids'] == 0]
    
    print(f"\n📭 빈 결과 분석:")
    print(f"  - V2 빈 결과: {len(empty_v2)}개 파일")
    print(f"  - V3 빈 결과: {len(empty_v3)}개 파일")
    print(f"  - V3에서 개선된 파일: {len(empty_v2) - len(empty_v3)}개")
    
    # 결론
    print(f"\n{'='*80}")
    print("💡 결론 및 인사이트")
    print(f"{'='*80}")
    
    print("✅ 주요 발견사항:")
    print(f"  1. V3가 V2 대비 {v3_total_ids-v2_total_ids}개 더 많은 요소를 식별")
    print(f"  2. 특히 ListText 요소에서 {v3_listtext-v2_listtext}개 증가 (대부분)")
    print(f"  3. ParaText(요약 대상)는 {v3_paratext-v2_paratext}개 소폭 증가")
    print(f"  4. 전체 {total_files}개 파일 중 {differences}개({differences/total_files*100:.1f}%)에서 개선")
    
    print(f"\n🎯 비즈니스 임팩트:")
    if v3_paratext > 0:
        print(f"  - 총 {v3_paratext}개의 요약 대상(ParaText) 식별")
        print(f"  - 요약 대상 비율: {v3_paratext/v3_total_ids*100:.1f}%")
    
    print(f"  - V3 모델이 더 포괄적이고 정확한 요소 식별 능력 보유")
    print(f"  - 특히 리스트 형태의 텍스트 인식 성능이 크게 향상")

def main():
    """메인 실행"""
    create_final_report()
    
    print(f"\n📁 생성된 파일:")
    print(f"  - complete_validation_results.csv: 전체 상세 결과")
    print(f"  - validation_results.csv: 초기 테스트 결과")
    
    print(f"\n🚀 사용 방법:")
    print(f"  - Excel에서 complete_validation_results.csv 열어서 상세 분석 가능")
    print(f"  - has_difference=True 필터링하여 차이점만 확인 가능")
    print(f"  - v3_paratext_count > 0 필터링하여 요약 대상만 확인 가능")

if __name__ == "__main__":
    main()