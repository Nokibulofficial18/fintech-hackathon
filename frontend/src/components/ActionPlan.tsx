import { useState } from 'react'
import {
  ListTodo,
  AlertOctagon,
  Clock,
  CheckCircle2,
  XCircle,
  PlayCircle,
  Info,
  RotateCcw,
} from 'lucide-react'
import type { RecommendationsResponse, ActionableRecommendation } from '../types/api'
import { formatCurrency, formatAmount } from '../utils/formatters'
import { useTranslation } from '../i18n/useTranslation'

interface ActionPlanProps {
  recommendations: RecommendationsResponse | null
  onSimulateAction: (actionId: string, actionTitle: string) => void
}

export function ActionPlan({ recommendations, onSimulateAction }: ActionPlanProps) {
  const { t, locale } = useTranslation()
  // Local state for tracking acknowledged or dismissed items during the session
  const [acknowledgedIds, setAcknowledgedIds] = useState<Record<string, string>>({})
  const [dismissedIds, setDismissedIds] = useState<Record<string, boolean>>({})

  if (!recommendations) {
    return (
      <div className="fintech-card loading-box">
        <Clock className="spin-icon" size={32} color="#14b8a6" />
        <p>{t('common.loading')}</p>
      </div>
    )
  }

  const handleAcknowledge = (id: string) => {
    setAcknowledgedIds((prev) => ({
      ...prev,
      [id]: t('actions.acknowledgedSuccess'),
    }))
  }

  const handleDismiss = (id: string) => {
    setDismissedIds((prev) => ({
      ...prev,
      [id]: true,
    }))
  }

  const handleSimulate = (id: string, title: string) => {
    setAcknowledgedIds((prev) => ({
      ...prev,
      [id]: t('actions.simulatedSuccess'),
    }))
    onSimulateAction(id, title)
  }

  const activeRecs = recommendations.recommendations.filter((r) => !dismissedIds[r.id])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="fintech-card">
        <div className="card-title-row">
          <div className="card-heading">
            <ListTodo size={20} color="#14b8a6" />
            <span>{t('actions.title')}</span>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <span className="badge-critical">
              {recommendations.critical_count} {t('actions.criticalPriority')}
            </span>
            <span className="badge-high">
              {recommendations.high_count} {t('actions.highPriority')}
            </span>
          </div>
        </div>

        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Prioritized checklist derived strictly from tuition deadlines, funding gap analysis, and currency burn modeling.
          Simulate workflows or acknowledge planning steps without triggering live financial payments.
        </p>

        {activeRecs.length === 0 ? (
          <div className="empty-state-card" style={{ padding: '36px 20px', textAlign: 'center' }}>
            <CheckCircle2 size={32} color="#10b981" style={{ margin: '0 auto 12px' }} />
            <h4 style={{ color: '#fff', fontSize: '15px', marginBottom: '6px' }}>{t('actions.allCleared')}</h4>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', maxWidth: '420px', margin: '0 auto 16px' }}>
              {t('actions.allClearedSub')}
            </p>
            <button
              type="button"
              onClick={() => {
                setDismissedIds({})
                setAcknowledgedIds({})
              }}
              className="btn btn-secondary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            >
              <RotateCcw size={14} />
              <span>{t('actions.resetRecommendations')}</span>
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {activeRecs.map((rec: ActionableRecommendation) => {
              const statusText = acknowledgedIds[rec.id]
              return (
                <div
                  key={rec.id}
                  style={{
                    background: 'var(--bg-card-alt)',
                    border: `1px solid ${
                      rec.priority === 'CRITICAL'
                        ? 'rgba(244, 63, 94, 0.4)'
                        : rec.priority === 'HIGH'
                        ? 'rgba(245, 158, 11, 0.4)'
                        : 'var(--border-card)'
                    }`,
                    borderRadius: '12px',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '14px',
                  }}
                >
                  {/* Header Row */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <AlertOctagon
                        size={20}
                        color={rec.priority === 'CRITICAL' ? '#f43f5e' : rec.priority === 'HIGH' ? '#f59e0b' : '#38bdf8'}
                      />
                      <span style={{ fontWeight: 700, fontSize: '16px', color: '#fff' }}>
                        {rec.title}
                      </span>
                    </div>

                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span className={`badge-${rec.priority.toLowerCase()}`}>
                        {rec.priority} PRIORITY
                      </span>
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 600,
                          padding: '3px 8px',
                          borderRadius: '4px',
                          background: 'rgba(255, 255, 255, 0.05)',
                          color: '#94a3b8',
                          border: '1px solid var(--border-subtle)',
                        }}
                      >
                        {rec.urgency}
                      </span>
                    </div>
                  </div>

                  {/* Reason & Analytical Justification */}
                  <div style={{ fontSize: '13.5px', color: '#e2e8f0', lineHeight: 1.5 }}>
                    {rec.reason}
                  </div>

                  {/* Supporting Numbers Grid */}
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                      gap: '8px',
                      background: 'rgba(0, 0, 0, 0.25)',
                      padding: '10px 14px',
                      borderRadius: '8px',
                    }}
                  >
                    {Object.entries(rec.supporting_numbers).map(([key, val]) => (
                      <div key={key}>
                        <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'capitalize' }}>
                          {key.replace(/_/g, ' ')}
                        </div>
                        <div style={{ fontSize: '14px', fontWeight: 600, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>
                          {typeof val === 'number'
                            ? key.toLowerCase().includes('bdt')
                              ? formatCurrency(val, 'BDT', { locale })
                              : key.toLowerCase().includes('cny') ||
                                key.toLowerCase().includes('cost') ||
                                key.toLowerCase().includes('tuition') ||
                                key.toLowerCase().includes('shortfall') ||
                                key.toLowerCase().includes('amount') ||
                                key.toLowerCase().includes('gap')
                              ? formatCurrency(val, 'CNY', { locale })
                              : formatAmount(val, 2, locale)
                            : String(val)}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Suggested Action */}
                  <div style={{ fontSize: '13px', color: '#34d399', fontWeight: 500 }}>
                    <strong>Action:</strong> {rec.suggested_action}
                  </div>

                  {/* Assumptions & Uncertainty */}
                  <div style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div>
                      <em>Assumptions:</em> {rec.assumptions.join(' ')}
                    </div>
                    <div>
                      <em>Uncertainty:</em> {rec.uncertainty}
                    </div>
                  </div>

                  {/* Simulation Status Badge if simulated */}
                  {statusText && (
                    <div
                      style={{
                        padding: '8px 12px',
                        background: 'rgba(16, 185, 129, 0.1)',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                        borderRadius: '6px',
                        fontSize: '12.5px',
                        color: '#34d399',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      <CheckCircle2 size={14} />
                      <span>{statusText}</span>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div style={{ display: 'flex', gap: '10px', paddingTop: '6px', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      onClick={() => handleSimulate(rec.id, rec.title)}
                      className="btn btn-outline-emerald"
                      style={{ padding: '8px 14px', fontSize: '12.5px' }}
                    >
                      <PlayCircle size={14} />
                      <span>{t('actions.simulateWorkflow')}</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleAcknowledge(rec.id)}
                      className="btn btn-secondary"
                      style={{ padding: '8px 14px', fontSize: '12.5px' }}
                    >
                      <CheckCircle2 size={14} />
                      <span>{t('actions.acknowledgeStep')}</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDismiss(rec.id)}
                      className="btn btn-secondary"
                      style={{ padding: '8px 14px', fontSize: '12.5px' }}
                    >
                      <XCircle size={14} />
                      <span>{t('actions.dismiss')}</span>
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        <div style={{ padding: '14px', background: 'rgba(0,0,0,0.25)', borderRadius: '8px', fontSize: '12px', color: '#94a3b8', display: 'flex', gap: '8px' }}>
          <Info size={16} color="#6366f1" style={{ flexShrink: 0, marginTop: '2px' }} />
          <span>{recommendations.compliance_disclaimer}</span>
        </div>
      </div>
    </div>
  )
}
