import ActiveLearningDashboard from './components/Vector1/ActiveLearningDashboard'

function App() {
  return (
    <div className="container mx-auto p-4 md:p-8">
      <header className="mb-8 text-center md:text-left">
        <h1 className="text-3xl font-extrabold text-blue-400">EnFormis Manufacturing Intelligence Core</h1>
        <p className="text-gray-400 mt-1">Vector 1 — Multi-Objective Active Bayesian Formulation Optimizer</p>
      </header>
      <main>
        <ActiveLearningDashboard />
      </main>
    </div>
  )
}

export default App
