import { useState, useEffect, useRef } from 'react'
import {
  Bell,
  Menu,
  X,
  AlertTriangle,
  Building2,
  Calendar,
  CheckCircle2,
  Sparkles,
  ChevronRight,
} from 'lucide-react'
import type { TabId } from './TabNav'
import type { HealthStatus, StudentProfileData, FundingGapResponse, RecommendationsResponse } from '../types/api'
import { formatCurrency } from '../utils/formatters'
import { useTranslation } from '../i18n/useTranslation'
import { LanguageSelector } from './LanguageSelector'

interface TopBarProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  profile?: StudentProfileData | null
  health: HealthStatus | null
  latencyMs: number | null
  gap: FundingGapResponse | null
  recommendations: RecommendationsResponse | null
  mobileMenuOpen: boolean
  onToggleMobileMenu: () => void
}

export function TopBar({
  activeTab,
  onTabChange,
  profile,
  health,
  latencyMs,
  gap,
  recommendations,
  mobileMenuOpen,
  onToggleMobileMenu,
}: TopBarProps) {
  const { t, locale } = useTranslation()
  const [showNotifications, setShowNotifications] = useState(false)
  const notifRef = useRef<HTMLDivElement | null>(null)

  // Escape key and click-outside handling for accessible popover
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showNotifications) {
        setShowNotifications(false)
      }
    }

    const handleClickOutside = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setShowNotifications(false)
      }
    }

    if (showNotifications) {
      document.addEventListener('keydown', handleKeyDown)
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showNotifications])

  const getPageTitle = (tab: TabId) => {
    switch (tab) {
      case 'overview':
        return t('topbar.overviewTitle')
      case 'transfers':
        return t('topbar.transfersTitle')
      case 'copilot':
        return t('topbar.copilotTitle')
      case 'actions':
        return t('topbar.actionsTitle')
      case 'transparency':
        return t('topbar.transparencyTitle')
      default:
        return 'BorderWise AI'
    }
  }

  const getPageSubtitle = (tab: TabId) => {
    switch (tab) {
      case 'overview':
        return t('topbar.overviewSubtitle')
      case 'transfers':
        return t('topbar.transfersSubtitle')
      case 'copilot':
        return t('topbar.copilotSubtitle')
      case 'actions':
        return t('topbar.actionsSubtitle')
      case 'transparency':
        return t('topbar.transparencySubtitle')
      default:
        return ''
    }
  }

  const notificationCount =
    (gap?.target_currency_has_shortfall ? 1 : 0) +
    (recommendations?.critical_count || 0)

  return (
    <header className="app-topbar">
      <div className="topbar-left">
        <button
          type="button"
          onClick={onToggleMobileMenu}
          className="mobile-menu-toggle"
          aria-label={mobileMenuOpen ? 'Close Navigation Menu' : 'Open Navigation Menu'}
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        <div className="topbar-title-block">
          {/* Accessible Breadcrumbs */}
          <nav aria-label="Breadcrumb" className="topbar-breadcrumb">
            <span className="breadcrumb-root">{t('topbar.breadcrumbRoot')}</span>
            <ChevronRight size={12} className="breadcrumb-sep" aria-hidden="true" />
            <span className="breadcrumb-current" aria-current="page">
              {getPageTitle(activeTab)}
            </span>
          </nav>
          <h1 className="topbar-title">{getPageTitle(activeTab)}</h1>
          <p className="topbar-subtitle">{getPageSubtitle(activeTab)}</p>
        </div>
      </div>

      <div className="topbar-right">
        {/* Language Selector Dropdown */}
        <LanguageSelector />

        {/* Student Context Badge */}
        {profile && (
          <div className="topbar-student-pill" title={`${profile.full_name} • ${profile.program_name}`}>
            <Building2 size={13} color="#94a3b8" />
            <span className="student-pill-univ">{profile.university_name}</span>
            <span className="student-pill-sep">&bull;</span>
            <span className="student-pill-term">{profile.intake_term}</span>
          </div>
        )}

        {/* Backend Status */}
        {health ? (
          <div className="status-pill topbar-status" title="FastAPI Financial Engine Online">
            <span className="status-dot"></span>
            <span>{t('topbar.backendOnline')} {latencyMs !== null ? `${latencyMs}ms` : 'ok'}</span>
          </div>
        ) : (
          <div className="status-pill error topbar-status" title="Backend Server Disconnected">
            <span className="status-dot"></span>
            <span>{t('topbar.backendOffline')}</span>
          </div>
        )}

        {/* Demo Indicator */}
        <div className="topbar-demo-pill" title="Synthetic Dataset: 2026-10-15 Baseline">
          <Calendar size={12} color="#fbbf24" />
          <span>{t('common.demoTag')} &bull; Oct 15</span>
        </div>

        {/* Notification Bell */}
        <div style={{ position: 'relative' }} ref={notifRef}>
          <button
            type="button"
            onClick={() => setShowNotifications((prev) => !prev)}
            className={`topbar-icon-btn ${notificationCount > 0 ? 'has-badge' : ''}`}
            title="View financial alerts and notifications"
            aria-label={`Notifications, ${notificationCount} unread alerts`}
            aria-haspopup="dialog"
            aria-expanded={showNotifications}
          >
            <Bell size={18} />
            {notificationCount > 0 && (
              <span className="notification-counter" aria-hidden="true">
                {notificationCount}
              </span>
            )}
          </button>

          {/* Notifications Dropdown Panel */}
          {showNotifications && (
            <div
              className="notifications-popover"
              role="dialog"
              aria-label="Financial Alerts"
            >
              <div className="notifications-header">
                <span style={{ fontWeight: 700, fontSize: '13px', color: '#fff' }}>
                  {t('topbar.notifications')} ({notificationCount})
                </span>
                <button
                  type="button"
                  onClick={() => setShowNotifications(false)}
                  style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
                  aria-label={t('topbar.closePopover')}
                >
                  <X size={14} />
                </button>
              </div>

              <div className="notifications-list">
                {gap?.target_currency_has_shortfall && (
                  <div
                    className="notification-item alert"
                    tabIndex={0}
                    role="button"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        onTabChange('overview')
                        setShowNotifications(false)
                      }
                    }}
                    onClick={() => {
                      onTabChange('overview')
                      setShowNotifications(false)
                    }}
                  >
                    <AlertTriangle size={16} color="#fb7185" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div>
                      <div className="notif-title">{t('topbar.urgentFundingAlert')}</div>
                      <div className="notif-desc">
                        Local shortfall of{' '}
                        <strong>
                          {formatCurrency(gap.target_currency_shortfall_amount, 'CNY', { locale })}
                        </strong>{' '}
                        for upcoming university tuition.
                      </div>
                      <span className="notif-action">{t('topbar.viewActions')}</span>
                    </div>
                  </div>
                )}

                {recommendations && recommendations.critical_count > 0 && (
                  <div
                    className="notification-item warning"
                    tabIndex={0}
                    role="button"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        onTabChange('actions')
                        setShowNotifications(false)
                      }
                    }}
                    onClick={() => {
                      onTabChange('actions')
                      setShowNotifications(false)
                    }}
                  >
                    <Sparkles size={16} color="#fbbf24" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div>
                      <div className="notif-title">{t('topbar.criticalActionsPending')} ({recommendations.critical_count})</div>
                      <div className="notif-desc">
                        {recommendations.recommendations[0]?.title || 'Prioritized step required'}
                      </div>
                      <span className="notif-action">{t('topbar.viewActions')}</span>
                    </div>
                  </div>
                )}

                {notificationCount === 0 && (
                  <div className="notification-empty">
                    <CheckCircle2 size={20} color="#10b981" />
                    <span>{t('topbar.systemStatusNormal')}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
