#!/usr/bin/env python3
"""
라벨링 품질 검수 도구 메인 패키지
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 한 번만 추가
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

__version__ = "1.0.0"
__author__ = "Quality Control Team"
__description__ = "라벨링 품질 검수 자동화 도구"
