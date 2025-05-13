import { Routes, Route, useNavigate } from 'react-router-dom'
import './index.css'
import { AuthProvider } from './lib/AuthContext'
import { AuthCallback } from './components/auth/AuthCallback'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { SyncBackend } from './components/auth/SyncBackend'
import { ResetPassword } from './components/auth/ResetPassword'
import Dashboard from './components/dashboard/dashboard'
import { NewAuthPage } from './components/auth/Page'
import { Toaster } from './components/ui/toaster'

function LandingPage() {
  const navigate = useNavigate()

  const handleGetStarted = () => {
    navigate('/auth')
  }

  return (
    <div className="min-h-screen bg-gradient-to-r from-[#ff5757] to-[#8c52ff] flex flex-col">
      {/* Navigation */}
      <nav className="container mx-auto px-6 py-4 flex justify-between items-center">
        <div className="flex items-center">
          <h1 className="text-4xl font-light text-black font-['Poppins']">Steadi.</h1>
        </div>
        <div>
          <button 
            onClick={handleGetStarted}
            className="bg-black text-white px-6 py-3 rounded-full font-['Poppins'] font-medium"
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex-grow flex flex-col justify-center">
        <div className="container mx-auto px-6 text-center">
          <h2 className="text-6xl md:text-7xl lg:text-8xl font-['Playfair_Display'] text-black mb-6">
            The <span className="font-['Quintessential'] italic">AI Agent</span> for<br />
            <span className="font-['Playfair_Display'] not-italic">Small Businesses</span>
          </h2>
          <p className="text-lg md:text-xl max-w-3xl mx-auto text-black mb-12 font-['Poppins']">
            Revolutionize your customer acquisition and optimize
            supply chain management with advanced AI technology
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button 
              onClick={handleGetStarted}
              className="bg-black text-white px-8 py-4 rounded-full font-['Poppins'] font-medium text-lg"
            >
              Get Started
            </button>
            <a href="#watch-demo" className="bg-white/30 backdrop-blur-sm text-black px-8 py-4 rounded-full font-['Poppins'] font-medium text-lg">Watch Demo</a>
          </div>
        </div>
      </main>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      {/* Synchronize Supabase auth with backend */}
      <SyncBackend />
      
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/auth" element={<NewAuthPage />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/auth/reset-password" element={<ResetPassword />} />
        
        {/* Protected routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
          {/* Add other protected routes here */}
        </Route>
      </Routes>

      {/* Toast notifications */}
      <Toaster />
    </AuthProvider>
  )
}

export default App
