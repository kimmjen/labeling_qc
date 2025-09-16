#!/usr/bin/env python3
"""
더 많은 샘플로 패턴 분석
"""

import csv
import json
import zipfile
import os
from pathlib import Path

def analyze_multiple_samples():
    """여러 샘플로 패턴 분석"""
    
    print("=== 다중 샘플 패턴 분석 ===")
    
    # CSV 파일들 로드
    csv_v2 = []
    csv_v3 = []
    
    with open('responses_v2.csv', 'r', encoding='utf-8-sig') as f:
        csv_v2 = list(csv.DictReader(f))
    
    with open('responses_v3.csv', 'r', encoding='utf-8-sig') as f:
        csv_v3 = list(csv.DictReader(f))
    
    # 첫 5개 샘플 분석
    print("첫 5개 샘플 V2 vs V3 비교:")
    for i in range(5):
        v2_row = csv_v2[i]
        v3_row = csv_v3[i]
        
        print(f"\n--- 샘플 {i+1}: {v2_row['source_file']} ---")
        print(f"V2 output: {v2_row['output_text'].strip()}")
        print(f"V3 output: {v3_row['output_text'].strip()}")
        
        # 숫자 추출
        import re
        v2_ids = re.findall(r'\d+', v2_row['output_text'])
        v3_ids = re.findall(r'\d+', v3_row['output_text'])
        
        print(f"V2 IDs: {v2_ids}")
        print(f"V3 IDs: {v3_ids}")
        
        if set(v2_ids) != set(v3_ids):
            print("🔍 V2와 V3 결과가 다름!")
    
    return csv_v2, csv_v3

def extract_and_analyze_json(zip_filename, kinx_number):
    """특정 ZIP에서 JSON 추출하고 분석"""
    
    try:
        # 대형 ZIP에서 특정 파일 추출
        with zipfile.ZipFile('filesforabstract.zip', 'r') as main_zip:
            # 임시 추출
            main_zip.extract(zip_filename, 'temp_extract')
            
            # 내부 ZIP 추출
            inner_zip_path = f'temp_extract/{zip_filename}'
            with zipfile.ZipFile(inner_zip_path, 'r') as inner_zip:
                # visualinfo JSON 찾기
                json_files = [f for f in inner_zip.namelist() if 'visualinfo' in f and f.endswith('.json')]
                
                if json_files:
                    json_file = json_files[0]
                    inner_zip.extract(json_file, 'temp_extract/inner2')
                    
                    # JSON 분석
                    json_path = f'temp_extract/inner2/{json_file}'
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # ParaText와 ListText 찾기
                    para_texts = [e for e in data['elements'] if e['category']['label'] == 'ParaText']
                    list_texts = [e for e in data['elements'] if e['category']['label'] == 'ListText']
                    
                    print(f"\n=== {kinx_number} JSON 분석 ===")
                    print(f"ParaText 개수: {len(para_texts)}")
                    print(f"ListText 개수: {len(list_texts)}")
                    
                    # PARAGRAPH type 확인
                    paragraph_elements = [e for e in data['elements'] if e['category']['type'] == 'PARAGRAPH']
                    print(f"PARAGRAPH type 개수: {len(paragraph_elements)}")
                    
                    # 정리
                    os.remove(json_path)
                    os.remove(inner_zip_path)
                    
                    return {
                        'para_texts': len(para_texts),
                        'list_texts': len(list_texts),
                        'paragraphs': len(paragraph_elements),
                        'elements': data['elements']
                    }
    
    except Exception as e:
        print(f"오류 발생 {kinx_number}: {e}")
        return None

def main():
    csv_v2, csv_v3 = analyze_multiple_samples()
    
    # 특정 KINX 번호들로 JSON 분석
    print(f"\n=== 특정 샘플 JSON 분석 ===")
    
    sample_indices = [0, 1, 2]  # 처음 3개 샘플
    
    for idx in sample_indices:
        source_file = csv_v2[idx]['source_file']
        kinx_match = source_file.replace('_visualinfo.json', '').replace('KINX', '')
        zip_filename = f'visualcontent-KINX{kinx_match}.zip'
        
        print(f"\n처리 중: {source_file} -> {zip_filename}")
        
        # ZIP에서 JSON 추출 및 분석
        result = extract_and_analyze_json(zip_filename, kinx_match)
        
        if result:
            # CSV 결과와 비교
            v2_ids = [int(x) for x in __import__('re').findall(r'\d+', csv_v2[idx]['output_text']) if x.isdigit()]
            v3_ids = [int(x) for x in __import__('re').findall(r'\d+', csv_v3[idx]['output_text']) if x.isdigit()]
            
            print(f"V2 추출 IDs: {v2_ids}")
            print(f"V3 추출 IDs: {v3_ids}")
            
            # ID별 요소 확인
            for element_id in set(v2_ids + v3_ids):
                element = next((e for e in result['elements'] if e['id'] == str(element_id)), None)
                if element:
                    label = element['category']['label']
                    elem_type = element['category']['type']
                    text = element.get('content', {}).get('text', '')[:50] if 'content' in element else ''
                    
                    is_summary_target = (label == 'ParaText' and elem_type == 'PARAGRAPH')
                    status = "✅ 요약대상" if is_summary_target else "❌ 일반텍스트"
                    
                    print(f"  ID {element_id}: {label} ({elem_type}) - {text}... [{status}]")

if __name__ == "__main__":
    main()