import React from 'react';
import ActiveLearningDashboard from './components/Vector1/ActiveLearningDashboard';
import { Cpu, Award } from 'lucide-react';

function App() {
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
                EnFormis <span className="text-emerald-400 font-normal text-sm bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-900/50">Vector 1 Platform</span>
              </h1>
              <p className="text-xs text-gray-500">Manufacturing Intelligence & Active Bayesian DoE Optimizer Core</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="container mx-auto p-4 md:p-8">
        <div className="mb-6">
          <h2 className="text-2xl font-black text-white uppercase tracking-wider flex items-center gap-2">
            <Cpu className="text-emerald-400" />
            Multi-Objective Active Bayesian DoE Optimizer
          </h2>
          <p className="text-sm text-gray-400 mt-1">
            Fits independent Gaussian Process models utilizing qLogNEHVI Expected Hypervolume Improvement to locate Pareto-optimal formulation recipes.
          </p>
        </div>

        <div className="mt-6">
          <ActiveLearningDashboard />
        </div>
      </main>

      <footer className="border-t border-gray-950 bg-black text-center text-xs text-gray-600 py-8 mt-12 uppercase tracking-widest">
        EnFormis Pharmaceutical Manufacturing Suite — Module 3 Team Gamma
      </footer>
    </div>
  );
}

export default App;
