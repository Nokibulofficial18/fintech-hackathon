import { useState, useEffect } from 'react'
import {
  AlertCircle,
  Clock,
  Sparkles,
} from 'lucide-react'
import {
  checkBackendHealth,
  fetchDemoScenario,
  resetDemoScenario,
  fetchFinanceOverview,
  fetchCashFlowForecast,
  fetchFundingGap,
  fetchRecommendations,
} from './services/api'
import type {
  HealthStatus,
  FullStudentScenario,
  FinanceOverviewResponse,
  CashFlowForecastResponse,
  FundingGapResponse,
  RecommendationsResponse,
} from './types/api'
import type { TabId } from './components/TabNav'
import { Sidebar } from './components/Sidebar'
import { TopBar } from './components/TopBar'
import { FinancialOverview } from './components/FinancialOverview'
import { TransferComparison } from './components/TransferComparison'
import { AICopilot } from './components/AICopilot'
import { ActionPlan } from './components/ActionPlan'
import { DataTransparencyModal } from './components/DataTransparencyModal'
import { useTranslation } from './i18n/useTranslation'

export default function App() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<TabId>('overview')
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false)

  // Global API states
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [latencyMs, setLatencyMs] = useState<number | null>(null)
  const [scenario, setScenario] = useState<FullStudentScenario | null>(null)
  const [overview, setOverview] = useState<FinanceOverviewResponse | null>(null)
  const [forecast, setForecast] = useState<CashFlowForecastResponse | null>(null)
  const [gap, setGap] = useState<FundingGapResponse | null>(null)
  const [recommendations, setRecommendations] = useState<RecommendationsResponse | null>(null)

  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [simulationNotification, setSimulationNotification] = useState<string | null>(null)
  const [copilotPrompt, setCopilotPrompt] = useState<string | null>(null)

  const loadAllData = async () => {
    setLoading(true)
    setError(null)
    try {
      try {
        const { data: healthData, latencyMs: lat } = await checkBackendHealth()
        setHealth(healthData)
        setLatencyMs(lat)
      } catch {
        setHealth(null)
      }

      const [scenData, overData, foreData, gapData, recsData] = await Promise.all([
        fetchDemoScenario(),
        fetchFinanceOverview(),
        fetchCashFlowForecast(90),
        fetchFundingGap(90),
        fetchRecommendations(),
      ])

      setScenario(scenData)
      setOverview(overData)
      setForecast(foreData)
      setGap(gapData)
      setRecommendations(recsData)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to connect to BorderWise AI backend'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let ignore = false
    const init = async () => {
      try {
        try {
          const { data: healthData, latencyMs: lat } = await checkBackendHealth()
          if (!ignore) {
            setHealth(healthData)
            setLatencyMs(lat)
          }
        } catch {
          if (!ignore) setHealth(null)
        }

        const [scenData, overData, foreData, gapData, recsData] = await Promise.all([
          fetchDemoScenario(),
          fetchFinanceOverview(),
          fetchCashFlowForecast(90),
          fetchFundingGap(90),
          fetchRecommendations(),
        ])

        if (!ignore) {
          setScenario(scenData)
          setOverview(overData)
          setForecast(foreData)
          setGap(gapData)
          setRecommendations(recsData)
        }
      } catch (err: unknown) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : 'Failed to connect to BorderWise AI backend')
        }
      } finally {
        if (!ignore) {
          setLoading(false)
        }
      }
    }

    init()
    return () => {
      ignore = true
    }
  }, [])

  const handleSimulateAction = (_actionId: string, actionTitle: string) => {
    setSimulationNotification(
      `Simulation active for "${actionTitle}". Decision-support modeled in planning state; zero real funds were transferred.`
    )
    setTimeout(() => {
      setSimulationNotification(null)
    }, 6000)
  }

  const handleResetDemo = async () => {
    setLoading(true)
    try {
      await resetDemoScenario('china')
      setSimulationNotification(
        'Demo state successfully reset to Signature China–Bangladesh Student baseline (Tanvir Hasan, Tsinghua University, CNY/BDT). All figures refreshed.'
      )
      await loadAllData()
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  const handleTabChange = (tab: TabId) => {
    setActiveTab(tab)
    setMobileMenuOpen(false)
  }

  const handleNavigateToCopilot = (initialPromptText?: string) => {
    if (initialPromptText) {
      setCopilotPrompt(initialPromptText)
    }
    setActiveTab('copilot')
    setMobileMenuOpen(false)
  }

  const actionCount = recommendations ? recommendations.critical_count + recommendations.high_count : 0

  return (
    <div className="app-shell">
      {/* Mobile Backdrop */}
      {mobileMenuOpen && (
        <div
          className="mobile-backdrop"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Desktop & Mobile Responsive Sidebar */}
      <div className={`sidebar-container ${mobileMenuOpen ? 'mobile-open' : ''}`}>
        <Sidebar
          activeTab={activeTab}
          onTabChange={handleTabChange}
          actionCount={actionCount}
          hasWarning={gap?.target_currency_has_shortfall}
          profile={scenario?.profile}
          healthLoading={loading}
          onResetDemo={handleResetDemo}
          onRefresh={loadAllData}
        />
      </div>

      {/* Main Command Center Layout Area */}
      <div className="app-main-area">
        {/* TopBar with page title, student context, demo indicator, and notifications */}
        <TopBar
          activeTab={activeTab}
          onTabChange={handleTabChange}
          profile={scenario?.profile}
          health={health}
          latencyMs={latencyMs}
          gap={gap}
          recommendations={recommendations}
          mobileMenuOpen={mobileMenuOpen}
          onToggleMobileMenu={() => setMobileMenuOpen((prev) => !prev)}
        />

        {/* Scrollable Content Container */}
        <div className="app-content-body">
          {/* Simulation Feedback Alert */}
          {simulationNotification && (
            <div className="alert-feedback-banner">
              <Sparkles size={18} color="#2dd4bf" />
              <span>{simulationNotification}</span>
            </div>
          )}

          {/* Global Error Banner */}
          {error && (
            <div className="alert-error-banner">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <AlertCircle size={20} color="#f43f5e" />
                <span>{error}. Please ensure the backend server is running on http://127.0.0.1:8000.</span>
              </div>
              <button
                onClick={loadAllData}
                className="btn btn-secondary"
                style={{ padding: '6px 14px', fontSize: '12px' }}
              >
                {t('common.retry')}
              </button>
            </div>
          )}

          {/* Main Tab Views */}
          <main>
            {loading && !overview ? (
              <div className="fintech-card loading-box">
                <Clock className="spin-icon" size={36} color="#14b8a6" />
                <h3 style={{ color: '#fff', fontSize: '16px' }}>{t('common.initializing')}</h3>
                <p style={{ fontSize: '13.5px', color: '#94a3b8' }}>
                  {t('overview.loadingSchedule')}
                </p>
              </div>
            ) : (
              <>
                {activeTab === 'overview' && (
                  <FinancialOverview
                    overview={overview}
                    forecast={forecast}
                    gap={gap}
                    scenario={scenario}
                    onNavigateToTransfers={() => setActiveTab('transfers')}
                    onNavigateToCopilot={handleNavigateToCopilot}
                    onNavigateToActions={() => setActiveTab('actions')}
                  />
                )}

                {activeTab === 'transfers' && (
                  <TransferComparison
                    initialSendAmount={1000}
                    initialSendCurrency={scenario?.profile?.study_currency ?? 'CNY'}
                    initialReceiveCurrency={scenario?.profile?.home_currency ?? 'BDT'}
                  />
                )}

                {activeTab === 'copilot' && (
                  <AICopilot
                    overview={overview}
                    gap={gap}
                    forecast={forecast}
                    recommendations={recommendations}
                    initialPrompt={copilotPrompt}
                    onNavigateToActionPlan={() => setActiveTab('actions')}
                  />
                )}

                {activeTab === 'actions' && (
                  <ActionPlan
                    recommendations={recommendations}
                    onSimulateAction={handleSimulateAction}
                  />
                )}

                {activeTab === 'transparency' && (
                  <DataTransparencyModal
                    scenario={scenario}
                    forecast={forecast}
                    gap={gap}
                  />
                )}
              </>
            )}
          </main>

          {/* Command Center Footer */}
          <footer className="app-footer">
            <div style={{ fontWeight: 600, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>{t('common.footerNotesTitle')}</span>
            </div>
            <div style={{ lineHeight: 1.6 }}>
              &bull; <strong>{t('common.pureArithmeticNote').split(':')[0]}:</strong>{t('common.pureArithmeticNote').split(':')[1]}<br />
              &bull; <strong>{t('common.isolationNote').split(':')[0]}:</strong>{t('common.isolationNote').split(':')[1]}<br />
              &bull; <strong>{t('common.transparencyNote').split(':')[0]}:</strong>{t('common.transparencyNote').split(':')[1]}<br />
              &bull; <strong>{t('common.zeroPaymentsNote').split(':')[0]}:</strong>{t('common.zeroPaymentsNote').split(':')[1]}
            </div>
          </footer>
        </div>
      </div>
    </div>
  )
}
