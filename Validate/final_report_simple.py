import csv
from pathlib import Path

def create_final_report():
    """최종 분석 리포트 생성 (pandas 없이)"""
    
    print("📋 최종 분석 리포트 생성 중...")
    
    # CSV 파일 읽기
    with open('complete_validation_results.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    # 숫자 컬럼들을 int로 변환하고 집계용 변수 초기화
    total_files = len(data)
    successful_loads = 0
    differences = 0
    
    v2_total_ids = 0
    v3_total_ids = 0
    v2_paratext = 0
    v2_listtext = 0
    v2_other = 0
    v3_paratext = 0
    v3_listtext = 0
    v3_other = 0
    
    diff_files = []
    paratext_files_v2 = []
    paratext_files_v3 = []
    empty_v2 = []
    empty_v3 = []
    
    # 데이터 처리 및 집계
    for row in data:
        # 숫자 변환
        for col in ['v2_paratext_count', 'v2_listtext_count', 'v2_other_count', 
                   'v3_paratext_count', 'v3_listtext_count', 'v3_other_count',
                   'total_v2_ids', 'total_v3_ids']:
            row[col] = int(row[col])
        
        row['has_difference'] = row['has_difference'] == 'True'
        row['json_loaded'] = row['json_loaded'] == 'True'
        
        # 집계
        if row['json_loaded']:
            successful_loads += 1
        
        if row['has_difference']:
            differences += 1
            diff_files.append(row)
        
        v2_total_ids += row['total_v2_ids']
        v3_total_ids += row['total_v3_ids']
        v2_paratext += row['v2_paratext_count']
        v2_listtext += row['v2_listtext_count']
        v2_other += row['v2_other_count']
        v3_paratext += row['v3_paratext_count']
        v3_listtext += row['v3_listtext_count']
        v3_other += row['v3_other_count']
        
        # 필터링
        if row['v2_paratext_count'] > 0:
            paratext_files_v2.append(row)
        if row['v3_paratext_count'] > 0:
            paratext_files_v3.append(row)
        if row['total_v2_ids'] == 0:
            empty_v2.append(row)
        if row['total_v3_ids'] == 0:
            empty_v3.append(row)
    
    # 리포트 생성
    report = []
    report.append("=" * 80)
    report.append("📊 LABELING QC VALIDATION 최종 분석 리포트")
    report.append("=" * 80)
    report.append("")
    
    # 1. 전체 개요
    report.append("🎯 1. 전체 개요")
    report.append("-" * 40)
    report.append(f"• 총 분석 파일 수: {total_files:,}개")
    report.append(f"• JSON 로드 성공: {successful_loads:,}개 ({successful_loads/total_files*100:.1f}%)")
    report.append(f"• JSON 로드 실패: {total_files - successful_loads:,}개")
    report.append(f"• V2-V3 차이 있는 파일: {differences:,}개 ({differences/total_files*100:.1f}%)")
    report.append("")
    
    # 2. ID 개수 변화
    id_change = v3_total_ids - v2_total_ids
    report.append("📈 2. ID 개수 변화 (V2 → V3)")
    report.append("-" * 40)
    report.append(f"• V2 총 ID 수: {v2_total_ids:,}개")
    report.append(f"• V3 총 ID 수: {v3_total_ids:,}개")
    report.append(f"• 증감: {id_change:+,}개 ({id_change/v2_total_ids*100:+.1f}%)")
    report.append("")
    
    # 3. 카테고리별 변화
    report.append("🏷️ 3. 카테고리별 변화")
    report.append("-" * 40)
    
    para_change = v3_paratext - v2_paratext
    list_change = v3_listtext - v2_listtext
    other_change = v3_other - v2_other
    
    report.append("ParaText (요약 대상):")
    report.append(f"  • V2: {v2_paratext:,}개 → V3: {v3_paratext:,}개 ({para_change:+,})")
    report.append(f"  • 파일별 평균: V2 {v2_paratext/total_files:.1f}개 → V3 {v3_paratext/total_files:.1f}개")
    report.append("")
    
    report.append("ListText (일반 텍스트):")
    report.append(f"  • V2: {v2_listtext:,}개 → V3: {v3_listtext:,}개 ({list_change:+,})")
    report.append(f"  • 파일별 평균: V2 {v2_listtext/total_files:.1f}개 → V3 {v3_listtext/total_files:.1f}개")
    report.append("")
    
    report.append("기타:")
    report.append(f"  • V2: {v2_other:,}개 → V3: {v3_other:,}개 ({other_change:+,})")
    report.append("")
    
    # 4. 변화 패턴 분석
    report.append("🔍 4. 변화 패턴 분석")
    report.append("-" * 40)
    
    improved_files = 0
    decreased_files = 0
    for row in diff_files:
        if row['total_v3_ids'] > row['total_v2_ids']:
            improved_files += 1
        elif row['total_v3_ids'] < row['total_v2_ids']:
            decreased_files += 1
    
    report.append(f"• ID 증가 파일: {improved_files:,}개")
    report.append(f"• ID 감소 파일: {decreased_files:,}개")
    report.append(f"• 변화 없음: {differences - improved_files - decreased_files:,}개")
    report.append("")
    
    # 5. 요약 타겟 분석
    report.append("🎯 5. 요약 타겟 분석 (ParaText)")
    report.append("-" * 40)
    report.append(f"• V2에서 ParaText 있는 파일: {len(paratext_files_v2):,}개 ({len(paratext_files_v2)/total_files*100:.1f}%)")
    report.append(f"• V3에서 ParaText 있는 파일: {len(paratext_files_v3):,}개 ({len(paratext_files_v3)/total_files*100:.1f}%)")
    
    # ParaText 증가/감소 파일 분석
    para_gained = sum(1 for row in data if row['v2_paratext_count'] == 0 and row['v3_paratext_count'] > 0)
    para_lost = sum(1 for row in data if row['v2_paratext_count'] > 0 and row['v3_paratext_count'] == 0)
    
    report.append(f"• ParaText 새로 생긴 파일: {para_gained:,}개")
    report.append(f"• ParaText 사라진 파일: {para_lost:,}개")
    report.append("")
    
    # 6. 데이터 품질
    report.append("✅ 6. 데이터 품질")
    report.append("-" * 40)
    report.append(f"• V2 비어있는 파일: {len(empty_v2):,}개")
    report.append(f"• V3 비어있는 파일: {len(empty_v3):,}개")
    report.append(f"• JSON 파싱 실패: {total_files - successful_loads:,}개")
    report.append("")
    
    # 7. 비즈니스 영향
    report.append("💼 7. 비즈니스 영향 평가")
    report.append("-" * 40)
    report.append("긍정적 영향:")
    report.append(f"  ✓ 전체 라벨링 ID {id_change:+,}개 증가 ({id_change/v2_total_ids*100:+.1f}%)")
    report.append(f"  ✓ 요약 대상(ParaText) {para_change:+,}개 증가")
    report.append(f"  ✓ 일반 텍스트(ListText) {list_change:+,}개 증가")
    report.append(f"  ✓ 품질 개선된 파일: {differences:,}개 ({differences/total_files*100:.1f}%)")
    report.append("")
    
    if para_lost > 0 or decreased_files > 0:
        report.append("주의 사항:")
        if para_lost > 0:
            report.append(f"  ⚠️ ParaText 사라진 파일: {para_lost:,}개 검토 필요")
        if decreased_files > 0:
            report.append(f"  ⚠️ ID 감소 파일: {decreased_files:,}개 검토 필요")
        report.append("")
    
    # 8. 권장 사항
    report.append("📋 8. 권장 사항")
    report.append("-" * 40)
    report.append("1. V3 모델 도입 권장:")
    report.append(f"   • 전체적으로 {id_change:+,}개 ID 증가로 더 세밀한 라벨링")
    report.append(f"   • 요약 대상 식별 개선: {para_change:+,}개 ParaText 증가")
    report.append("")
    
    report.append("2. 추가 검토 필요:")
    if para_lost > 0:
        report.append(f"   • ParaText 사라진 {para_lost}개 파일 수동 검토")
    if decreased_files > 0:
        report.append(f"   • ID 감소한 {decreased_files}개 파일 원인 분석")
    if total_files - successful_loads > 0:
        report.append(f"   • JSON 파싱 실패 {total_files - successful_loads}개 파일 원인 조사")
    report.append("")
    
    report.append("3. 품질 관리:")
    report.append("   • 기존 labeling_qc 도구로 품질 검증 계속 수행")
    report.append("   • V3 전환 시 점진적 적용 고려")
    report.append("")
    
    report.append("=" * 80)
    report.append(f"📅 리포트 생성 일시: {Path().resolve()}")
    report.append("=" * 80)
    
    # 파일로 저장
    with open('final_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    # 화면 출력
    for line in report:
        print(line)
    
    print("\n✅ 최종 분석 리포트가 'final_analysis_report.txt' 파일로 저장되었습니다.")

if __name__ == "__main__":
    try:
        create_final_report()
    except FileNotFoundError:
        print("❌ 'complete_validation_results.csv' 파일을 찾을 수 없습니다.")
        print("먼저 complete_analyzer.py를 실행해주세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")