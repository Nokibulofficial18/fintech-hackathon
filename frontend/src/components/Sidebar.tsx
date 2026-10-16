import {
  ShieldCheck,
  LayoutDashboard,
  ArrowRightLeft,
  BotMessageSquare,
  ListTodo,
  ShieldAlert,
  RotateCcw,
  RefreshCw,
  GraduationCap,
  Sparkles,
} from 'lucide-react'
import type { TabId } from './TabNav'
import type { StudentProfileData } from '../types/api'
import { useTranslation } from '../i18n/useTranslation'

interface SidebarProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  actionCount: number
  hasWarning?: boolean
  profile?: StudentProfileData | null
  healthLoading: boolean
  onResetDemo: () => void
  onRefresh: () => void
}

export function Sidebar({
  activeTab,
  onTabChange,
  actionCount,
  hasWarning,
  profile,
  healthLoading,
  onResetDemo,
  onRefresh,
}: SidebarProps) {
  const { t } = useTranslation()

  const navItems = [
    {
      id: 'overview' as TabId,
      label: t('nav.commandCenter'),
      icon: LayoutDashboard,
      badge: null,
    },
    {
      id: 'transfers' as TabId,
      label: t('nav.transfers'),
      icon: ArrowRightLeft,
      badge: 'CNY ⇄ BDT',
    },
    {
      id: 'copilot' as TabId,
      label: t('nav.copilot'),
      icon: BotMessageSquare,
      badge: 'AI',
    },
    {
      id: 'actions' as TabId,
      label: t('nav.actionPlan'),
      icon: ListTodo,
      badge: actionCount > 0 ? String(actionCount) : null,
      badgeType: 'warning',
    },
    {
      id: 'transparency' as TabId,
      label: t('nav.transparency'),
      icon: ShieldAlert,
      badge: hasWarning ? 'Audit' : null,
      badgeType: hasWarning ? 'alert' : 'default',
    },
  ]

  return (
    <aside className="app-sidebar" aria-label="Main Navigation">
      {/* Brand Header */}
      <div className="sidebar-brand-box">
        <div className="brand-icon-box">
          <ShieldCheck size={24} color="#ffffff" />
        </div>
        <div>
          <div className="brand-name">
            <span>BorderWise</span>
            <span className="brand-ai-suffix">AI</span>
          </div>
          <div className="brand-tagline">{t('common.copilotTag')}</div>
        </div>
      </div>

      {/* Corridor Badge */}
      <div className="sidebar-corridor-box">
        <div className="sidebar-corridor-header">
          <span className="sidebar-corridor-label">{t('nav.activeCorridor')}</span>
          <span className="demo-badge-mini">{t('common.demoTag')}</span>
        </div>
        <div className="sidebar-corridor-route">
          <span className="corridor-flag">🇧🇩</span>
          <span>{t('nav.corridorDhaka')}</span>
          <span className="corridor-arrow">⇄</span>
          <span className="corridor-flag">🇨🇳</span>
          <span>{t('nav.corridorBeijing')}</span>
        </div>
      </div>

      {/* Nav Menu */}
      <nav className="sidebar-nav">
        <div className="sidebar-nav-label">{t('nav.navigationHeader')}</div>
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = activeTab === item.id
          return (
            <button
              key={item.id}
              type="button"
              className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
              onClick={() => onTabChange(item.id)}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon size={18} className="sidebar-nav-icon" />
              <span className="sidebar-nav-text">{item.label}</span>
              {item.badge && (
                <span
                  className={`sidebar-badge ${
                    item.badgeType === 'warning'
                      ? 'warning'
                      : item.badgeType === 'alert'
                      ? 'alert'
                      : ''
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Student Profile & Demo Actions */}
      <div className="sidebar-footer">
        {profile && (
          <div className="sidebar-student-card">
            <div className="student-avatar-box">
              <GraduationCap size={18} color="#2dd4bf" />
            </div>
            <div className="student-info-text">
              <div className="student-name-text">{profile.full_name}</div>
              <div className="student-sub-text">{profile.university_name}</div>
              <div className="student-term-text">{profile.intake_term} &bull; {t('topbar.masterDegree')}</div>
            </div>
          </div>
        )}

        {/* Demo Controls */}
        <div className="sidebar-actions-row">
          <button
            type="button"
            onClick={onResetDemo}
            disabled={healthLoading}
            className="sidebar-action-btn"
            title="Reset to pristine China-BD baseline demo state"
          >
            <RotateCcw size={13} />
            <span>{t('nav.resetDemo')}</span>
          </button>

          <button
            type="button"
            onClick={onRefresh}
            disabled={healthLoading}
            className="sidebar-action-btn"
            title="Sync all account balances and cash-flow forecast"
          >
            <RefreshCw size={13} className={healthLoading ? 'spin-icon' : ''} />
            <span>{t('nav.syncData')}</span>
          </button>
        </div>

        <div className="sidebar-guarantee-note">
          <Sparkles size={11} color="#14b8a6" />
          <span>{t('nav.arithmeticGuarantee')}</span>
        </div>
      </div>
    </aside>
  )
}
