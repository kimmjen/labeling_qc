import csv

def create_simplified_csv():
    """간소화된 CSV 파일 생성 - 핵심 컬럼만 유지"""
    
    print("📋 간소화된 CSV 생성 중...")
    
    # 원본 CSV 읽기
    with open('complete_validation_results.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    # 새로운 간소화된 데이터
    simplified_data = []
    
    for row in data:
        # 핵심 컬럼만 선택
        simplified_row = {
            'source_file': row['source_file'],
            'v2_output': row['v2_output'],
            'v2_result_summary': row['v2_result_summary'],
            'v2_paratext_count': row['v2_paratext_count'],
            'v2_listtext_count': row['v2_listtext_count'],
            'v3_output': row['v3_output'],
            'v3_result_summary': row['v3_result_summary'],
            'v3_paratext_count': row['v3_paratext_count'],
            'v3_listtext_count': row['v3_listtext_count'],
            'json_loaded': row['json_loaded']
        }
        simplified_data.append(simplified_row)
    
    # 간소화된 CSV 저장
    fieldnames = [
        'source_file',
        'v2_output',
        'v2_result_summary', 
        'v2_paratext_count',
        'v2_listtext_count',
        'v3_output',
        'v3_result_summary',
        'v3_paratext_count', 
        'v3_listtext_count',
        'json_loaded'
    ]
    
    with open('simplified_validation_results.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(simplified_data)
    
    print(f"✅ 간소화된 CSV 생성 완료: {len(simplified_data)}개 레코드")
    print("📁 파일: simplified_validation_results.csv")
    
    # 간단한 통계
    successful_loads = sum(1 for row in simplified_data if row['json_loaded'] == 'True')
    v2_paratext_total = sum(int(row['v2_paratext_count']) for row in simplified_data if row['json_loaded'] == 'True')
    v3_paratext_total = sum(int(row['v3_paratext_count']) for row in simplified_data if row['json_loaded'] == 'True')
    v2_listtext_total = sum(int(row['v2_listtext_count']) for row in simplified_data if row['json_loaded'] == 'True')
    v3_listtext_total = sum(int(row['v3_listtext_count']) for row in simplified_data if row['json_loaded'] == 'True')
    
    print("\n📊 핵심 통계:")
    print(f"• JSON 로드 성공: {successful_loads}/{len(simplified_data)} ({successful_loads/len(simplified_data)*100:.1f}%)")
    print(f"• ParaText: V2 {v2_paratext_total}개 → V3 {v3_paratext_total}개 ({v3_paratext_total-v2_paratext_total:+d})")
    print(f"• ListText: V2 {v2_listtext_total}개 → V3 {v3_listtext_total}개 ({v3_listtext_total-v2_listtext_total:+d})")

if __name__ == "__main__":
    try:
        create_simplified_csv()
    except FileNotFoundError:
        print("❌ 'complete_validation_results.csv' 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")