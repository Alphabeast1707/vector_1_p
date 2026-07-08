import React, { useState } from 'react';
import { CheckCircle, AlertTriangle, Cpu, ArrowRight } from 'lucide-react';

const BACKEND_BASE = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_BACKEND_URL) || "http://localhost:8001";

export default function ScaleUpDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  // Form states
  const [apiName, setApiName] = useState("Paracetamol");
  const [trueDensity, setTrueDensity] = useState(1.25);
  const [carrsIndex, setCarrsIndex] = useState(18.5);
  const [d50, setD50] = useState(125.0);

  const [labRpm, setLabRpm] = useState(400);
  const [labForce, setLabForce] = useState(12.0);
  const [labTemp, setLabTemp] = useState(50.0);
  const [labSpray, setLabSpray] = useState(15.0);

  const [labMachine, setLabMachine] = useState("lab_granulator_10L");
  const [commMachine, setCommMachine] = useState("commercial_granulator_300L");

  const runScaleup = async () => {
    setLoading(true);
    setError(null);
    setResults(null);

    const payload = {
      profile: {
        api_name: apiName,
        thermal_limits: { glass_transition_temp_c: 58.0, decomposition_temp_c: 210.0 },
        powder_metrics: {
          carrs_index: parseFloat(carrsIndex),
          hausner_ratio: 1.2,
          true_density_g_ml: parseFloat(trueDensity),
          particle_size_d50_um: parseFloat(d50)
        }
      },
      lab_params: {
        impeller_rpm: parseFloat(labRpm),
        compression_force_kn: parseFloat(labForce),
        drying_temp_c: parseFloat(labTemp),
        spray_rate_g_min: parseFloat(labSpray)
      },
      lab_machine_id: labMachine,
      comm_machine_id: commMachine
    };

    try {
      const res = await fetch(`${BACKEND_BASE}/v2/scaleup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error(`Failed with status ${res.status}`);
      }

      const data = await res.json();
      setResults(data);
    } catch (e) {
      setError(e.message || "Failed to execute Scale-up computation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 bg-black text-gray-200">
      {/* Parameters Panel */}
      <div className="lg:col-span-1 bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
        <h2 className="text-xl font-bold text-emerald-400 mb-4 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-emerald-500" />
          Lab Scale Recipe Inputs
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">API & Powder Metrics</label>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <span className="text-[10px] text-gray-500">API Name</span>
                <input
                  type="text"
                  value={apiName}
                  onChange={(e) => setApiName(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <span className="text-[10px] text-gray-500">True Density (g/mL)</span>
                <input
                  type="number"
                  step="0.01"
                  value={trueDensity}
                  onChange={(e) => setTrueDensity(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <span className="text-[10px] text-gray-500">Carr's Index</span>
                <input
                  type="number"
                  step="0.1"
                  value={carrsIndex}
                  onChange={(e) => setCarrsIndex(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <span className="text-[10px] text-gray-500">Particle Size D50 (µm)</span>
                <input
                  type="number"
                  value={d50}
                  onChange={(e) => setD50(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Lab Parameters</label>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <span className="text-[10px] text-gray-500">Impeller RPM</span>
                <input
                  type="number"
                  value={labRpm}
                  onChange={(e) => setLabRpm(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <span className="text-[10px] text-gray-500">Compression Force (kN)</span>
                <input
                  type="number"
                  step="0.1"
                  value={labForce}
                  onChange={(e) => setLabForce(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <span className="text-[10px] text-gray-500">Drying Temp (°C)</span>
                <input
                  type="number"
                  step="0.1"
                  value={labTemp}
                  onChange={(e) => setLabTemp(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <span className="text-[10px] text-gray-500">Spray Rate (g/min)</span>
                <input
                  type="number"
                  step="0.1"
                  value={labSpray}
                  onChange={(e) => setLabSpray(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Equipment Selection</label>
            <div className="space-y-2">
              <div>
                <span className="text-[10px] text-gray-500">Lab Granulator</span>
                <select
                  value={labMachine}
                  onChange={(e) => setLabMachine(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                >
                  <option value="lab_granulator_10L">Lab Scale Granulator (10L)</option>
                </select>
              </div>
              <div>
                <span className="text-[10px] text-gray-500">Commercial Granulator</span>
                <select
                  value={commMachine}
                  onChange={(e) => setCommMachine(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                >
                  <option value="commercial_granulator_300L">Commercial Production Granulator (300L)</option>
                </select>
              </div>
            </div>
          </div>

          <button
            onClick={runScaleup}
            disabled={loading}
            className="w-full py-3 px-4 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-black font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {loading ? "Scaling Up Recipe..." : "Calculate Scale-Up"}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Results Panel */}
      <div className="lg:col-span-2 space-y-6">
        {error && (
          <div className="bg-red-950/30 border border-red-900/50 rounded-xl p-4 text-red-400 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5" />
            <div>
              <h3 className="font-bold">Computation Error</h3>
              <p className="text-xs mt-1 text-red-300">{error}</p>
            </div>
          </div>
        )}

        {!results && !loading && !error && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center text-gray-500 flex flex-col items-center justify-center h-full min-h-[300px]">
            <Cpu className="w-12 h-12 text-gray-700 mb-3" />
            <h3 className="text-lg font-bold text-gray-400">Scale-Up Computation Ready</h3>
            <p className="text-sm mt-1 max-w-md">Input your laboratory formulation parameters on the left and click "Calculate Scale-Up" to run mechanistic-ML hybrid scaling.</p>
          </div>
        )}

        {loading && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center text-gray-400 flex flex-col items-center justify-center h-full min-h-[300px]">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-500 mb-3"></div>
            <p className="text-sm">Solving scaling laws and evaluating machine-learning residual corrector weights...</p>
          </div>
        )}

        {results && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Primary Process Parameters */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
              <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center gap-2 border-b border-gray-800 pb-2">
                <CheckCircle className="w-5 h-5 text-emerald-500" />
                Commercial Parameters
              </h3>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-950 p-3 rounded border border-gray-850">
                  <span className="block text-[10px] text-gray-400 uppercase tracking-wider">Impeller Speed</span>
                  <span className="text-xl font-bold text-emerald-400">{results.commercial_params.impeller_rpm}</span>
                  <span className="text-[10px] block text-gray-500">RPM</span>
                </div>
                <div className="bg-gray-950 p-3 rounded border border-gray-850">
                  <span className="block text-[10px] text-gray-400 uppercase tracking-wider">Compression Force</span>
                  <span className="text-xl font-bold text-emerald-400">{results.commercial_params.compression_force_kn}</span>
                  <span className="text-[10px] block text-gray-500">kN</span>
                </div>
                <div className="bg-gray-950 p-3 rounded border border-gray-850">
                  <span className="block text-[10px] text-gray-400 uppercase tracking-wider">Drying Temperature</span>
                  <span className="text-xl font-bold text-emerald-400">{results.commercial_params.drying_temp_c}</span>
                  <span className="text-[10px] block text-gray-500">°C</span>
                </div>
                <div className="bg-gray-950 p-3 rounded border border-gray-850">
                  <span className="block text-[10px] text-gray-400 uppercase tracking-wider">Spray Rate</span>
                  <span className="text-xl font-bold text-emerald-400">{results.commercial_params.spray_rate_g_min}</span>
                  <span className="text-[10px] block text-gray-500">g/min</span>
                </div>
                <div className="bg-gray-950 p-3 rounded border border-gray-850">
                  <span className="block text-[10px] text-gray-400 uppercase tracking-wider">Dwell Time</span>
                  <span className="text-xl font-bold text-emerald-400">{results.commercial_params.dwell_time_ms}</span>
                  <span className="text-[10px] block text-gray-500">ms</span>
                </div>
                <div className="bg-gray-950 p-3 rounded border border-gray-850">
                  <span className="block text-[10px] text-gray-400 uppercase tracking-wider">Batch Size</span>
                  <span className="text-xl font-bold text-emerald-400">{results.commercial_params.batch_size_kg}</span>
                  <span className="text-[10px] block text-gray-500">kg</span>
                </div>
              </div>
            </div>

            {/* Dimensional Analysis & Metadata */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
              <h3 className="text-lg font-bold text-gray-100 mb-2 flex items-center gap-2 border-b border-gray-800 pb-2">
                <Cpu className="w-5 h-5 text-gray-400" />
                Scale-Up Dimensional Verification
              </h3>

              <div className="space-y-3">
                <div className="flex justify-between items-center text-sm border-b border-gray-800 pb-2">
                  <span className="text-gray-400 font-medium">Scaling Law Strategy</span>
                  <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-950/40 text-emerald-400 border border-emerald-900/50 uppercase tracking-wider">
                    {results.scaling_law_used} Similarity
                  </span>
                </div>

                <div className="flex justify-between items-center text-sm border-b border-gray-800 pb-2">
                  <span className="text-gray-400 font-medium">Confidence Engine</span>
                  <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-950/40 text-emerald-400 border border-emerald-900/50 uppercase tracking-wider">
                    {results.scaleup_confidence.replace("_", " ")}
                  </span>
                </div>

                <div className="flex justify-between items-center text-sm border-b border-gray-800 pb-2">
                  <span className="text-gray-400 font-medium">Impeller Reynolds Number (Re)</span>
                  <span className="font-bold text-emerald-400">{results.reynolds_number.toLocaleString()}</span>
                </div>

                {/* Reynolds Warning Alert */}
                {results.reynolds_warning ? (
                  <div className="bg-amber-950/20 border border-amber-900/30 rounded p-3 text-amber-400 text-xs flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-bold mb-1">Reynolds Transition Alert</p>
                      <p className="text-gray-400">Impeller Reynolds number is below 10,000. Under current speed parameters, fully turbulent blending kinetics are not fully established in the production granulator. Mixing risks might occur.</p>
                    </div>
                  </div>
                ) : (
                  <div className="bg-emerald-950/10 border border-emerald-900/20 rounded p-3 text-emerald-400 text-xs flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-bold mb-1">Reynolds Check Passed</p>
                      <p className="text-gray-400">Re &gt; 10,000. Mixing regime in the commercial scale granulator is verified as fully turbulent, satisfying mass transfer similarity.</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
