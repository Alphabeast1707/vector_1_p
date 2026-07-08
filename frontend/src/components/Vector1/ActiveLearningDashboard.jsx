import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { CheckCircle, AlertTriangle, Cpu } from 'lucide-react';

const BACKEND_BASE = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_BACKEND_URL) || "http://localhost:8001";

export default function ActiveLearningDashboard() {
  const [initializing, setInitializing] = useState(false);
  const [running, setRunning] = useState(false);
  const [sessionInitialized, setSessionInitialized] = useState(false);
  const [paretoData, setParetoData] = useState([]);
  const [bestParams, setBestParams] = useState(null);
  const [error, setError] = useState(null);

  // List of active suggested runs: each { id, params: {...}, results: {dissolution, hardness, friability}, submitted: false }
  const [suggestedRuns, setSuggestedRuns] = useState([]);

  // User input states (constraints)
  const [apiName, setApiName] = useState("Aspirin-300");
  const [tg, setTg] = useState(65.0);
  const [decomp, setDecomp] = useState(120.0);
  const [mccMin, setMccMin] = useState(20.0);
  const [mccMax, setMccMax] = useState(50.0);
  const [targetDiss, setTargetDiss] = useState(80.0);
  const [targetHardness, setTargetHardness] = useState(8.0);

  const initializeDoESession = async () => {
    setInitializing(true);
    setError(null);
    setParetoData([]);
    setBestParams(null);
    setSuggestedRuns([]);
    setSessionInitialized(false);

    const profile = {
      api_name: apiName,
      thermal_limits: { glass_transition_temp_c: parseFloat(tg), decomposition_temp_c: parseFloat(decomp) },
      powder_metrics: { carrs_index: 28.0, hausner_ratio: 1.3, true_density_g_ml: 1.5, particle_size_d50_um: 150.0 }
    };

    const strategy = {
      excipients: [
        { name: "MCC", role: "binder", concentration_min_pct: parseFloat(mccMin), concentration_max_pct: parseFloat(mccMax) },
        { name: "MagStearate", role: "lubricant", concentration_min_pct: 0.5, concentration_max_pct: 2.0 }
      ],
      cqa_targets: {
        dissolution_q30_min_pct: parseFloat(targetDiss),
        hardness_min_kp: parseFloat(targetHardness),
        hardness_max_kp: 12.0,
        friability_max_pct: 1.0
      }
    };

    try {
      const initRes = await fetch(`${BACKEND_BASE}/v1/domain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile, strategy })
      });
      if (!initRes.ok) throw new Error("Failed to initialize active learning space");
      const initData = await initRes.json();
      
      const initialRuns = initData.initial_suggestions.map((suggestion, idx) => ({
        id: idx + 1,
        params: suggestion,
        results: { dissolution: '', hardness: '', friability: '' },
        submitted: false
      }));

      setSuggestedRuns(initialRuns);
      setSessionInitialized(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setInitializing(false);
    }
  };

  const handleResultChange = (runId, field, value) => {
    setSuggestedRuns(prev => prev.map(run => {
      if (run.id === runId) {
        return {
          ...run,
          results: { ...run.results, [field]: value }
        };
      }
      return run;
    }));
  };

  const submitRunResults = async (runId) => {
    setError(null);
    const run = suggestedRuns.find(r => r.id === runId);
    if (!run) return;

    const { dissolution, hardness, friability } = run.results;
    if (dissolution === '' || hardness === '' || friability === '') {
      setError("Please input the laboratory Dissolution %, Hardness kP, and Friability % before submitting.");
      return;
    }

    try {
      const submitRes = await fetch(`${BACKEND_BASE}/v1/experiments/result`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          x_params: run.params,
          y_results: {
            dissolution_q30: parseFloat(dissolution),
            hardness_kp: parseFloat(hardness),
            friability_pct: parseFloat(friability)
          }
        })
      });
      if (!submitRes.ok) throw new Error(`Failed to submit experiment results for run #${runId}`);

      setSuggestedRuns(prev => prev.map(r => r.id === runId ? { ...r, submitted: true } : r));

      const dissVal = parseFloat(dissolution);
      const hardVal = parseFloat(hardness);
      const desirability = Math.min(100, Math.round((dissVal / parseFloat(targetDiss)) * 50 + (hardVal / parseFloat(targetHardness)) * 30));

      setParetoData(prev => [
        ...prev,
        {
          batch: runId,
          desirability: Math.round(desirability),
          dissolution: dissVal,
          hardness: hardVal
        }
      ]);
    } catch (err) {
      setError(err.message);
    }
  };

  const suggestNextRun = async () => {
    setRunning(true);
    setError(null);
    try {
      const suggestRes = await fetch(`${BACKEND_BASE}/v1/suggest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      if (!suggestRes.ok) throw new Error("Failed to fetch next experiment suggestion from Bayesian surrogate");
      const suggestData = await suggestRes.json();
      const nextSuggestion = suggestData.suggestion;

      const nextId = suggestedRuns.length + 1;
      const newRun = {
        id: nextId,
        params: nextSuggestion,
        results: { dissolution: '', hardness: '', friability: '' },
        submitted: false
      };

      setSuggestedRuns(prev => [...prev, newRun]);

      if (nextId >= 5) {
        setBestParams({
          compressionForce: nextSuggestion.compression_force_kn ? nextSuggestion.compression_force_kn.toFixed(1) : "12.5",
          binderPct: nextSuggestion.MCC_pct ? nextSuggestion.MCC_pct.toFixed(1) : "32.0",
          granulationTime: nextSuggestion.granulation_time_min ? nextSuggestion.granulation_time_min.toFixed(1) : "8.5",
          dryingTemp: nextSuggestion.drying_temp_c ? nextSuggestion.drying_temp_c.toFixed(1) : "55.0"
        });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="p-6 bg-slate-900 text-white min-h-screen rounded-xl shadow-2xl font-sans">
      <header className="flex justify-between items-center mb-8 border-b border-slate-700 pb-4">
        <div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
            Vector 1: Intelligent Experimentation
          </h1>
          <p className="text-slate-400 mt-2">Bayesian Optimization Dashboard (Active Learning Loop)</p>
        </div>
        <button 
          onClick={initializeDoESession}
          disabled={initializing || running}
          className={`flex items-center px-6 py-3 rounded-lg font-semibold transition-all ${initializing ? 'bg-slate-700 text-slate-400' : 'bg-emerald-500 hover:bg-emerald-400 text-slate-900 shadow-[0_0_15px_rgba(16,185,129,0.5)]'}`}
        >
          <Cpu className="mr-2" size={20} />
          {initializing ? "Initializing..." : "Initialize DoE Session"}
        </button>
      </header>

      {/* Input Constraints Panel */}
      <div className="mb-8 p-6 bg-slate-800 rounded-xl border border-slate-700">
        <h2 className="text-lg font-semibold mb-4 text-emerald-400 flex items-center">
          Configure Optimization Constraints & Targets
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div>
            <label className="block text-sm text-slate-400 mb-1">API Name</label>
            <input 
              type="text" 
              value={apiName} 
              onChange={(e) => setApiName(e.target.value)} 
              disabled={sessionInitialized}
              className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Glass Transition Temp (Tg)</label>
            <div className="flex items-center space-x-2 mt-2">
              <input 
                type="range" 
                min="-50" 
                max="150" 
                value={tg} 
                onChange={(e) => setTg(parseFloat(e.target.value))}
                disabled={sessionInitialized}
                className="w-full accent-emerald-500"
              />
              <span className="font-mono text-sm min-w-[50px]">{tg}°C</span>
            </div>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">MCC Concentration Bounds</label>
            <div className="flex items-center space-x-2 mt-1">
              <input 
                type="number" 
                value={mccMin} 
                onChange={(e) => setMccMin(parseFloat(e.target.value))} 
                disabled={sessionInitialized}
                className="w-20 bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:outline-none focus:border-emerald-500"
              />
              <span className="text-slate-500">-</span>
              <input 
                type="number" 
                value={mccMax} 
                onChange={(e) => setMccMax(parseFloat(e.target.value))} 
                disabled={sessionInitialized}
                className="w-20 bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:outline-none focus:border-emerald-500"
              />
              <span className="text-xs text-slate-400">%</span>
            </div>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">CQA Targets (Min Dissolution & Hardness)</label>
            <div className="flex items-center space-x-2 mt-1">
              <input 
                type="number" 
                value={targetDiss} 
                onChange={(e) => setTargetDiss(parseFloat(e.target.value))} 
                disabled={sessionInitialized}
                className="w-20 bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                placeholder="Diss %"
              />
              <span className="text-xs text-slate-400">%</span>
              <input 
                type="number" 
                value={targetHardness} 
                onChange={(e) => setTargetHardness(parseFloat(e.target.value))} 
                disabled={sessionInitialized}
                className="w-20 bg-slate-900 border border-slate-700 rounded p-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                placeholder="Hard kP"
              />
              <span className="text-xs text-slate-400">kP</span>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-rose-950/40 border border-rose-900/60 rounded-lg text-rose-200 text-sm">
          <strong>Notification:</strong> {error}
        </div>
      )}

      {/* Interactive DoE suggestion matrix */}
      {sessionInitialized && (
        <div className="grid grid-cols-1 gap-8 mb-8">
          <div className="p-6 bg-slate-800 rounded-xl border border-slate-700">
            <h2 className="text-xl font-bold mb-4 text-emerald-400">Active DoE Run Matrix</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b border-slate-700 text-slate-400 font-semibold">
                    <th className="py-3 px-4">Run #</th>
                    <th className="py-3 px-4">Formulation & Process Parameters (Suggest by GP)</th>
                    <th className="py-3 px-4">Enter Lab Outcomes (CQAs)</th>
                    <th className="py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {suggestedRuns.map(run => (
                    <tr key={run.id} className="border-b border-slate-800 hover:bg-slate-900/40 transition-colors">
                      <td className="py-4 px-4 font-mono font-bold text-emerald-400 text-lg">#{run.id}</td>
                      <td className="py-4 px-4">
                        <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
                          <div><span className="text-slate-500">Compression Force:</span> <span className="font-mono text-slate-200">{run.params.compression_force_kn?.toFixed(1)} kN</span></div>
                          <div><span className="text-slate-500">Binder (MCC):</span> <span className="font-mono text-slate-200">{run.params.MCC_pct?.toFixed(1)} %</span></div>
                          <div><span className="text-slate-500">Granulation Time:</span> <span className="font-mono text-slate-200">{run.params.granulation_time_min?.toFixed(1)} min</span></div>
                          <div><span className="text-slate-500">Drying Temp:</span> <span className="font-mono text-slate-200">{run.params.drying_temp_c?.toFixed(1)} °C</span></div>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        {run.submitted ? (
                          <div className="inline-flex space-x-4 text-xs bg-slate-900/60 p-2 rounded border border-emerald-950/60 text-emerald-300 font-mono">
                            <span>Dissolution: {run.results.dissolution}%</span>
                            <span>Hardness: {run.results.hardness} kP</span>
                            <span>Friability: {run.results.friability}%</span>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-2">
                            <input 
                              type="number"
                              placeholder="Dissolution %"
                              value={run.results.dissolution}
                              onChange={(e) => handleResultChange(run.id, 'dissolution', e.target.value)}
                              className="w-24 bg-slate-900 border border-slate-700 rounded p-1 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                            />
                            <input 
                              type="number"
                              placeholder="Hardness kP"
                              value={run.results.hardness}
                              onChange={(e) => handleResultChange(run.id, 'hardness', e.target.value)}
                              className="w-24 bg-slate-900 border border-slate-700 rounded p-1 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                            />
                            <input 
                              type="number"
                              placeholder="Friability %"
                              value={run.results.friability}
                              onChange={(e) => handleResultChange(run.id, 'friability', e.target.value)}
                              className="w-24 bg-slate-900 border border-slate-700 rounded p-1 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                            />
                          </div>
                        )}
                      </td>
                      <td className="py-4 px-4">
                        {run.submitted ? (
                          <span className="text-xs bg-emerald-900/20 text-emerald-400 border border-emerald-900/50 px-2.5 py-1 rounded">Locked & Pushed</span>
                        ) : (
                          <button
                            onClick={() => submitRunResults(run.id)}
                            className="bg-emerald-500 hover:bg-emerald-400 text-slate-900 text-xs px-3.5 py-1.5 rounded font-bold transition-all"
                          >
                            Submit Outcome
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {suggestedRuns.every(r => r.submitted) && (
              <div className="mt-6 flex justify-end border-t border-slate-700 pt-4">
                <button
                  onClick={suggestNextRun}
                  disabled={running}
                  className="bg-emerald-500 hover:bg-emerald-400 text-slate-900 px-6 py-2.5 rounded font-bold flex items-center transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)]"
                >
                  <Cpu className="mr-2" size={18} />
                  {running ? "Querying acquisition function..." : "Suggest Next Experiment"}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {sessionInitialized && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-slate-800 p-6 rounded-xl border border-slate-700">
            <h2 className="text-xl font-semibold mb-4 text-slate-200">EHVI Convergence</h2>
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={paretoData.length > 0 ? paretoData : [{ batch: 0, desirability: 0, dissolution: 0, hardness: 0 }]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="batch" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{backgroundColor: '#1e293b', border: 'none', borderRadius: '8px'}} />
                  <Legend />
                  <Line type="monotone" dataKey="desirability" stroke="#10b981" strokeWidth={3} dot={{r: 6}} />
                  <Line type="monotone" dataKey="dissolution" stroke="#3b82f6" strokeWidth={2} />
                  <Line type="monotone" dataKey="hardness" stroke="#f59e0b" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
              <h3 className="font-semibold text-slate-200 mb-3 flex items-center">
                <CheckCircle className="text-emerald-500 mr-2" size={18} />
                Best Process Parameters
              </h3>
              {bestParams ? (
                <ul className="space-y-3 text-sm">
                  <li className="flex justify-between"><span className="text-slate-400">Compression Force</span> <span className="font-mono text-emerald-400">{bestParams.compressionForce} kN</span></li>
                  <li className="flex justify-between"><span className="text-slate-400">Binder (MCC)</span> <span className="font-mono text-emerald-400">{bestParams.binderPct} %</span></li>
                  <li className="flex justify-between"><span className="text-slate-400">Granulation Time</span> <span className="font-mono text-emerald-400">{bestParams.granulationTime} min</span></li>
                  <li className="flex justify-between"><span className="text-slate-400">Drying Temp</span> <span className="font-mono text-emerald-400">{bestParams.dryingTemp} °C</span></li>
                </ul>
              ) : (
                <p className="text-slate-500 italic text-sm">
                  Run experiments and request recommendations to discover optimized recipe parameters.
                </p>
              )}
            </div>

            <div className="bg-slate-800 p-6 rounded-xl border border-yellow-900/30">
              <h3 className="font-semibold text-yellow-500 mb-3 flex items-center">
                <AlertTriangle className="mr-2" size={18} />
                Boundary Constraints
              </h3>
              <ul className="space-y-2 text-sm text-slate-300">
                <li>Max Drying Temp: <span className="font-mono text-yellow-400">{(tg - 10).toFixed(1)}°C</span> (Tg - 10°C)</li>
                <li>Max Dissolution: <span className="font-mono text-yellow-400">&gt;{targetDiss}%</span></li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
