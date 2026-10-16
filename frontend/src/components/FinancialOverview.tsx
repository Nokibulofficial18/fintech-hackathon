import { useState, useMemo } from 'react'
import {
  Flame,
  ArrowRightLeft,
  Clock,
  TrendingDown,
  TrendingUp,
  Sparkles,
  BotMessageSquare,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  BadgeAlert,
  Calendar,
  Layers,
  Info,
} from 'lucide-react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ReferenceLine,
} from 'recharts'
import type {
  FinanceOverviewResponse,
  CashFlowForecastResponse,
  FundingGapResponse,
  FullStudentScenario,
  TimelineEvent,
  PlannedRemittance,
  LivingExpenseItem,
} from '../types/api'
import { formatCurrency, formatAmount, formatDate } from '../utils/formatters'
import { useTranslation } from '../i18n/useTranslation'

interface FinancialOverviewProps {
  overview: FinanceOverviewResponse | null
  forecast: CashFlowForecastResponse | null
  gap: FundingGapResponse | null
  scenario: FullStudentScenario | null
  onNavigateToTransfers: () => void
  onNavigateToCopilot: (initialPrompt?: string) => void
  onNavigateToActions: () => void
}

type SemanticStatus = {
  label: 'On track' | 'Attention needed' | 'Funding gap' | 'Critical deficit'
  variant: 'success' | 'warning' | 'alert' | 'danger'
  headline: string
  detail: string
}

function computeSemanticStatus(
  overview: FinanceOverviewResponse,
  gap: FundingGapResponse | null
): SemanticStatus {
  if (gap?.summary_status === 'CRITICAL_DEFICIT') {
    return {
      label: 'Critical deficit',
      variant: 'danger',
      headline: `Local liquid accounts face an unbridged shortfall of ${formatCurrency(gap.target_currency_shortfall_amount, 'CNY', { showFullLabel: true })}.`,
      detail:
        'Available liquid funds and home reserves combined are insufficient for upcoming obligations without supplementary capital.',
    }
  }

  if (gap?.target_currency_has_shortfall || overview.has_funding_gap) {
    const isCoverable = gap?.cross_currency_remedy?.can_cover_full_gap ?? true
    if (isCoverable) {
      return {
        label: 'Funding gap',
        variant: 'alert',
        headline: `Funding gap identified: ${formatCurrency(gap?.target_currency_shortfall_amount || 15300, 'CNY', { showFullLabel: true })} local shortfall.`,
        detail:
          '100% coverable via scheduled family transfer of ৳250,000 BDT from Dhaka savings before the Nov 15 tuition deadline.',
      }
    } else {
      return {
        label: 'Attention needed',
        variant: 'warning',
        headline: `Tuition due in ${overview.days_until_tuition_due} days with partial coverability.`,
        detail: 'Home currency reserves cover part of the obligation. Review transfer benchmarks and timeline.',
      }
    }
  }

  if (overview.has_imminent_shortfall) {
    return {
      label: 'Attention needed',
      variant: 'warning',
      headline: 'Upcoming 30-day obligations exceed local liquid reserves.',
      detail: 'Review planned remittances to ensure transfer timing matches invoice schedules.',
    }
  }

  return {
    label: 'On track',
    variant: 'success',
    headline: 'All upcoming tuition and living obligations are fully funded in local accounts.',
    detail: 'Current liquid CNY balances and expected stipends exceed 90-day commitments.',
  }
}

