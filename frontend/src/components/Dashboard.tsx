import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FileCheck,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Activity,
  Zap,
  BarChart3,
  PieChart
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart as RechartsPieChart, Pie, Cell } from 'recharts';

interface DashboardStats {
  totalFiles: number;
  issuesFound: number;
  accuracyRate: number;
  aiPredictions: number;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalFiles: 1247,
    issuesFound: 89,
    accuracyRate: 94.2,
    aiPredictions: 567
  });

  // 주간 품질 트렌드 데이터 (이미지의 주간 동향 차트와 유사)
  const weeklyTrend = [
    { day: '월', quality: 85, issues: 15 },
    { day: '화', quality: 92, issues: 8 },
    { day: '수', quality: 88, issues: 12 },
    { day: '목', quality: 95, issues: 5 },
    { day: '금', quality: 97, issues: 3 },
    { day: '토', quality: 93, issues: 7 },
    { day: '일', quality: 100, issues: 0 },
  ];

  // 이슈 유형별 분포 데이터 (이미지의 파이 차트와 유사)
  const issueDistribution = [
    { name: 'R001 빈텍스트', value: 35, color: '#EF4444' },
    { name: 'R004 날짜형식', value: 28, color: '#F59E0B' },
    { name: '라벨 타입', value: 20, color: '#3B82F6' },
    { name: '기타 오류', value: 17, color: '#6B7280' }
  ];

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">품질 검수 대시보드</h1>
          <p className="text-sm text-gray-600 mt-1">실시간 라벨링 품질 모니터링</p>
        </div>
        <div className="flex items-center space-x-2 text-sm text-green-600">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span>시스템 정상</span>
        </div>
      </div>

      {/* 주요 통계 카드 (이미지 상단의 4개 메트릭과 유사) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-lg p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">총 파일 수</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalFiles.toLocaleString()}</p>
            </div>
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileCheck className="w-5 h-5 text-blue-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-lg p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">발견된 이슈</p>
              <p className="text-2xl font-bold text-gray-900">{stats.issuesFound}</p>
            </div>
            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-lg p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">정확도</p>
              <p className="text-2xl font-bold text-gray-900">{stats.accuracyRate}%</p>
            </div>
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-lg p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">AI 예측 수</p>
              <p className="text-2xl font-bold text-gray-900">{stats.aiPredictions}</p>
            </div>
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-purple-600" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* 차트 영역 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 주간 품질 트렌드 (이미지의 주간 동향 바 차트) */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white rounded-lg p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">주간 품질 트렌드</h3>
            <BarChart3 className="w-5 h-5 text-gray-400" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={weeklyTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="day" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Bar dataKey="quality" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-between mt-2 text-sm text-gray-600">
            <span>품질 점수</span>
            <span className="text-green-600 flex items-center">
              <TrendingUp className="w-4 h-4 mr-1" />
              +2.3% 전주 대비
            </span>
          </div>
        </motion.div>

        {/* 이슈 유형별 분포 (이미지의 파이 차트) */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white rounded-lg p-6 shadow-sm border border-gray-200"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">이슈 유형별 분포</h3>
            <PieChart className="w-5 h-5 text-gray-400" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RechartsPieChart>
                <Pie
                  data={issueDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {issueDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [`${value}%`, '비율']} />
              </RechartsPieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {issueDistribution.map((item, index) => (
              <div key={index} className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-xs text-gray-600">{item.name}</span>
                <span className="text-xs font-medium text-gray-900">{item.value}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* 최근 활동 및 시스템 상태 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 최근 활동 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="lg:col-span-2 bg-white rounded-lg p-6 shadow-sm border border-gray-200"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">최근 활동</h3>
          <div className="space-y-3">
            {[
              { type: 'upload', message: 'TLAW1202000305_TP.json 검수 완료', time: '2분 전', status: 'success' },
              { type: 'ai', message: 'AI가 12개 라벨 예측 완료', time: '5분 전', status: 'info' },
              { type: 'error', message: 'R004 규칙 위반 3건 발견', time: '8분 전', status: 'warning' },
              { type: 'fix', message: '자동 수정 15건 적용', time: '12분 전', status: 'success' },
            ].map((activity, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className={`w-2 h-2 rounded-full mt-2 ${
                  activity.status === 'success' ? 'bg-green-500' :
                  activity.status === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">{activity.message}</p>
                  <p className="text-xs text-gray-500">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* 시스템 상태 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="bg-white rounded-lg p-6 shadow-sm border border-gray-200"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">시스템 상태</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">API 서버</span>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-xs text-green-600">정상</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">AI 엔진</span>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-xs text-green-600">정상</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">데이터베이스</span>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-xs text-green-600">정상</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">메모리 사용량</span>
              <span className="text-xs text-gray-900">67%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full" style={{ width: '67%' }}></div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* 빠른 액션 버튼들 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.9 }}
        className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 border border-blue-200"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">빠른 액션</h3>
        <div className="flex flex-wrap gap-3">
          <button className="btn-primary text-sm">
            <FileCheck className="w-4 h-4 mr-2" />
            새 파일 검수
          </button>
          <button className="btn-secondary text-sm">
            <Zap className="w-4 h-4 mr-2" />
            AI 예측 실행
          </button>
          <button className="btn-secondary text-sm">
            <BarChart3 className="w-4 h-4 mr-2" />
            상세 리포트
          </button>
          <button className="btn-secondary text-sm">
            <Activity className="w-4 h-4 mr-2" />
            시스템 모니터링
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default Dashboard;
