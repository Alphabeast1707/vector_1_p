import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, ShieldAlert, Download, Activity, FileText } from 'lucide-react';

const BACKEND_BASE = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_BACKEND_URL) || "http://localhost:8001";

export default function RiskAuditDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);

  // Inputs
  const [apiName, setApiName] = useState("Paracetamol");
  const [trueDensity, setTrueDensity] = useState(1.25);
  const [carrsIndex, setCarrsIndex] = useState(18.5);
  const [d50, setD50] = useState(125.0);

  // Commercial scale inputs (Vector 2 results)
  const [rpm, setRpm] = useState(200);
  const [force, setForce] = useState(13.8);
  const [temp, setTemp] = useState(50.0);
  
  // Optional extra parameters
  const [moisture, setMoisture] = useState(4.5);
  const [binder, setBinder] = useState(3.5);

  const runRiskAudit = async () => {
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
      commercial_params: {
        impeller_rpm: parseFloat(rpm),
        compression_force_kn: parseFloat(force),
        drying_temp_c: parseFloat(temp),
        inlet_air_humidity_pct_rh: 40.0,
        dwell_time_ms: 105.0,
        batch_size_kg: 150.0,
        spray_rate_g_min: 450.0
      },
      moisture_pct: parseFloat(moisture),
      binder_pct: parseFloat(binder)
    };

    try {
      const res = await fetch(`${BACKEND_BASE}/v3/risk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error(`Failed with status ${res.status}`);
      }

      const data = await res.json();
      setResults(data.process_development_card);
    } catch (e) {
      setError(e.message || "Failed to execute Risk Audit process");
    } finally {
      setLoading(false);
    }
  };

  const exportJSON = () => {
    if (!results) return;
    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(
      JSON.stringify(results, null, 2)
    )}`;
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", jsonString);
    downloadAnchor.setAttribute("download", `ProcessDevelopmentCard_${results.api_name}_v${results.version}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const getTrafficColor = (level) => {
    if (level === "GREEN") return "text-emerald-500 bg-emerald-950/40 border-emerald-900/50";
    if (level === "YELLOW") return "text-amber-500 bg-amber-950/40 border-amber-900/50";
    return "text-red-500 bg-red-950/40 border-red-900/50";
  };

  const getBannerStyle = (rec) => {
    if (rec === "PROCEED") return "bg-emerald-950/40 border-emerald-800 text-emerald-400";
    if (rec === "ADJUST_CPPS") return "bg-amber-950/40 border-amber-800 text-amber-400";
    return "bg-red-950/40 border-red-800 text-red-400";
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 bg-black text-gray-200">
      {/* Parameters Input */}
      <div className="lg:col-span-1 bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg space-y-4">
        <h2 className="text-xl font-bold text-emerald-400 mb-2 flex items-center gap-2">
          <Activity className="w-5 h-5 text-emerald-500" />
          Risk Input Setup
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Commercial Parameters</label>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <span className="text-[10px] text-gray-500">Impeller Speed (RPM)</span>
                <input
                  type="number"
                  value={rpm}
                  onChange={(e) => setRpm(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <span className="text-[10px] text-gray-500">Compression Force (kN)</span>
                <input
                  type="number"
                  step="0.1"
                  value={force}
                  onChange={(e) => setForce(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="col-span-2">
                <span className="text-[10px] text-gray-500">Drying Temperature (°C)</span>
                <input
                  type="number"
                  step="0.1"
                  value={temp}
                  onChange={(e) => setTemp(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Excipient / Formulation Ratios</label>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <span className="text-[10px] text-gray-500">Granulation Moisture %</span>
                <input
                  type="number"
                  step="0.1"
                  value={moisture}
                  onChange={(e) => setMoisture(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <span className="text-[10px] text-gray-500">Binder Percentage %</span>
                <input
                  type="number"
                  step="0.1"
                  value={binder}
                  onChange={(e) => setBinder(e.target.value)}
                  className="w-full bg-gray-950 border border-gray-800 rounded p-2 text-sm text-gray-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>
          </div>

          <button
            onClick={runRiskAudit}
            disabled={loading}
            className="w-full py-3 px-4 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-black font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            {loading ? "Simulating Risks (N=500)..." : "Execute Risk Audit"}
          </button>
        </div>
      </div>

      {/* Audit Output */}
      <div className="lg:col-span-2 space-y-6">
        {error && (
          <div className="bg-red-950/30 border border-red-900/50 rounded-xl p-4 text-red-400 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5" />
            <div>
              <h3 className="font-bold">Failure Modeling Error</h3>
              <p className="text-xs mt-1 text-red-300">{error}</p>
            </div>
          </div>
        )}

        {!results && !loading && !error && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center text-gray-500 flex flex-col items-center justify-center h-full min-h-[300px]">
            <ShieldAlert className="w-12 h-12 text-gray-700 mb-3" />
            <h3 className="text-lg font-bold text-gray-400">Risk Audit Engine Standby</h3>
            <p className="text-sm mt-1 max-w-sm">Setup commercial process parameters and click "Execute Risk Audit" to run 5 XGBoost models, evaluate SHAP explanations, and run Monte Carlo simulations.</p>
          </div>
        )}

        {loading && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center text-gray-400 flex flex-col items-center justify-center h-full min-h-[300px]">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-500 mb-3"></div>
            <p className="text-sm">Running 5 XGBoost risk classifiers and executing N=500 Monte Carlo perturbations...</p>
          </div>
        )}

        {results && (
          <div className="space-y-6 animate-fade-in">
            {/* Proceed Recommendation Banner */}
            <div className={`border p-4 rounded-xl flex items-center justify-between shadow-md ${getBannerStyle(results.proceed_recommendation)}`}>
              <div className="flex items-center gap-3">
                {results.proceed_recommendation === "PROCEED" ? (
                  <CheckCircle className="w-6 h-6 text-emerald-400" />
                ) : (
                  <ShieldAlert className="w-6 h-6 text-rose-500" />
                )}
                <div>
                  <h3 className="font-extrabold text-lg tracking-wide uppercase">Recommendation: {results.proceed_recommendation}</h3>
                  <p className="text-xs text-gray-300 mt-0.5">
                    {results.proceed_recommendation === "PROCEED" && "Formulation and scale-up recipe evaluated as low risk. Verified safe to export."}
                    {results.proceed_recommendation === "ADJUST_CPPS" && "Minor structural risks identified. Tweak CPP knobs in design space."}
                    {results.proceed_recommendation === "REFORMULATE" && "High risk of capping or recrystallisation detected. Reformulation advised."}
                  </p>
                </div>
              </div>
              
              <button
                onClick={exportJSON}
                className="py-2 px-3 bg-emerald-500 hover:bg-emerald-600 text-black font-bold text-xs rounded transition-colors flex items-center gap-1.5"
              >
                <Download className="w-4 h-4" />
                Export Card
              </button>
            </div>

            {/* Failure Risks and SHAP waterfall representations */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Risks & Traffic Lights */}
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
                <h3 className="text-base font-bold text-gray-100 border-b border-gray-800 pb-2 mb-4 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  XGBoost Failure Risk Classifier Scores
                </h3>

                <div className="space-y-4">
                  {Object.entries(results.failure_risks).map(([fm, value]) => {
                    const status = results.risk_levels[fm == "overdrying_risk" ? "overdrying" : fm == "crystallisation_risk" ? "crystallisation" : fm];
                    return (
                      <div key={fm} className="space-y-1">
                        <div className="flex justify-between items-center text-xs">
                          <span className="font-semibold text-gray-300 capitalize">{fm.replace("_", " ")}</span>
                          <span className={`px-1.5 py-0.5 text-[10px] font-extrabold rounded border ${getTrafficColor(status)}`}>
                            {(value * 100).toFixed(1)}% — {status}
                          </span>
                        </div>
                        <div className="w-full bg-gray-950 rounded-full h-2">
                          <div
                            style={{ width: `${value * 100}%` }}
                            className={`h-2 rounded-full ${
                              status === "GREEN" ? "bg-emerald-500" : status === "YELLOW" ? "bg-amber-500" : "bg-red-500"
                            }`}
                          ></div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Locked Design Space bounds (Monte Carlo output) */}
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
                <h3 className="text-base font-bold text-gray-100 border-b border-gray-800 pb-2 mb-4 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-emerald-400" />
                  Locked Operating Space (PAR — 95% Confidence)
                </h3>

                <div className="overflow-x-auto text-xs">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b border-gray-800 text-gray-400">
                        <th className="py-2">Critical Parameter (CPP)</th>
                        <th className="py-2 text-right">Lower Bound</th>
                        <th className="py-2 text-right">Nominal</th>
                        <th className="py-2 text-right">Upper Bound</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800">
                      {Object.entries(results.locked_design_space).map(([cpp, val]) => (
                        <tr key={cpp} className="hover:bg-gray-950 transition-colors">
                          <td className="py-2 font-medium capitalize text-gray-300">{cpp.replace("_", " ")}</td>
                          <td className="py-2 text-right text-gray-400">{val.lower}</td>
                          <td className="py-2 text-right font-bold text-emerald-400">{val.nominal}</td>
                          <td className="py-2 text-right text-gray-400">{val.upper}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Explanations SHAP Impact waterfall fallbacks */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 shadow-lg">
              <h3 className="text-base font-bold text-gray-100 border-b border-gray-800 pb-2 mb-4 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-emerald-400" />
                GMP Explainability Logs (Primary SHAP Risk Drivers)
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
                {Object.entries(results.shap_explanations).map(([fm, values]) => {
                  const sortedDrivers = Object.entries(values).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 3);
                  return (
                    <div key={fm} className="bg-gray-950 border border-gray-800 rounded p-3 text-xs space-y-2">
                      <h4 className="font-bold capitalize text-emerald-400 border-b border-gray-800 pb-1">{fm.replace("_", " ")}</h4>
                      <div className="space-y-1.5">
                        {sortedDrivers.map(([k, val]) => (
                          <div key={k} className="flex flex-col">
                            <span className="text-[10px] text-gray-500 capitalize">{k.replace("_", " ")}</span>
                            <span className={`font-semibold ${val >= 0 ? "text-rose-400" : "text-emerald-400"}`}>
                              {val >= 0 ? `+${val.toFixed(3)} (Promotes)` : `${val.toFixed(3)} (Inhibits)`}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
