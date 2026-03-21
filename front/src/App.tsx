import React, { useState } from 'react';
import {
  Layers,
  TrendingUp,
  GitBranch,
  ShieldCheck,
} from 'lucide-react';
import Page1NewSession from './components/Page1NewSession';
import Page2Dashboard from './components/Page2Dashboard';
import Page3Canvas from './components/Page3Canvas';
import Page4Execution from './components/Page4Execution';
import Page5Release from './components/Page5Release';

interface Page {
  id: number;
  key: string;
  name: string;
  icon: React.ReactNode;
  desc: string;
}

const pages: Page[] = [
  { id: 1, key: 'newSession', name: '需求/意图澄清', icon: <Layers className="w-4 h-4" />, desc: '把业务意图转成可执行交付任务' },
  { id: 2, key: 'dashboard', name: '关键流程确认', icon: <TrendingUp className="w-4 h-4" />, desc: 'AI 正在托管推进，你只处理关键决策' },
  { id: 3, key: 'canvas', name: '跨域协议确认', icon: <Layers className="w-4 h-4" />, desc: '从 UI 意图到 BFF/SOA 协议的一体化中轴' },
  { id: 4, key: 'execution', name: '多智能体执行台', icon: <GitBranch className="w-4 h-4" />, desc: '由主控编排、由专业智能体团队并行交付' },
  { id: 5, key: 'release', name: '需求验收与发布', icon: <ShieldCheck className="w-4 h-4" />, desc: '不是看过程是否热闹，而是看结果是否可交付' },
];

export default function App() {
  const [activePageId, setActivePageId] = useState(1);

  const activePageData = pages.find(p => p.id === activePageId) || pages[0];

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-800 flex flex-col w-full">
      {/* 顶部全局导航 */}
      <header className="bg-slate-900 text-white shadow-lg z-50 sticky top-0">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between md:justify-start h-16">
            {/* Logo */}
            <div className="flex items-center space-x-3 shrink-0 cursor-pointer hover:opacity-90 transition-opacity">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-xl shadow-inner shadow-blue-400/30">
                O
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-lg leading-tight tracking-wide">OxygenSE</span>
                <span className="text-slate-400 text-[10px] uppercase tracking-wider">Workspace</span>
              </div>
            </div>

            {/* 视觉分隔符 (仅 Desktop) */}
            <div className="hidden md:block h-6 w-px bg-slate-700 mx-6"></div>

            {/* Desktop Nav */}
            <div className="hidden md:flex space-x-1 overflow-x-auto">
              {pages.map(page => (
                <button
                  key={page.id}
                  onClick={() => setActivePageId(page.id)}
                  className={`px-4 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ease-out flex items-center space-x-2 whitespace-nowrap active:scale-95 ${
                    activePageId === page.id
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/50 ring-1 ring-blue-500 font-bold'
                      : 'text-slate-400 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <span className={`flex justify-center items-center w-4 h-4 rounded-full text-[9px] ${
                    activePageId === page.id ? 'bg-white text-blue-600' : 'bg-slate-700 text-slate-300'
                  }`}>
                    {page.id}
                  </span>
                  <span>{page.name}</span>
                </button>
              ))}
            </div>

            {/* Mobile Nav */}
            <div className="md:hidden flex items-center text-slate-400">
              <span className="text-xs bg-slate-800 px-3 py-1 rounded-full border border-slate-700">
                Step {activePageId}/5
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* 页面标题区 */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center">
            <span className="w-8 h-8 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mr-3">
              {activePageData.icon}
            </span>
            {activePageData.name}
          </h1>
          <p className="text-slate-500 text-sm mt-1 ml-11 max-w-3xl">
            {activePageData.desc}
          </p>
        </div>
      </div>

      {/* Mobile 步骤导航 */}
      <div className="md:hidden bg-slate-900 border-t border-slate-800 px-4 py-2">
        <div className="flex space-x-1 overflow-x-auto">
          {pages.map(page => (
            <button
              key={page.id}
              onClick={() => setActivePageId(page.id)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                activePageId === page.id
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {page.id}. {page.name}
            </button>
          ))}
        </div>
      </div>

      {/* 页面内容渲染区 */}
      <main className="flex-1 w-full max-w-[1440px] mx-auto p-4 sm:p-6 lg:p-8">
        <div key={activePageId}>
          {activePageId === 1 && <Page1NewSession onNext={() => setActivePageId(2)} />}
          {activePageId === 2 && <Page2Dashboard onNavigate={setActivePageId} />}
          {activePageId === 3 && <Page3Canvas onNavigate={setActivePageId} />}
          {activePageId === 4 && <Page4Execution />}
          {activePageId === 5 && <Page5Release />}
        </div>
      </main>
    </div>
  );
}
