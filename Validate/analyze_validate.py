#!/usr/bin/env python3
"""
Validate 폴더 분석 스크립트
CSV와 ZIP 파일 간 연결관계 파악
"""

import csv
import zipfile
import re
from pathlib import Path

def analyze_validate_folder():
    """Validate 폴더 내용 분석"""
    
    # 1. CSV 파일들 분석
    print("=== CSV 파일 분석 ===")
    
    csv_files = ['responses_v2.csv', 'responses_v3.csv']
    csv_data = {}
    
    for csv_file in csv_files:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            csv_data[csv_file] = rows
            
            print(f"\n{csv_file}:")
            print(f"  - 행 수: {len(rows)}")
            print(f"  - 컬럼: {list(rows[0].keys())}")
            print(f"  - source_file 샘플:")
            for row in rows[:3]:
                print(f"    {row['source_file']}")
    
    # 2. ZIP 파일 분석
    print("\n=== ZIP 파일 분석 ===")
    
    with zipfile.ZipFile('filesforabstract.zip', 'r') as z:
        zip_files = z.namelist()
        print(f"ZIP 내 파일 수: {len(zip_files)}")
        print(f"ZIP 파일 샘플:")
        for f in zip_files[:5]:
            print(f"  {f}")
    
    # 3. 파일명 패턴 분석
    print("\n=== 파일명 패턴 분석 ===")
    
    # CSV의 source_file에서 KINX 번호 추출
    csv_kinx_numbers = set()
    for rows in csv_data.values():
        for row in rows:
            source_file = row['source_file']
            match = re.search(r'KINX(\d+)', source_file)
            if match:
                csv_kinx_numbers.add(match.group(1))
    
    print(f"CSV에서 추출된 KINX 번호 수: {len(csv_kinx_numbers)}")
    print(f"CSV KINX 번호 샘플: {list(csv_kinx_numbers)[:5]}")
    
    # ZIP 파일명에서 KINX 번호 추출
    zip_kinx_numbers = set()
    for zip_file in zip_files:
        match = re.search(r'KINX(\d+)', zip_file)
        if match:
            zip_kinx_numbers.add(match.group(1))
    
    print(f"ZIP에서 추출된 KINX 번호 수: {len(zip_kinx_numbers)}")
    print(f"ZIP KINX 번호 샘플: {list(zip_kinx_numbers)[:5]}")
    
    # 4. 매칭 분석
    print("\n=== 매칭 분석 ===")
    
    common_numbers = csv_kinx_numbers & zip_kinx_numbers
    csv_only = csv_kinx_numbers - zip_kinx_numbers
    zip_only = zip_kinx_numbers - csv_kinx_numbers
    
    print(f"공통 KINX 번호: {len(common_numbers)}개")
    print(f"CSV에만 있는 번호: {len(csv_only)}개")
    print(f"ZIP에만 있는 번호: {len(zip_only)}개")
    
    if csv_only:
        print(f"CSV에만 있는 번호 샘플: {list(csv_only)[:5]}")
    if zip_only:
        print(f"ZIP에만 있는 번호 샘플: {list(zip_only)[:5]}")
    
    # 5. 구체적 매칭 예시
    print("\n=== 매칭 예시 ===")
    
    # CSV 첫 번째 파일과 대응되는 ZIP 파일 찾기
    first_csv_file = csv_data['responses_v2.csv'][0]['source_file']
    match = re.search(r'KINX(\d+)', first_csv_file)
    if match:
        kinx_num = match.group(1)
        matching_zip = [f for f in zip_files if kinx_num in f]
        print(f"CSV: {first_csv_file}")
        print(f"KINX 번호: {kinx_num}")
        print(f"매칭되는 ZIP: {matching_zip}")
    
    return {
        'csv_data': csv_data,
        'zip_files': zip_files,
        'csv_kinx_numbers': csv_kinx_numbers,
        'zip_kinx_numbers': zip_kinx_numbers,
        'common_numbers': common_numbers
    }

if __name__ == "__main__":
    result = analyze_validate_folder()