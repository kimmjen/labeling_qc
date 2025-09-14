// API 통신을 위한 타입 정의
export interface QualityIssue {
  rule_id: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  file_path: string;
  element_id?: string;
  page_index?: number;
  category: string;
  suggested_fix?: string;
  auto_fixable: boolean;
}

export interface AIAnalysis {
  anomalies: Array<{
    type: string;
    message: string;
    severity: 'error' | 'warning' | 'info';
  }>;
  optimizations: {
    immediate_actions: string[];
    process_improvements: string[];
    automation_opportunities: string[];
  };
  quality_score: number;
}

// 백엔드 API와 일치하는 ValidationResult 타입
export interface ValidationResult {
  filename: string;
  issues_count: number;
  issues: QualityIssue[];
  ai_analysis: AIAnalysis;
}

export interface LabelPrediction {
  predicted_label: string;
  confidence: number;
  reason: string;
  alternatives: Array<{
    label: string;
    confidence: number;
    score: number;
  }>;
}

export interface TrendData {
  date: string;
  issue_count: number;
  accuracy: number;
}

// API 요청/응답 타입
export interface LabelPredictionRequest {
  text: string;
  context?: Record<string, any>;
}

export interface TrendAnalysisRequest {
  history: Array<Record<string, any>>;
}