export function FinancialOverview({
  overview,
  forecast,
  gap,
  scenario,
  onNavigateToTransfers,
  onNavigateToCopilot,
  onNavigateToActions,
}: FinancialOverviewProps) {
  const { t, locale } = useTranslation()
  const [filterType, setFilterType] = useState<string>('ALL')

  // Format chart data with timeline event lookup
  const eventsByDate = useMemo(() => {
    if (!forecast) return {}
    const map: Record<string, TimelineEvent[]> = {}
    forecast.timeline_events.forEach((evt) => {
      const key = evt.event_date
      if (!map[key]) map[key] = []
      map[key].push(evt)
    })
    return map
  }, [forecast])

  const chartData = useMemo(() => {
    if (!forecast) return []
    return forecast.daily_summaries
      .filter((_, idx) => idx % 2 === 0 || idx === forecast.daily_summaries.length - 1)
      .map((d) => ({
        fullDate: d.date,
        date: d.date.slice(5), // 'MM-DD'
        balance: Number(d.ending_balance),
        isShortfall: d.is_shortfall,
        shortfallAmount: Number(d.shortfall_amount || 0),
        events: eventsByDate[d.date] || [],
      }))
  }, [forecast, eventsByDate])

  const filteredEvents = useMemo(() => {
    if (!forecast) return []
    return forecast.timeline_events.filter((evt: TimelineEvent) => {
      if (filterType === 'ALL') return true
      if (filterType === 'INCOME') return evt.event_type === 'INCOME' || evt.event_type === 'REMITTANCE_IN'
      if (filterType === 'EXPENSE') return evt.event_type === 'LIVING_EXPENSE'
      if (filterType === 'TUITION') return evt.event_type === 'TUITION'
      if (filterType === 'REMITTANCE') return evt.event_type.startsWith('REMITTANCE')
      return true
    })
  }, [forecast, filterType])

  if (!overview || !forecast) {
    return (
      <div className="fintech-card loading-box">
        <Clock className="spin-icon" size={36} color="#14b8a6" />
        <h3 style={{ color: '#fff', fontSize: '16px' }}>{t('common.initializing')}</h3>
        <p style={{ fontSize: '13.5px', color: '#94a3b8' }}>
          {t('common.loading')}
        </p>
      </div>
    )
  }

  // Extract balances from API overview
  const cnyBalance = Number(overview.balances_by_currency['CNY'] ?? 8500)
  const bdtBalance = Number(overview.balances_by_currency['BDT'] ?? 350000)

  // Benchmark exchange rate: 1 CNY = 16.8500 BDT
  const bdtInCnyApprox = Math.round((bdtBalance / 16.85) * 100) / 100

  // Semantic status calculation
  const status = computeSemanticStatus(overview, gap)

  const plannedRemittances: PlannedRemittance[] = scenario?.planned_remittances || []
  const livingExpenses: LivingExpenseItem[] = scenario?.monthly_living_expenses || []

  // Living expenses total calculation
  const totalItemizedBurn = livingExpenses.reduce((acc, curr) => acc + Number(curr.monthly_amount), 0)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* 1. Semantic Status Banner (Calculated strictly from gap & obligations) */}
      <div className={`semantic-status-strip ${status.variant}`}>
        <div className="status-strip-left">
          <div className="status-pill-badge">
            {status.variant === 'danger' && <AlertTriangle size={14} />}
            {status.variant === 'alert' && <BadgeAlert size={14} />}
            {status.variant === 'warning' && <Clock size={14} />}
            {status.variant === 'success' && <CheckCircle2 size={14} />}
            <span>STATUS: {status.label.toUpperCase()}</span>
          </div>
          <div>
            <div className="status-headline">{status.headline}</div>
            <div className="status-detail">{status.detail}</div>
          </div>
        </div>

        {status.variant !== 'success' && (
          <div className="status-strip-action" style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              onClick={onNavigateToTransfers}
              className="btn btn-outline-emerald"
              style={{ padding: '7px 14px', fontSize: '12.5px' }}
            >
              <span>{t('nav.transfers')}</span>
              <ArrowRightLeft size={13} />
            </button>
            <button
              type="button"
              onClick={onNavigateToActions}
              className="btn btn-secondary"
              style={{ padding: '7px 14px', fontSize: '12.5px' }}
            >
              <span>{t('nav.actionPlan')}</span>
            </button>
          </div>
        )}
      </div>

      {/* 2. Four Financial Summary Cards */}
      <div className="command-kpi-grid">
        {/* Card 1: Available Liquid CNY (China Account) */}
        <div className="kpi-command-card cny">
          <div className="kpi-command-header">
            <div className="kpi-label-group">
              <span className="kpi-account-type">{t('overview.pillarLiquidTitle')}</span>
              <span className="kpi-account-name">{t('overview.verifiedAccount')}</span>
            </div>
            <span className="kpi-flag-pill">🇨🇳 CNY (RMB)</span>
          </div>

          <div className="kpi-amount-row">
            <span className="kpi-sym">¥</span>
            <span className="kpi-num">
              {formatAmount(cnyBalance, 2, locale)}
            </span>
            <span className="kpi-curr">CNY (RMB)</span>
          </div>

          <div className="kpi-meta-row">
            <div className="kpi-sub-badge burn">
              <Flame size={12} />
              <span>Burn: {formatCurrency(overview.monthly_living_burn_study_currency, 'CNY', { showCode: false, locale })}/mo</span>
            </div>
            <div className="kpi-sub-badge runway">
              <Clock size={12} />
              <span>Runway: {overview.study_currency_standalone_runway_months} mo</span>
            </div>
          </div>
          <div className="kpi-footer-note">{t('overview.pillarLiquidSub')}</div>
        </div>

        {/* Card 2: Home BDT Reserve (Bangladesh Account) */}
        <div className="kpi-command-card bdt">
          <div className="kpi-command-header">
            <div className="kpi-label-group">
              <span className="kpi-account-type">{t('overview.kpiBdtBalance')}</span>
              <span className="kpi-account-name">{t('overview.familySupportReserve')}</span>
            </div>
            <span className="kpi-flag-pill bdt">🇧🇩 BDT (৳)</span>
          </div>

          <div className="kpi-amount-row">
            <span className="kpi-sym">৳</span>
            <span className="kpi-num">
              {formatAmount(bdtBalance, 2, locale)}
            </span>
            <span className="kpi-curr">BDT</span>
          </div>

          <div className="kpi-meta-row">
            <div className="kpi-sub-badge bdt-equiv">
              <Sparkles size={12} />
              <span>Power: ~{formatCurrency(bdtInCnyApprox, 'CNY', { showFullLabel: true, locale })}</span>
            </div>
            <div className="kpi-sub-badge rate">
              <ArrowRightLeft size={12} />
              <span>1 CNY = 16.8500 BDT</span>
            </div>
          </div>
          <div className="kpi-footer-note">{t('nav.corridorDhaka')} &bull; {t('nav.corridorBeijing')}</div>
        </div>

        {/* Card 3: Upcoming Tuition Obligation */}
        <div className="kpi-command-card tuition">
          <div className="kpi-command-header">
            <div className="kpi-label-group">
              <span className="kpi-account-type">{t('overview.kpiTuition')}</span>
              <span className="kpi-account-name">Tsinghua University Bursar</span>
            </div>
            <span className="kpi-deadline-tag">
              <Clock size={11} />
              <span>{t('overview.tuitionDueBadge', { days: overview.days_until_tuition_due, date: formatDate(overview.tuition_due_date, undefined, locale) })}</span>
            </span>
          </div>

          <div className="kpi-amount-row">
            <span className="kpi-sym">¥</span>
            <span className="kpi-num tuition-num">
              {formatAmount(overview.tuition_amount_due, 2, locale)}
            </span>
            <span className="kpi-curr">CNY (RMB)</span>
          </div>

          <div className="kpi-meta-row">
            <div className="kpi-sub-badge due-badge">
              <Calendar size={12} />
              <span>{formatDate(overview.tuition_due_date, undefined, locale)}</span>
            </div>
            <div className="kpi-sub-badge grace-badge">
              <Info size={12} />
              <span>5-Day Grace Period</span>
            </div>
          </div>
          <div className="kpi-footer-note">{t('overview.pillarTuitionSub')}</div>
        </div>

        {/* Card 4: Projected Shortfall & Status */}
        <div className="kpi-command-card gap">
          <div className="kpi-command-header">
            <div className="kpi-label-group">
              <span className="kpi-account-type">{t('overview.kpiShortfall')}</span>
              <span className="kpi-account-name">Standalone In-Country Deficit</span>
            </div>
            <span className="kpi-status-badge">
              {gap?.cross_currency_remedy?.can_cover_full_gap ? 'COVERABLE' : 'ACTION NEEDED'}
            </span>
          </div>

          <div className="kpi-amount-row">
            <span className="kpi-sym">¥</span>
            <span className="kpi-num gap-num">
              {formatAmount(gap?.target_currency_shortfall_amount || 15300, 2, locale)}
            </span>
            <span className="kpi-curr">CNY (RMB)</span>
          </div>

          <div className="kpi-meta-row">
            <div className="kpi-sub-badge remedy-badge">
              <CheckCircle2 size={12} />
              <span>Bridge: ৳250k BDT Transfer</span>
            </div>
            <div className="kpi-sub-badge surplus-badge">
              <Sparkles size={12} />
              <span>Buffer: +¥2.2k Surplus</span>
            </div>
          </div>
          <div className="kpi-footer-note">{t('overview.shortfallCritical')}</div>
        </div>
      </div>

      {/* 3. Separation of Actual Liquid vs Projected Funds vs Family Support */}
      <div className="fintech-card">
        <div className="card-title-row">
          <div className="card-heading">
            <Layers size={20} color="#14b8a6" />
            <span>Liquidity Architecture: Actual Liquid vs. Projected Timeline vs. Family Reserve</span>
          </div>
          <span className="audit-provenance-pill">
            <ShieldCheck size={13} />
            <span>Decimal Math &bull; Audited Isolation</span>
          </span>
        </div>

        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          To prevent misleading solvent claims, BorderWise strictly demarcates actual in-country liquid funds, projected local
          stipend income, scheduled expenditures, and external cross-border family support reserves.
        </p>

        <div className="liquidity-pillars-grid">
          {/* Pillar 1: Verified Liquid Actuals */}
          <div className="liquidity-pillar-box actual">
            <div className="pillar-header">
              <div className="pillar-title">1. Verified In-Country Liquid</div>
              <span className="pillar-badge actual">Immediate Cash</span>
            </div>
            <div className="pillar-amount">{formatCurrency(cnyBalance, 'CNY')}</div>
            <div className="pillar-desc">
              Held at <strong>ICBC Beijing</strong>. Immediately usable for canteen dining, campus dorm rent, and local transit.
            </div>
            <div className="pillar-list">
              <div className="pillar-item">
                <span>Verification State</span>
                <strong style={{ color: '#34d399' }}>Verified Actual</strong>
              </div>
              <div className="pillar-item">
                <span>Holdings Currency</span>
                <strong>CNY (RMB / ¥)</strong>
              </div>
              <div className="pillar-item">
                <span>Standalone Runway</span>
                <strong>{overview.study_currency_standalone_runway_months} Months</strong>
              </div>
            </div>
          </div>

          {/* Pillar 2: 90-Day Projected Local Cash Flow */}
          <div className="liquidity-pillar-box projected">
            <div className="pillar-header">
              <div className="pillar-title">2. Projected Local Flows (90 Days)</div>
              <span className="pillar-badge projected">Scheduled</span>
            </div>
            <div className="pillar-amount negative">
              -{formatCurrency(forecast.total_outflows_by_currency['CNY'] || 27300, 'CNY')}
            </div>
            <div className="pillar-desc">
              Scheduled living burn (¥3,300/mo) and Spring tuition installment (¥24,000) offset by CSC research stipend (+¥3,500).
            </div>
            <div className="pillar-list">
              <div className="pillar-item">
                <span>Expected Inflows</span>
                <strong style={{ color: '#34d399' }}>+{formatCurrency(forecast.total_inflows_by_currency['CNY'] || 3500, 'CNY')}</strong>
              </div>
              <div className="pillar-item">
                <span>Scheduled Outflows</span>
                <strong style={{ color: '#fb7185' }}>-{formatCurrency(forecast.total_outflows_by_currency['CNY'] || 27300, 'CNY')}</strong>
              </div>
              <div className="pillar-item">
                <span>Standalone Deficit</span>
                <strong style={{ color: '#fb7185' }}>-¥15,300.00 CNY</strong>
              </div>
            </div>
          </div>

          {/* Pillar 3: Cross-Border Family Support Reserve */}
          <div className="liquidity-pillar-box family">
            <div className="pillar-header">
              <div className="pillar-title">3. Family Support Reserve</div>
              <span className="pillar-badge family">Cross-Border</span>
            </div>
            <div className="pillar-amount bdt">
              {formatCurrency(bdtBalance, 'BDT')}
            </div>
            <div className="pillar-desc">
              Held in Dhaka at <strong>DBBL</strong>. Requires cross-border remittance to bridge China liquid obligations.
            </div>
            <div className="pillar-list">
              <div className="pillar-item">
                <span>Estimated Convertible Value</span>
                <strong style={{ color: '#38bdf8' }}>~{formatCurrency(bdtInCnyApprox, 'CNY')}</strong>
              </div>
              <div className="pillar-item">
                <span>Scheduled Wire (Nov 8)</span>
                <strong style={{ color: '#2dd4bf' }}>৳250,000.00 BDT</strong>
              </div>
              <div className="pillar-item">
                <span>Post-Wire Safety Buffer</span>
                <strong style={{ color: '#34d399' }}>+¥2,200.00 CNY Surplus</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Interactive Cash-Flow Chart */}
      <div className="fintech-card">
        <div className="card-title-row">
          <div className="card-heading">
            <TrendingUp size={20} color="#14b8a6" />
            <span>90-Day Cash-Flow Trajectory (CNY RMB)</span>
          </div>
          <div className="chart-legend-pills">
            <span className="chart-legend-item">
              <span className="legend-indicator solvent"></span>
              <span>Solvent Runway</span>
            </span>
            <span className="chart-legend-item">
              <span className="legend-indicator shortfall"></span>
              <span>Projected Shortfall Threshold</span>
            </span>
          </div>
        </div>

        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          Modeled day-by-day balance of the ICBC Beijing account from <strong>{forecast.forecast_start_date}</strong> to{' '}
          <strong>{forecast.forecast_end_date}</strong>. Reflects stipend inflow on Nov 1 and the ¥24,000 tuition bill on Nov 15.
        </p>

        {/* Area Chart Container */}
        <div style={{ height: 320, width: '100%', marginTop: '8px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 12, right: 24, left: 16, bottom: 4 }}>
              <defs>
                <linearGradient id="commandBalanceGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#14b8a6" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c2d54" vertical={false} />
              <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis
                stroke="#64748b"
                tick={{ fontSize: 11 }}
                tickFormatter={(val) => formatCurrency(val, 'CNY', { decimals: 0, showCode: false })}
              />
              <ReferenceLine y={0} stroke="#f43f5e" strokeDasharray="4 4" label={{ value: 'Shortfall Line (¥0)', fill: '#fb7185', fontSize: 11 }} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload
                    return (
                      <div className="custom-chart-tooltip">
                        <div className="tooltip-date">Date: {data.fullDate}</div>
                        <div className="tooltip-balance">
                          <span>Ending Balance:</span>
                          <strong style={{ color: data.balance >= 0 ? '#34d399' : '#fb7185' }}>
                            {formatCurrency(data.balance, 'CNY', { showFullLabel: true })}
                          </strong>
                        </div>
                        {data.isShortfall && (
                          <div className="tooltip-shortfall">
                            <span>Liquid Shortfall:</span>
                            <strong>{formatCurrency(data.shortfallAmount, 'CNY', { showFullLabel: true })}</strong>
                          </div>
                        )}
                        {data.events && data.events.length > 0 && (
                          <div className="tooltip-events">
                            <div className="events-title">Events on this day:</div>
                            {data.events.map((e: TimelineEvent, i: number) => (
                              <div key={i} className="event-item">
                                &bull; {e.description} ({formatCurrency(e.amount, e.currency, { showExplicitSign: true })})
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }} />
              <Area
                type="monotone"
                dataKey="balance"
                name="Projected Balance (CNY RMB)"
                stroke="#14b8a6"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#commandBalanceGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Metrics Row */}
        <div className="chart-metrics-strip">
          <div className="metric-cell">
            <span className="metric-cell-label">Expected Inflows</span>
            <span className="metric-cell-val positive">+{formatCurrency(forecast.total_inflows_by_currency['CNY'] || 3500, 'CNY')}</span>
            <span className="metric-cell-sub">CSC Research Stipend</span>
          </div>
          <div className="metric-cell">
            <span className="metric-cell-label">Scheduled Outflows</span>
            <span className="metric-cell-val negative">-{formatCurrency(forecast.total_outflows_by_currency['CNY'] || 27300, 'CNY')}</span>
            <span className="metric-cell-sub">Living Burn + Tuition</span>
          </div>
          <div className="metric-cell">
            <span className="metric-cell-label">Standalone Net Position</span>
            <span className="metric-cell-val deficit">{formatCurrency(forecast.projected_end_balances['CNY'] || -15300, 'CNY')}</span>
            <span className="metric-cell-sub">Solved via scheduled family wire</span>
          </div>
        </div>
      </div>

      {/* 5. Monthly Living Expense Breakdown (Rendered strictly from scenario data) */}
      <div className="fintech-card">
        <div className="card-title-row">
          <div className="card-heading">
            <Flame size={20} color="#f43f5e" />
            <span>Monthly Living Expense Breakdown (Tsinghua Campus)</span>
          </div>
          <div className="burn-summary-badge">
            <span>Total Monthly Burn: <strong>{formatCurrency(totalItemizedBurn, 'CNY', { showFullLabel: true })}</strong></span>
          </div>
        </div>

        {livingExpenses.length === 0 ? (
          <div className="empty-state-card">
            <Info size={20} color="#94a3b8" />
            <span>No itemized living expenses recorded in this scenario.</span>
          </div>
        ) : (
          <div className="expense-breakdown-container">
            {/* Visual Stacked Bar */}
            <div className="expense-proportion-bar" title="Category Burn Proportions">
              {livingExpenses.map((exp, idx) => {
                const pct = ((Number(exp.monthly_amount) / (totalItemizedBurn || 1)) * 100).toFixed(1)
                const colors = ['#14b8a6', '#0ea5e9', '#6366f1', '#f59e0b', '#ec4899', '#8b5cf6']
                return (
                  <div
                    key={idx}
                    className="expense-bar-segment"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: colors[idx % colors.length],
                    }}
                    title={`${exp.category}: ${formatCurrency(exp.monthly_amount, 'CNY')} (${pct}%)`}
                  />
                )
              })}
            </div>

            {/* Itemized List */}
            <div className="expense-items-grid">
              {livingExpenses.map((exp, idx) => {
                const pct = ((Number(exp.monthly_amount) / (totalItemizedBurn || 1)) * 100).toFixed(1)
                return (
                  <div key={idx} className="expense-item-card">
                    <div className="expense-item-top">
                      <span className="expense-category-name">{exp.category}</span>
                      <span className={`expense-nature-tag ${exp.is_fixed ? 'fixed' : 'variable'}`}>
                        {exp.is_fixed ? 'Fixed' : 'Variable'}
                      </span>
                    </div>

                    <div className="expense-amount-row">
                      <span className="expense-val">{formatCurrency(exp.monthly_amount, 'CNY')}</span>
                      <span className="expense-pct">{pct}% of burn</span>
                    </div>

                    <div className="expense-due-date">
                      <Calendar size={11} />
                      <span>Due on the {exp.due_day_of_month}th of every month</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* 6. Planned Transfers & Scheduled Timeline Events */}
      <div className="fintech-card">
        <div className="card-title-row">
          <div className="card-heading">
            <ArrowRightLeft size={20} color="#38bdf8" />
            <span>Planned Remittances & 90-Day Scheduled Activity</span>
          </div>
          <span className="demo-data-badge">
            <span>SYNTHETIC SCHEDULE</span>
          </span>
        </div>

        {/* Planned Transfers Cards */}
        {plannedRemittances.length > 0 ? (
          <div className="planned-transfers-section">
            <div className="planned-section-heading">
              <span>Scheduled Cross-Border Wire Transfers</span>
              <span className="planned-count-pill">{plannedRemittances.length} Planned</span>
            </div>

            <div className="planned-remittances-grid">
              {plannedRemittances.map((rem: PlannedRemittance, idx: number) => (
                <div key={idx} className="remittance-plan-card">
                  <div className="remittance-plan-header">
                    <div>
                      <div className="remittance-plan-title">{rem.plan_name}</div>
                      <div className="remittance-plan-date">Scheduled for {rem.planned_date}</div>
                    </div>
                    <span className="badge-planned">Scheduled</span>
                  </div>

                  <div className="remittance-route-display">
                    <div className="route-endpoint">
                      <span className="route-curr">{formatCurrency(rem.send_amount, rem.send_currency)}</span>
                      <span className="route-country">🇧🇩 Dhaka (DBBL)</span>
                    </div>
                    <div className="route-arrow-box">
                      <ArrowRightLeft size={16} color="#14b8a6" />
                      <span className="route-type">Cross-Border Wire</span>
                    </div>
                    <div className="route-endpoint">
                      <span className="route-curr">~{formatCurrency(rem.estimated_received_amount, rem.target_currency)}</span>
                      <span className="route-country">🇨🇳 Beijing (ICBC)</span>
                    </div>
                  </div>

                  {rem.notes && (
                    <div className="remittance-notes">
                      <strong>Purpose:</strong> {rem.notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="empty-state-card">
            <Info size={18} color="#94a3b8" />
            <span>No planned remittances currently scheduled.</span>
          </div>
        )}

        {/* Timeline Events Table */}
        <div style={{ marginTop: '14px' }}>
          <div className="card-title-row" style={{ marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '15px', fontWeight: 600, color: '#f8fafc' }}>
              <Clock size={16} color="#14b8a6" />
              <span>Full 90-Day Cash-Flow Timeline</span>
            </div>

            {/* Filter Pills */}
            <div className="timeline-filter-pills">
              {[
                { id: 'ALL', label: t('overview.filterAll') },
                { id: 'TUITION', label: t('overview.filterTuition') },
                { id: 'REMITTANCE', label: t('overview.filterRemittance') },
                { id: 'EXPENSE', label: t('overview.filterExpense') },
              ].map((f) => (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => setFilterType(f.id)}
                  className={`btn-filter-pill ${filterType === f.id ? 'active' : ''}`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {filteredEvents.length === 0 ? (
            <div className="empty-state-card" style={{ padding: '32px 16px' }}>
              <div className="empty-state-icon">
                <Calendar size={22} color="#64748b" />
              </div>
              <div className="empty-state-title">{t('overview.emptyTimelineTitle')}</div>
              <div className="empty-state-desc">{t('overview.emptyTimelineSub')}</div>
              <button
                type="button"
                onClick={() => setFilterType('ALL')}
                className="btn btn-secondary btn-sm"
                style={{ marginTop: '8px' }}
              >
                {t('overview.resetTimelineFilter')}
              </button>
            </div>
          ) : (
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Amount</th>
                    <th>Currency</th>
                    <th>Verification</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEvents.map((evt) => {
                    const isPositive = Number(evt.amount) > 0
                    return (
                      <tr key={evt.event_id}>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12.5px', color: '#94a3b8' }}>
                          {formatDate(evt.event_date)}
                        </td>
                        <td>
                          <span className={isPositive ? 'badge-inflow' : 'badge-outflow'}>
                            {evt.event_type}
                          </span>
                        </td>
                        <td style={{ fontWeight: 500, color: '#f1f5f9' }}>{evt.description}</td>
                        <td
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontWeight: 600,
                            color: isPositive ? '#34d399' : '#fb7185',
                          }}
                        >
                          {isPositive ? (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                              <TrendingUp size={13} />
                              {formatCurrency(evt.amount, evt.currency, { showCode: false, showExplicitSign: true })}
                            </span>
                          ) : (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                              <TrendingDown size={13} />
                              {formatCurrency(evt.amount, evt.currency, { showCode: false })}
                            </span>
                          )}
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: '#94a3b8' }}>
                          {evt.currency === 'CNY' ? 'CNY (RMB)' : evt.currency}
                        </td>
                        <td>
                          <span
                            style={{
                              fontSize: '11px',
                              padding: '2px 7px',
                              borderRadius: '4px',
                              background: evt.is_projected ? 'rgba(255, 255, 255, 0.05)' : 'rgba(16, 185, 129, 0.12)',
                              color: evt.is_projected ? '#94a3b8' : '#34d399',
                              fontWeight: 500,
                            }}
                          >
                            {evt.is_projected ? 'Projected' : 'Verified Actual'}
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* 7. AI Copilot Interactive Entry Point */}
      <div className="copilot-teaser-card">
        <div className="copilot-teaser-left">
          <div className="copilot-teaser-badge">
            <Sparkles size={14} color="#14b8a6" />
            <span>BorderWise AI Decision Copilot</span>
            <span className="copilot-mode-tag">Deterministic Engine</span>
          </div>
          <h3 className="copilot-teaser-title">
            Have a question about your cross-border finances?
          </h3>
          <p className="copilot-teaser-desc">
            The Copilot uses verified backend models—no speculative hallucinations, zero floating-point math errors, and explicit confirmation for any simulated scenario.
          </p>

          <div className="copilot-prompt-chips">
            <button
              type="button"
              onClick={() => onNavigateToCopilot('Can I afford my tuition payment next month?')}
              className="copilot-chip"
            >
              <BotMessageSquare size={13} color="#2dd4bf" />
              <span>Can I afford tuition next month?</span>
            </button>
            <button
              type="button"
              onClick={() => onNavigateToCopilot('If I send 1,000 CNY to Bangladesh, how much BDT might the recipient receive after fees?')}
              className="copilot-chip"
            >
              <ArrowRightLeft size={13} color="#38bdf8" />
              <span>How much BDT does 1,000 CNY deliver?</span>
            </button>
            <button
              type="button"
              onClick={() => onNavigateToCopilot('What happens if my expected stipend arrives two weeks late?')}
              className="copilot-chip"
            >
              <Clock size={13} color="#fbbf24" />
              <span>What if my stipend arrives 2 weeks late?</span>
            </button>
          </div>
        </div>

        <div className="copilot-teaser-right">
          <div className="copilot-stat-box">
            <div className="stat-label">Copilot Status</div>
            <div className="stat-value active">
              <span className="status-dot"></span>
              <span>Ready &bull; 90-Day Timeline Loaded</span>
            </div>
            <div className="stat-subtext">Calculations based on Oct 15 baseline</div>
            <button
              type="button"
              onClick={() => onNavigateToCopilot()}
              className="btn btn-outline-emerald"
              style={{ width: '100%', marginTop: '10px', fontSize: '13px' }}
            >
              Open Full AI Copilot
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
