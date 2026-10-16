import {
  ShieldAlert,
  Database,
  Calendar,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react'
import type {
  CashFlowForecastResponse,
  FundingGapResponse,
  FullStudentScenario,
} from '../types/api'
import { useTranslation } from '../i18n/useTranslation'

interface DataTransparencyModalProps {
  scenario: FullStudentScenario | null
  forecast: CashFlowForecastResponse | null
  gap: FundingGapResponse | null
}

export function DataTransparencyModal({ scenario, forecast, gap }: DataTransparencyModalProps) {
  const { t } = useTranslation()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div className="fintech-card">
        <div className="card-title-row">
          <div className="card-heading">
            <ShieldAlert size={20} color="#f59e0b" />
            <span>{t('transparency.title')}</span>
          </div>
          <span style={{ fontSize: '12px', color: '#38bdf8' }}>{t('transparency.badge')}</span>
        </div>

        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          {t('transparency.subtitle')}
        </p>

        {/* Provenance Matrix */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          {/* Card 1: Student Profile & Balances */}
          <div style={{ background: 'var(--bg-card-alt)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fff', fontWeight: 600, marginBottom: '8px' }}>
              <Database size={16} color="#38bdf8" />
              <span>{t('transparency.cardStudentTitle')}</span>
            </div>
            <div style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.5 }}>
              Status: <strong style={{ color: '#38bdf8' }}>Synthetic Demo Dataset</strong><br />
              Student: {scenario?.profile.full_name || 'Tanvir Hasan'}<br />
              As-Of Date: <strong>2026-10-15</strong><br />
              Liquid Accounts: 2 Verified Accounts (CNY ICBC Beijing, BDT DBBL Dhaka)<br />
              Real Bank Access: <strong>None (Strict Sandbox)</strong>
            </div>
          </div>

          {/* Card 2: Foreign Exchange Rates */}
          <div style={{ background: 'var(--bg-card-alt)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fff', fontWeight: 600, marginBottom: '8px' }}>
              <Calendar size={16} color="#10b981" />
              <span>{t('transparency.cardFxTitle')}</span>
            </div>
            <div style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.5 }}>
              Quote Feed: <strong>Simulated Central Benchmark (DEMO DATA)</strong><br />
              Rate Applied: <strong>1 CNY = 16.8500 BDT (1 BDT = 0.0593 CNY)</strong><br />
              Timestamp: <strong>2026-10-15 00:00 UTC</strong><br />
              Staleness Flag: {gap?.has_stale_rate_warning ? (
                <span style={{ color: '#fb7185', fontWeight: 700 }}>STALE (&gt;24h)</span>
              ) : (
                <span style={{ color: '#34d399', fontWeight: 700 }}>VERIFIED FRESH</span>
              )}
            </div>
          </div>

          {/* Card 3: Provider Benchmark Schedules */}
          <div style={{ background: 'var(--bg-card-alt)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fff', fontWeight: 600, marginBottom: '8px' }}>
              <CheckCircle2 size={16} color="#14b8a6" />
              <span>{t('transparency.cardTransferTitle')}</span>
            </div>
            <div style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.5 }}>
              Alipay / WeChat / Specialists: <strong>Digital Schedule (Simulated Benchmark)</strong><br />
              Global Wire Banks: <strong>Bank of China Retail Schedule</strong><br />
              Campus Desk: <strong>Simulated University Partner Agreement</strong><br />
              Execution: <strong>Informational Benchmark Only</strong>
            </div>
          </div>
        </div>

        {/* Data Completeness Breakdown */}
        {forecast && (
          <div style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '18px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ fontWeight: 600, color: '#fff', fontSize: '14px' }}>
                {t('transparency.forecastCompletenessAudit')}
              </span>
              <span style={{ fontSize: '13px', fontWeight: 700, color: '#10b981' }}>
                {(forecast.data_completeness.completeness_score * 100).toFixed(0)}% {t('transparency.score')}
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px', fontSize: '12.5px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={14} color="#34d399" />
                <span>{t('transparency.liquidBalances')}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={14} color="#34d399" />
                <span>{t('transparency.incomeStreams')}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={14} color="#34d399" />
                <span>{t('transparency.livingExpenses')}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={14} color="#34d399" />
                <span>{t('transparency.tuitionSchedule')}</span>
              </div>
            </div>

            <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '10px' }}>
              <em>Audit Notes:</em> {forecast.data_completeness.notes}
            </div>
          </div>
        )}

        {/* Warnings or Staleness Notes */}
        {gap && gap.rate_warnings.length > 0 && (
          <div style={{ padding: '14px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', color: '#fbbf24', fontSize: '13px', display: 'flex', gap: '8px' }}>
            <AlertTriangle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              {gap.rate_warnings.map((w, idx) => (
                <div key={idx}>{w}</div>
              ))}
            </div>
          </div>
        )}

        {/* Assumptions */}
        {forecast && (
          <div style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontWeight: 600, color: '#e2e8f0' }}>{t('transparency.modelingAssumptions')}</span>
            {forecast.assumptions.map((asm, idx) => (
              <div key={idx}>• {asm}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
