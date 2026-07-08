import React, { useState } from 'react';
import ActiveLearningDashboard from './components/Vector1/ActiveLearningDashboard';
import ScaleUpDashboard from './components/Vector2/ScaleUpDashboard';
import RiskAuditDashboard from './components/Vector3/RiskAuditDashboard';
import { Cpu, Activity, ShieldAlert, Award } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState("v1");

  return (
    <div className="min-h-screen bg-black text-gray-200 font-sans">
      {/* Platform Header */}
      <header className="border-b border-gray-900 bg-gray-950/40 p-4 sticky top-0 backdrop-blur-md z-50">
        <div className="container mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/20 text-emerald-400">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-black text-white tracking-wider uppercase flex items-center gap-2">
                EnFormis <span className="text-emerald-400 font-normal text-sm bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-900/50">Module 3 Core</span>
              </h1>
              <p className="text-xs text-gray-500">Manufacturing Intelligence, Process Scale-Up & GMP Risk Audit platform</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex bg-gray-950 p-1 border border-gray-900 rounded-lg text-sm">
            <button
              onClick={() => setActiveTab("v1")}
              className={`px-4 py-2 font-bold rounded flex items-center gap-2 transition-all ${
                activeTab === "v1"
                  ? "bg-emerald-500 text-black shadow-md shadow-emerald-500/20"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <Cpu className="w-4 h-4" />
              Vector 1: Active Learning
            </button>
            <button
              onClick={() => setActiveTab("v2")}
              className={`px-4 py-2 font-bold rounded flex items-center gap-2 transition-all ${
                activeTab === "v2"
                  ? "bg-emerald-500 text-black shadow-md shadow-emerald-500/20"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <Activity className="w-4 h-4" />
              Vector 2: Scale-Up
            </button>
            <button
              onClick={() => setActiveTab("v3")}
              className={`px-4 py-2 font-bold rounded flex items-center gap-2 transition-all ${
                activeTab === "v3"
                  ? "bg-emerald-500 text-black shadow-md shadow-emerald-500/20"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <ShieldAlert className="w-4 h-4" />
              Vector 3: Risk Audit
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="container mx-auto p-4 md:p-8">
        <div className="mb-6">
          <h2 className="text-2xl font-black text-white uppercase tracking-wider">
            {activeTab === "v1" && "Vector 1 — Multi-Objective Active Bayesian DoE Optimizer"}
            {activeTab === "v2" && "Vector 2 — Digital Twin Scale-Up Simulator"}
            {activeTab === "v3" && "Vector 3 — Risk Audit & Failure Modeler (GMP compliance)"}
          </h2>
          <p className="text-sm text-gray-400 mt-1">
            {activeTab === "v1" && "Fits 8 independent Gaussian Processes to converge to Pareto-optimal recipes."}
            {activeTab === "v2" && "Solves dimensionless scaling laws combined with a pre-trained ML residual corrector layer."}
            {activeTab === "v3" && "Evaluates 5 Critical Quality failure modes to generate the immutable ProcessDevelopmentCard."}
          </p>
        </div>

        <div className="mt-6">
          {activeTab === "v1" && <ActiveLearningDashboard />}
          {activeTab === "v2" && <ScaleUpDashboard />}
          {activeTab === "v3" && <RiskAuditDashboard />}
        </div>
      </main>

      <footer className="border-t border-gray-950 bg-black text-center text-xs text-gray-600 py-8 mt-12 uppercase tracking-widest">
        EnFormis Pharmaceutical Manufacturing Suite — Alpha, Beta, Gamma Integration
      </footer>
    </div>
  );
}

export default App;
