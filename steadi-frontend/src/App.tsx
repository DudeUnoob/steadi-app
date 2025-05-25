import { Routes, Route } from 'react-router-dom'
import './index.css'
import { AuthProvider } from './lib/AuthContext'
import { AuthCallback } from './components/auth/AuthCallback'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { SyncBackend } from './components/auth/SyncBackend'
import { ResetPassword } from './components/auth/ResetPassword'
import { VerifyEmail } from './components/auth/VerifyEmail'
import Dashboard from './components/dashboard/dashboard'
import { ConnectorsDashboard } from './components/connectors/connectors-dashboard'
import { OAuthCallback } from './components/connectors/oauth-callback'
import { NewAuthPage } from './components/auth/Page'
import RulesPage from './components/auth/Rules'
import OrganizationPage from './components/auth/Organization'
import RoleSelectionPage from './components/auth/RoleSelection'
import { Toaster } from './components/ui/toaster'
// Import landing page components
import { LandingCta } from './components/landing/landing-cta'
import { LandingFeatures } from './components/landing/landing-features'
import { LandingFooter } from './components/landing/landing-footer'
import { LandingHero } from './components/landing/landing-hero'
import { LandingNavbar } from './components/landing/landing-navbar'
import { LandingTestimonials } from './components/landing/landing-testimonials'

// Combined landing page component
function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <LandingNavbar />
      <LandingHero />
      <LandingFeatures />
      <LandingTestimonials />
      <LandingCta />
      <LandingFooter />
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
        <Route path="/auth/verify-email" element={<VerifyEmail />} />
        <Route path="/auth/role-selection" element={<RoleSelectionPage />} />
        <Route path="/auth/rules" element={
          <ProtectedRoute requireRulesCompleted={false}>
            <RulesPage />
          </ProtectedRoute>
        } />
        <Route path="/auth/organization" element={
          <ProtectedRoute requireOrgCode={true}>
            <OrganizationPage />
          </ProtectedRoute>
        } />
        
        {/* POS Connector OAuth callback */}
        <Route path="/connectors/oauth/callback" element={
          <ProtectedRoute>
            <OAuthCallback />
          </ProtectedRoute>
        } />
        
        {/* Protected routes */}
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/connectors" element={
          <ProtectedRoute>
            <ConnectorsDashboard />
          </ProtectedRoute>
        } />
        {/* Add other protected routes here */}
      </Routes>

      {/* Toast notifications */}
      <Toaster />
    </AuthProvider>
  )
}

export default App
