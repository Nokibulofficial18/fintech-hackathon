import { ShieldCheck, RefreshCw, GraduationCap, Building2, RotateCcw, ArrowRightLeft } from 'lucide-react'
import type { HealthStatus, StudentProfileData } from '../types/api'

interface NavbarProps {
  health: HealthStatus | null
  healthLoading: boolean
  latencyMs: number | null
  profile?: StudentProfileData | null
  onRefresh: () => void
  onResetDemo: () => void
}

export function Navbar({ health, healthLoading, latencyMs, profile, onRefresh, onResetDemo }: NavbarProps) {
  return (
    <header className="app-header">
      <div className="brand-section">
        <div className="brand-icon-box" title="BorderWise AI - Cross-Border Student Financial Copilot">
          <ShieldCheck size={26} color="#ffffff" />
        </div>
        <div>
          <div className="brand-name">
            <span>BorderWise AI</span>
            <span className="brand-badge">
              FINTECH COPILOT
            </span>
          </div>
          <div className="student-tag">
            {profile ? (
              <>
                <GraduationCap size={14} color="#94a3b8" />
                <span style={{ fontWeight: 600, color: '#f8fafc' }}>{profile.full_name}</span>
                <span className="bullet-sep">•</span>
                <Building2 size={13} color="#94a3b8" />
                <span>{profile.university_name}</span>
                <span className="bullet-sep">•</span>
                <span className="corridor-pill">
                  <span>Dhaka</span>
                  <ArrowRightLeft size={10} color="#14b8a6" />
                  <span>Beijing</span>
                </span>
              </>
            ) : (
              <span>Cross-Border Financial Copilot for International Students</span>
            )}
          </div>
        </div>
      </div>

      <div className="header-actions">
        {health ? (
          <div className="status-pill" title="FastAPI Financial Engine Online">
            <span className="status-dot"></span>
            <span>FastAPI Backend ({latencyMs !== null ? `${latencyMs}ms` : 'ok'})</span>
          </div>
        ) : (
          <div className="status-pill error" title="Cannot connect to backend">
            <span className="status-dot"></span>
            <span>Backend Disconnected</span>
          </div>
        )}

        <button
          onClick={onResetDemo}
          disabled={healthLoading}
          className="btn btn-outline-emerald"
          title="Reset to Signature China–Bangladesh Student Baseline (Tanvir Hasan, CNY/BDT)"
          aria-label="Reset Demo State"
        >
          <RotateCcw size={14} />
          <span>Reset Demo</span>
        </button>

        <button
          onClick={onRefresh}
          disabled={healthLoading}
          className="btn btn-secondary"
          title="Refresh All Financial Models & Account Balances"
          aria-label="Sync Financial Data"
        >
          <RefreshCw size={14} className={healthLoading ? 'spin-icon' : ''} />
          <span>Sync Data</span>
        </button>
      </div>
    </header>
  )
}
