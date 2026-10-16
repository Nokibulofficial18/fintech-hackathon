import {
  LayoutDashboard,
  ArrowRightLeft,
  BotMessageSquare,
  ListTodo,
  ShieldAlert,
} from 'lucide-react'

import { useTranslation } from '../i18n/useTranslation'

export type TabId = 'overview' | 'transfers' | 'copilot' | 'actions' | 'transparency'

interface TabNavProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
  actionCount?: number
  hasWarning?: boolean
}

export function TabNav({ activeTab, onTabChange, actionCount = 0, hasWarning = false }: TabNavProps) {
  const { t } = useTranslation()

  return (
    <nav className="nav-tabs" aria-label="Dashboard Navigation" role="tablist">
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === 'overview'}
        className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
        onClick={() => onTabChange('overview')}
      >
        <LayoutDashboard size={16} />
        <span>{t('nav.commandCenter')}</span>
      </button>

      <button
        type="button"
        role="tab"
        aria-selected={activeTab === 'transfers'}
        className={`tab-btn ${activeTab === 'transfers' ? 'active' : ''}`}
        onClick={() => onTabChange('transfers')}
      >
        <ArrowRightLeft size={16} />
        <span>{t('nav.transfers')}</span>
      </button>

      <button
        type="button"
        role="tab"
        aria-selected={activeTab === 'copilot'}
        className={`tab-btn ${activeTab === 'copilot' ? 'active' : ''}`}
        onClick={() => onTabChange('copilot')}
      >
        <BotMessageSquare size={16} />
        <span>{t('nav.copilot')}</span>
      </button>

      <button
        type="button"
        role="tab"
        aria-selected={activeTab === 'actions'}
        className={`tab-btn ${activeTab === 'actions' ? 'active' : ''}`}
        onClick={() => onTabChange('actions')}
      >
        <ListTodo size={16} />
        <span>{t('nav.actionPlan')}</span>
        {actionCount > 0 && <span className="tab-badge">{actionCount}</span>}
      </button>

      <button
        type="button"
        role="tab"
        aria-selected={activeTab === 'transparency'}
        className={`tab-btn ${activeTab === 'transparency' ? 'active' : ''}`}
        onClick={() => onTabChange('transparency')}
      >
        <ShieldAlert size={16} color={hasWarning ? '#fbbf24' : undefined} />
        <span>{t('nav.transparency')}</span>
      </button>
    </nav>
  )
}
