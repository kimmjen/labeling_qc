import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  FileCheck,
  Brain,
  TrendingUp,
  Upload,
  Settings,
  BarChart3,
  Zap
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import FileUpload from './components/FileUpload';
import AIPredictor from './components/AIPredictor';
import TrendAnalysis from './components/TrendAnalysis';
import './App.css';

type TabType = 'dashboard' | 'upload' | 'ai-predict' | 'trends' | 'settings';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');

  const tabs = [
    { id: 'dashboard', label: '대시보드', icon: BarChart3 },
    { id: 'upload', label: '파일 검수', icon: Upload },
    { id: 'ai-predict', label: 'AI 예측', icon: Brain },
    { id: 'trends', label: '트렌드 분석', icon: TrendingUp },
    { id: 'settings', label: '설정', icon: Settings },
  ] as const;

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard />;
      case 'upload':
        return <FileUpload />;
      case 'ai-predict':
        return <AIPredictor />;
      case 'trends':
        return <TrendAnalysis />;
      case 'settings':
        return (
          <div className="card">
            <h2 className="text-2xl font-bold mb-4">시스템 설정</h2>
            <p className="text-gray-600">설정 기능은 개발 중입니다...</p>
          </div>
        );
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">라벨링 QC</h1>
                  <p className="text-xs text-gray-500">AI 품질 검수 플랫폼</p>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <div className="w-2 h-2 bg-success-500 rounded-full"></div>
                <span>시스템 정상</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 네비게이션 */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as TabType)}
                  className={`
                    relative flex items-center space-x-2 px-3 py-4 text-sm font-medium transition-colors
                    ${isActive 
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-500 hover:text-gray-700 hover:border-b-2 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>

                  {isActive && (
                    <motion.div
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600"
                      layoutId="activeTab"
                      initial={false}
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* 메인 콘텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.2 }}
        >
          {renderContent()}
        </motion.div>
      </main>
    </div>
  );
}

export default App;
