#!/usr/bin/env python3
"""
JSON 파일의 ID별 Label 정보 분석
"""

import json
import csv
from pathlib import Path

def analyze_json_labels():
    """JSON 파일에서 ID별 Label 정보 분석"""
    
    # JSON 파일 로드
    json_path = Path('temp_extract/inner/visualinfo/KINX2025000285_visualinfo.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=== JSON 파일 ID별 Label 분석 ===")
    print(f"파일: {json_path.name}")
    print(f"총 elements 수: {len(data['elements'])}")
    
    # Label별 분류
    label_stats = {}
    id_label_map = {}
    
    for element in data['elements']:
        element_id = element['id']
        label = element['category']['label']
        element_type = element['category']['type']
        
        text_content = element.get('content', {}).get('text', '') if 'content' in element else ''
        id_label_map[element_id] = {
            'label': label,
            'type': element_type,
            'text': text_content[:100] if text_content else '',  # 처음 100자만
            'confidence': element.get('confidence', 0.0)
        }
        
        if label not in label_stats:
            label_stats[label] = []
        label_stats[label].append(element_id)
    
    # Label별 통계 출력
    print("\n=== Label별 통계 ===")
    for label, ids in label_stats.items():
        print(f"{label}: {len(ids)}개")
        if label in ['ParaText', 'ListText']:
            print(f"  IDs: {ids[:5]}{'...' if len(ids) > 5 else ''}")
    
    # ParaText와 ListText 상세 분석
    print("\n=== ParaText 상세 분석 ===")
    para_texts = [e for e in data['elements'] if e['category']['label'] == 'ParaText']
    for i, element in enumerate(para_texts[:5]):
        print(f"ID {element['id']}: {element['category']['type']} - {element['content']['text'][:80]}...")
    
    print(f"\n=== ListText 상세 분석 ===")
    list_texts = [e for e in data['elements'] if e['category']['label'] == 'ListText']
    for i, element in enumerate(list_texts[:5]):
        print(f"ID {element['id']}: {element['category']['type']} - {element['content']['text'][:80]}...")
    
    # PARAGRAPH type 확인
    print(f"\n=== PARAGRAPH type 분석 ===")
    paragraph_elements = [e for e in data['elements'] if e['category']['type'] == 'PARAGRAPH']
    print(f"PARAGRAPH type 총 개수: {len(paragraph_elements)}")
    for element in paragraph_elements[:5]:
        print(f"ID {element['id']}: {element['category']['label']} - {element['content']['text'][:50]}...")
    
    return id_label_map, label_stats

def match_csv_with_json():
    """CSV output_text의 ID와 JSON ID 매칭 확인"""
    
    print("\n=== CSV-JSON ID 매칭 분석 ===")
    
    # CSV 파일 읽기 (v2와 v3 모두)
    csv_files = ['responses_v2.csv', 'responses_v3.csv']
    
    for csv_file in csv_files:
        print(f"\n--- {csv_file} 분석 ---")
        
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # KINX2025000285와 매칭되는 row 찾기
        target_row = None
        for row in rows:
            if 'KINX2025000285' in row['source_file']:
                target_row = row
                break
        
        if target_row:
            print(f"매칭 파일: {target_row['source_file']}")
            print(f"Output text: {target_row['output_text']}")
            
            # output_text에서 숫자 추출
            import re
            numbers = re.findall(r'\d+', target_row['output_text'])
            print(f"추출된 ID들: {numbers}")
            
            return numbers
        else:
            print("매칭되는 파일을 찾지 못했습니다.")
    
    return []

if __name__ == "__main__":
    id_label_map, label_stats = analyze_json_labels()
    csv_ids = match_csv_with_json()
    
    # 매칭 결과 확인
    if csv_ids:
        print(f"\n=== CSV ID와 JSON Label 매칭 ===")
        for csv_id in csv_ids:
            if csv_id in id_label_map:
                info = id_label_map[csv_id]
                print(f"ID {csv_id}: {info['label']} ({info['type']}) - {info['text']}")
                
                # ParaText인지 확인
                if info['label'] == 'ParaText' and info['type'] == 'PARAGRAPH':
                    print(f"  ✅ 요약 대상: ParaText + PARAGRAPH")
                else:
                    print(f"  ❌ 요약 대상 아님: {info['label']} + {info['type']}")
            else:
                print(f"ID {csv_id}: JSON에서 찾을 수 없음")