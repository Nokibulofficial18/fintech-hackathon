import { useState, useEffect, useId } from 'react'
import {
  ArrowRightLeft,
  Clock,
  Sparkles,
  Info,
  Calendar,
  ShieldCheck,
  Building,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  LayoutGrid,
  Table as TableIcon,
  RefreshCw,
  Zap,
} from 'lucide-react'
import { fetchTransferComparison } from '../services/api'
import type { TransferCompareResponse, SupportedCurrency, DetailedTransferQuote } from '../types/api'
import {
  formatCurrency,
  formatAmount,
  formatExchangeRate,
  formatPercent,
  formatDate,
  getCurrencySymbol,
  getCurrencyLabel,
} from '../utils/formatters'
import { useTranslation } from '../i18n/useTranslation'

interface TransferComparisonProps {
  initialSendAmount?: number
  initialSendCurrency?: SupportedCurrency
  initialReceiveCurrency?: SupportedCurrency
}

export function TransferComparison({
  initialSendAmount = 1000,
  initialSendCurrency = 'CNY',
  initialReceiveCurrency = 'BDT',
}: TransferComparisonProps = {}) {
  const { t, locale } = useTranslation()
  // CNY -> BDT is the default transfer direction for students in China remitting home or receiving funds
  const [sendAmount, setSendAmount] = useState<number>(initialSendAmount)
  const [amountInputStr, setAmountInputStr] = useState<string>(String(initialSendAmount))
  const [sendCurrency, setSendCurrency] = useState<SupportedCurrency>(initialSendCurrency)
  const [receiveCurrency, setReceiveCurrency] = useState<SupportedCurrency>(initialReceiveCurrency)
  const [comparison, setComparison] = useState<TransferCompareResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [inputError, setInputError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards')
  const [selectedBreakdownProvider, setSelectedBreakdownProvider] = useState<string | null>(null)

  const amountInputId = useId()
  const sendSelectId = useId()
  const receiveSelectId = useId()

  const handleSwapCurrencies = () => {
    const nextSend = receiveCurrency
    const nextReceive = sendCurrency
    setSendCurrency(nextSend)
    setReceiveCurrency(nextReceive)
    setInputError(null)

    // Set realistic preset when swapping
    if (nextSend === 'BDT') {
      setSendAmount(250000)
      setAmountInputStr('250000')
    } else if (nextSend === 'CNY') {
      setSendAmount(1000)
      setAmountInputStr('1000')
    }
  }

  const validateInput = (value: number, sCurr: string, rCurr: string): string | null => {
    if (isNaN(value) || value <= 0) {
      return `Please enter a valid transfer amount greater than 0 ${sCurr}.`
    }
    if (value > 5000000) {
      return `Transfer amount exceeds maximum educational planning simulation limit (5,000,000 ${sCurr}).`
    }
    if (sCurr === rCurr) {
      return 'Sending and receiving currency must be different for cross-border transfer comparison.'
    }
    return null
  }

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const rawVal = e.target.value
    setAmountInputStr(rawVal)
    const num = parseFloat(rawVal)

    const err = validateInput(num, sendCurrency, receiveCurrency)
    setInputError(err)

    if (!err && !isNaN(num)) {
      setSendAmount(num)
    }
  }

  const handleSelectPreset = (presetVal: number) => {
    setSendAmount(presetVal)
    setAmountInputStr(String(presetVal))
    setInputError(null)
  }

  const loadQuotes = async () => {
    const num = parseFloat(amountInputStr)
    const validationErr = validateInput(num, sendCurrency, receiveCurrency)
    if (validationErr) {
      setInputError(validationErr)
      return
    }

    setLoading(true)
    setError(null)
    setInputError(null)

    try {
      const data = await fetchTransferComparison(num, sendCurrency, receiveCurrency)
      setComparison(data)
      if (data.quotes.length > 0) {
        setSelectedBreakdownProvider(data.recommended_cheapest || data.quotes[0].provider_name)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to query transfer comparison')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let isCancelled = false
    const runInitialQuery = async () => {
      setLoading(true)
      try {
        const data = await fetchTransferComparison(initialSendAmount, initialSendCurrency, initialReceiveCurrency)
        if (!isCancelled) {
          setComparison(data)
          if (data.quotes.length > 0) {
            setSelectedBreakdownProvider(data.recommended_cheapest || data.quotes[0].provider_name)
          }
        }
      } catch (err: unknown) {
        if (!isCancelled) {
          setError(err instanceof Error ? err.message : 'Failed to query transfer comparison')
        }
      } finally {
        if (!isCancelled) {
          setLoading(false)
        }
      }
    }
    runInitialQuery()
    return () => {
      isCancelled = true
    }
  }, [initialSendAmount, initialSendCurrency, initialReceiveCurrency])

  const getDisplaySymbol = getCurrencySymbol

  // Active breakdown provider quote
  const activeQuote = comparison?.quotes.find((q) => q.provider_name === selectedBreakdownProvider) || comparison?.quotes[0]

  // Traditional bank quote for relative benefit comparison
  const tradBankQuote = comparison?.quotes.find((q) => q.provider_type === 'TRADITIONAL_BANK')
  const cheapestQuote = comparison?.quotes.find((q) => q.provider_name === comparison.recommended_cheapest)

  const extraProceedsVsBank =
    cheapestQuote && tradBankQuote
      ? Number(cheapestQuote.recipient_amount_receive_currency) - Number(tradBankQuote.recipient_amount_receive_currency)
      : 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* 1. Prominent Transfer Calculator Card */}
      <div className="fintech-card transfer-calculator-card">
        <div className="card-title-row">
          <div className="card-heading">
            <ArrowRightLeft size={20} color="#14b8a6" />
            <span>{t('transfers.calculatorTitle')}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="demo-data-badge">
              <span>{t('common.demoTag')} &bull; {t('common.simulatedBenchmark')}</span>
            </span>
            <span className="corridor-pill">
              <span>{sendCurrency === 'CNY' ? 'CNY (RMB)' : sendCurrency} ⇄ {receiveCurrency === 'CNY' ? 'CNY (RMB)' : receiveCurrency}</span>
            </span>
          </div>
        </div>

        <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          {t('transfers.calculatorSubtitle')}
        </p>

        {/* Transfer Input Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault()
            loadQuotes()
          }}
          className="transfer-calculator-form"
        >
          <div className="transfer-inputs-grid">
            {/* Amount Input */}
            <div className="form-group-field">
              <label className="input-label" htmlFor={amountInputId}>
                {t('transfers.sendingAmount')} ({sendCurrency === 'CNY' ? 'CNY (RMB)' : sendCurrency})
              </label>
              <div className="input-with-affix">
                <span className="input-affix">{getDisplaySymbol(sendCurrency)}</span>
                <input
                  id={amountInputId}
                  type="number"
                  step="any"
                  min="1"
                  value={amountInputStr}
                  onChange={handleAmountChange}
                  className={`input-control ${inputError ? 'input-error' : ''}`}
                  style={{ paddingLeft: '32px', fontFamily: 'var(--font-mono)' }}
                  placeholder={`Enter amount in ${sendCurrency}`}
                  aria-invalid={inputError ? 'true' : 'false'}
                  aria-describedby={inputError ? 'amount-error-msg' : undefined}
                />
              </div>
            </div>

            {/* Source Currency */}
            <div className="form-group-field">
              <label className="input-label" htmlFor={sendSelectId}>
                {t('transfers.fromCurrency')}
              </label>
              <select
                id={sendSelectId}
                value={sendCurrency}
                onChange={(e) => {
                  setSendCurrency(e.target.value as SupportedCurrency)
                  setInputError(null)
                }}
                className="input-control"
              >
                <option value="CNY">CNY (RMB) — Chinese Yuan (¥)</option>
                <option value="BDT">BDT — Bangladeshi Taka (৳)</option>
                <option value="USD">USD — US Dollar ($)</option>
                <option value="EUR">EUR — Euro (€)</option>
              </select>
            </div>

            {/* Direction Switch Control (Swap button) */}
            <div className="swap-button-container">
              <button
                type="button"
                onClick={handleSwapCurrencies}
                className="btn btn-secondary swap-btn"
                title={t('transfers.switchDirection')}
                aria-label={t('transfers.switchDirection')}
              >
                <ArrowRightLeft size={16} color="#14b8a6" />
                <span>{t('transfers.switchDirection')}</span>
              </button>
            </div>

            {/* Destination Currency */}
            <div className="form-group-field">
              <label className="input-label" htmlFor={receiveSelectId}>
                {t('transfers.toCurrency')}
              </label>
              <select
                id={receiveSelectId}
                value={receiveCurrency}
                onChange={(e) => {
                  setReceiveCurrency(e.target.value as SupportedCurrency)
                  setInputError(null)
                }}
                className="input-control"
              >
                <option value="BDT">BDT — Bangladeshi Taka (৳)</option>
                <option value="CNY">CNY (RMB) — Chinese Yuan (¥)</option>
                <option value="USD">USD — US Dollar ($)</option>
                <option value="EUR">EUR — Euro (€)</option>
              </select>
            </div>
          </div>

          {/* Validation Error Banner */}
          {inputError && (
            <div id="amount-error-msg" className="inline-validation-error" role="alert">
              <AlertCircle size={15} />
              <span>{inputError}</span>
            </div>
          )}

          {/* Quick Presets & Submit Button */}
          <div className="calculator-footer-row">
            <div className="quick-presets-strip">
              <span className="presets-label">{t('transfers.quickPresets')}</span>
              {(sendCurrency === 'BDT'
                ? [50000, 100000, 250000, 300000, 500000]
                : [500, 1000, 2500, 5000, 10000]
              ).map((preset) => (
                <button
                  key={preset}
                  type="button"
                  onClick={() => handleSelectPreset(preset)}
                  className={`suggestion-chip ${sendAmount === preset ? 'active' : ''}`}
                >
                  {formatAmount(preset, 0, locale)} {sendCurrency === 'CNY' ? 'CNY (RMB)' : sendCurrency}
                </button>
              ))}
            </div>

            <button
              type="submit"
              disabled={loading || !!inputError}
              className="btn btn-primary submit-compare-btn"
            >
              {loading ? (
                <>
                  <RefreshCw size={15} className="spin-icon" />
                  <span>{t('transfers.comparingButton')}</span>
                </>
              ) : (
                <>
                  <TrendingUp size={15} />
                  <span>{t('transfers.compareButton')}</span>
                </>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="alert-error-banner" style={{ marginTop: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
            <button
              type="button"
              onClick={loadQuotes}
              className="btn btn-secondary"
              style={{ padding: '6px 12px', fontSize: '12px' }}
            >
              {t('common.retry')}
            </button>
          </div>
        )}
      </div>

      {/* Loading Skeleton */}
      {loading && !comparison && (
        <div className="fintech-card loading-box">
          <RefreshCw className="spin-icon" size={32} color="#14b8a6" />
          <h3 style={{ color: '#fff', fontSize: '15px' }}>Querying Central Bank Parity & Multi-Provider Benchmarks</h3>
          <p style={{ fontSize: '13px', color: '#94a3b8' }}>
            Decomposing wire fees, foreign exchange spreads, and estimated arrival SLAs...
          </p>
        </div>
      )}

      {/* Comparison Results */}
      {comparison && (
        <>
          {/* 2. Explicit Exchange Rate & Benchmark Banner */}
          <div className="transparency-banner rate-direction-banner">
            <div className="banner-item">
              <Sparkles size={18} color="#34d399" />
              <div>
                <span className="rate-direction-label">{t('transfers.benchmarkRate')}</span>
                <span className="rate-direction-val">
                  {formatExchangeRate(
                    comparison.mid_market_rate,
                    getCurrencyLabel(comparison.send_currency),
                    getCurrencyLabel(comparison.receive_currency),
                    4,
                    locale
                  )}
                </span>
                <span className="rate-inverse-sub">
                  (Inverse:{' '}
                  {formatExchangeRate(
                    1 / Number(comparison.mid_market_rate),
                    getCurrencyLabel(comparison.receive_currency),
                    getCurrencyLabel(comparison.send_currency),
                    4,
                    locale
                  )}
                  )
                </span>
              </div>
            </div>

            <div className="banner-item rate-meta-group">
              <div className="rate-meta-item">
                <Calendar size={13} color="#94a3b8" />
                <span>{t('transfers.sourceSimulated')}</span>
              </div>
              <div className="rate-meta-item">
                <Clock size={13} color="#14b8a6" />
                <span>{t('transfers.updatedTag')} <strong>{formatDate(comparison.quotes_timestamp_utc, undefined, locale)}</strong></span>
              </div>
              <div className="rate-meta-item">
                <ShieldCheck size={13} color="#38bdf8" />
                <span className="demo-status-tag">{t('common.demoTag')}</span>
              </div>
            </div>
          </div>

          {/* Highlight Benefit Callout if potential savings exist */}
          {Number(comparison.potential_savings_vs_bank) > 0 && (
            <div className="savings-highlight-callout">
              <div className="savings-callout-icon">
                <Zap size={20} color="#10b981" />
              </div>
              <div className="savings-callout-text">
                <div className="savings-callout-title">
                  {t('transfers.savingsAdvantageTitle', {
                    amount: formatCurrency(comparison.potential_savings_vs_bank, comparison.send_currency, { showFullLabel: true, locale }),
                  })}
                </div>
                <div className="savings-callout-desc">
                  {extraProceedsVsBank > 0 && (
                    <span>
                      {t('transfers.savingsAdvantageDesc', {
                        amount: formatCurrency(extraProceedsVsBank, comparison.receive_currency, { showExplicitSign: true, showFullLabel: true, locale }),
                        provider: comparison.recommended_cheapest,
                      })}
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* View Mode Toggle Bar */}
          <div className="view-toggle-row">
            <div className="view-toggle-left">
              <span className="options-count-text">
                {t('transfers.availableProviders', { count: comparison.quotes.length })}
              </span>
            </div>

            <div className="view-mode-buttons" role="group" aria-label="View format">
              <button
                type="button"
                onClick={() => setViewMode('cards')}
                className={`btn-view-toggle ${viewMode === 'cards' ? 'active' : ''}`}
                aria-pressed={viewMode === 'cards'}
                title={t('transfers.cardView')}
              >
                <LayoutGrid size={14} />
                <span>{t('transfers.cardView')}</span>
              </button>
              <button
                type="button"
                onClick={() => setViewMode('table')}
                className={`btn-view-toggle ${viewMode === 'table' ? 'active' : ''}`}
                aria-pressed={viewMode === 'table'}
                title={t('transfers.tableView')}
              >
                <TableIcon size={14} />
                <span>{t('transfers.tableView')}</span>
              </button>
            </div>
          </div>

          {/* 3. Card View or Table View or Empty State */}
          {comparison.quotes.length === 0 ? (
            <div className="fintech-card empty-state-card" style={{ padding: '40px 24px', textAlign: 'center' }}>
              <Building size={32} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
              <h3 style={{ color: '#fff', fontSize: '16px', marginBottom: '6px' }}>{t('transfers.noQuotesTitle')}</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', maxWidth: '440px', margin: '0 auto 16px' }}>
                {t('transfers.noQuotesDesc')}
              </p>
              <button
                type="button"
                onClick={() => handleSelectPreset(sendCurrency === 'BDT' ? 50000 : 1000)}
                className="btn btn-secondary"
              >
                {t('transfers.resetPresets')}
              </button>
            </div>
          ) : viewMode === 'cards' ? (
            <div className="providers-grid">
              {comparison.quotes.map((quote: DetailedTransferQuote) => {
                const isRecommendedCheapest = quote.provider_name === comparison.recommended_cheapest
                const isRecommendedFastest = quote.provider_name === comparison.recommended_fastest && !isRecommendedCheapest

                return (
                  <div
                    key={quote.provider_name}
                    className={`provider-card ${isRecommendedCheapest ? 'best-choice' : ''}`}
                  >
                    {isRecommendedCheapest && (
                      <div className="best-choice-ribbon">
                        {t('transfers.bestChoiceRibbon')}
                      </div>
                    )}

                    {isRecommendedFastest && (
                      <div className="best-choice-ribbon fastest">
                        {t('transfers.fastestRibbon')}
                      </div>
                    )}

                    <div className="provider-header-row">
                      <div>
                        <div className="provider-name">{quote.provider_name}</div>
                        <div className="provider-type-tag">
                          <Building size={11} />
                          <span>{quote.provider_type.replace(/_/g, ' ')} &bull; {quote.quote_provenance}</span>
                        </div>
                      </div>
                    </div>

                    {/* Net Recipient Proceeds Box */}
                    <div className="recipient-proceeds-box">
                      <div className="proceeds-label">{t('transfers.recipientReceives')}</div>
                      <div className="proceeds-amount">
                        {getCurrencySymbol(comparison.receive_currency)}
                        {formatAmount(quote.recipient_amount_receive_currency, 2, locale)}
                        <span className="proceeds-currency">
                          {getCurrencyLabel(comparison.receive_currency)}
                        </span>
                      </div>
                      <div className="proceeds-subtext">
                        {t('transfers.recipientSubtext')}
                      </div>
                    </div>

                    {/* Fee Decomposition List */}
                    <div className="fee-decomposition-list">
                      <div className="fee-row">
                        <span className="fee-label">{t('transfers.offeredRate')}</span>
                        <strong className="fee-val" style={{ fontFamily: 'var(--font-mono)' }}>
                          {quote.offered_exchange_rate}
                        </strong>
                      </div>

                      <div className="fee-row">
                        <span className="fee-label">{t('transfers.upfrontFee')}</span>
                        <span className="fee-val">
                          {formatCurrency(quote.upfront_transfer_fee, comparison.send_currency, { showFullLabel: true, locale })}
                        </span>
                      </div>

                      {Number(quote.other_disclosed_fees) > 0 && (
                        <div className="fee-row">
                          <span className="fee-label">{t('transfers.correspondentFee')}</span>
                          <span className="fee-val">
                            {formatCurrency(quote.other_disclosed_fees, comparison.send_currency, { showFullLabel: true, locale })}
                          </span>
                        </div>
                      )}

                      <div className="fee-row">
                        <span className="fee-label">{t('transfers.hiddenFxMargin')}</span>
                        <span
                          className="fee-val"
                          style={{ color: Number(quote.fx_markup_percentage) > 1.5 ? '#fb7185' : '#cbd5e1' }}
                        >
                          {formatPercent(quote.fx_markup_percentage)} ({formatCurrency(quote.fx_markup_amount, comparison.send_currency, { showFullLabel: true, locale })})
                        </span>
                      </div>

                      <div className="fee-row total-fee-row">
                        <span className="fee-label total">{t('transfers.totalEstimatedCost')}</span>
                        <span className="fee-val total">
                          {formatCurrency(quote.total_fee_cost, comparison.send_currency, { showFullLabel: true, locale })}
                        </span>
                      </div>
                    </div>

                    {/* Delivery SLA & Payment Methods */}
                    <div className="provider-footer-sla">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#94a3b8' }}>
                        <Clock size={13} color="#14b8a6" />
                        <span>{t('transfers.transitTime')} <strong>{quote.estimated_delivery_time}</strong></span>
                      </div>

                      {quote.payment_methods_supported && quote.payment_methods_supported.length > 0 && (
                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '4px' }}>
                          {quote.payment_methods_supported.map((pm, idx) => (
                            <span key={idx} className="method-pill">
                              {pm}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="quote-audit-note">
                        {quote.quote_notes}
                      </div>

                      {/* Math Breakdown Trigger Button */}
                      <button
                        type="button"
                        onClick={() => setSelectedBreakdownProvider(quote.provider_name)}
                        className={`btn-math-inspect ${selectedBreakdownProvider === quote.provider_name ? 'active' : ''}`}
                      >
                        <HelpCircle size={12} />
                        <span>{t('transfers.inspectMathButton')}</span>
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            /* Table View */
            <div className="fintech-card" style={{ padding: '0', overflow: 'hidden' }}>
              <div className="data-table-wrapper" style={{ border: 'none', borderRadius: '0' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>{t('transfers.tableThProvider')}</th>
                      <th>{t('transfers.tableThRate')}</th>
                      <th>{t('transfers.tableThUpfront')}</th>
                      <th>{t('transfers.tableThFxMargin')}</th>
                      <th>{t('transfers.tableThTotalCost')}</th>
                      <th>{t('transfers.tableThReceives')}</th>
                      <th>{t('transfers.tableThSpeed')}</th>
                      <th>{t('transfers.tableThProvenance')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparison.quotes.map((quote: DetailedTransferQuote) => {
                      const isRecommendedCheapest = quote.provider_name === comparison.recommended_cheapest
                      const isRecommendedFastest = quote.provider_name === comparison.recommended_fastest && !isRecommendedCheapest

                      return (
                        <tr
                          key={quote.provider_name}
                          style={{
                            backgroundColor: isRecommendedCheapest ? 'rgba(16, 185, 129, 0.05)' : undefined,
                            cursor: 'pointer',
                          }}
                          onClick={() => setSelectedBreakdownProvider(quote.provider_name)}
                        >
                          <td>
                            <div style={{ fontWeight: 600, color: '#fff' }}>{quote.provider_name}</div>
                            <div style={{ fontSize: '11px', color: '#94a3b8' }}>{quote.provider_type.replace(/_/g, ' ')}</div>
                            {isRecommendedCheapest && (
                              <span className="badge-best-inline">{t('transfers.bestChoiceRibbon')}</span>
                            )}
                            {isRecommendedFastest && (
                              <span className="badge-fastest-inline">{t('transfers.fastestRibbon')}</span>
                            )}
                          </td>
                          <td style={{ fontFamily: 'var(--font-mono)' }}>{quote.offered_exchange_rate}</td>
                          <td style={{ fontFamily: 'var(--font-mono)' }}>
                            {formatCurrency(quote.upfront_transfer_fee, comparison.send_currency, { locale })}
                          </td>
                          <td style={{ fontFamily: 'var(--font-mono)' }}>
                            {formatPercent(quote.fx_markup_percentage)} ({formatCurrency(quote.fx_markup_amount, comparison.send_currency, { locale })})
                          </td>
                          <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#fb7185' }}>
                            {formatCurrency(quote.total_fee_cost, comparison.send_currency, { locale })}
                          </td>
                          <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#38bdf8', fontSize: '14.5px' }}>
                            {formatCurrency(quote.recipient_amount_receive_currency, comparison.receive_currency, { locale })}
                          </td>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}>
                              <Clock size={12} color="#14b8a6" />
                              <span>{quote.estimated_delivery_time}</span>
                            </div>
                          </td>
                          <td>
                            <span style={{ fontSize: '11px', color: '#94a3b8' }}>{quote.quote_provenance}</span>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 6. Detailed Mathematical Breakdown Drawer / Card */}
          {activeQuote && (
            <div className="fintech-card math-breakdown-card">
              <div className="card-title-row">
                <div className="card-heading">
                  <CheckCircle2 size={18} color="#14b8a6" />
                  <span>{t('transfers.mathHeading', { provider: activeQuote.provider_name })}</span>
                </div>
                <div style={{ display: 'flex', gap: '6px' }}>
                  {comparison.quotes.map((q) => (
                    <button
                      key={q.provider_name}
                      type="button"
                      onClick={() => setSelectedBreakdownProvider(q.provider_name)}
                      className={`btn-provider-tab ${selectedBreakdownProvider === q.provider_name ? 'active' : ''}`}
                    >
                      {q.provider_name.split('/')[0].trim()}
                    </button>
                  ))}
                </div>
              </div>

              <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                {t('transfers.mathSubtext')}
              </p>

              <div className="math-steps-grid">
                {/* Step 1: Gross Amount Sent */}
                <div className="math-step-box">
                  <div className="step-num">Step 1</div>
                  <div className="step-title">{t('transfers.mathStep1Title')}</div>
                  <div className="step-val">
                    {formatCurrency(comparison.send_amount, comparison.send_currency, { locale })}
                  </div>
                  <div className="step-note">{t('transfers.mathStep1Note')}</div>
                </div>

                <div className="math-operator">−</div>

                {/* Step 2: Upfront Wire & Intermediary Fees */}
                <div className="math-step-box">
                  <div className="step-num">Step 2</div>
                  <div className="step-title">{t('transfers.mathStep2Title')}</div>
                  <div className="step-val negative">
                    -{formatCurrency(Number(activeQuote.upfront_transfer_fee) + Number(activeQuote.other_disclosed_fees), comparison.send_currency, { locale })}
                  </div>
                  <div className="step-note">{t('transfers.mathStep2Note')}</div>
                </div>

                <div className="math-operator">=</div>

                {/* Step 3: Convertible Principal */}
                <div className="math-step-box">
                  <div className="step-num">Step 3</div>
                  <div className="step-title">{t('transfers.mathStep3Title')}</div>
                  <div className="step-val" style={{ color: '#38bdf8' }}>
                    {formatCurrency(Number(comparison.send_amount) - Number(activeQuote.upfront_transfer_fee) - Number(activeQuote.other_disclosed_fees), comparison.send_currency, { locale })}
                  </div>
                  <div className="step-note">{t('transfers.mathStep3Note')}</div>
                </div>

                <div className="math-operator">×</div>

                {/* Step 4: Applied Rate after FX Margin */}
                <div className="math-step-box">
                  <div className="step-num">Step 4</div>
                  <div className="step-title">{t('transfers.mathStep4Title')}</div>
                  <div className="step-val" style={{ color: '#fbbf24' }}>
                    {activeQuote.offered_exchange_rate}
                  </div>
                  <div className="step-note">
                    {t('transfers.mathStep4Note')}
                  </div>
                </div>

                <div className="math-operator">=</div>

                {/* Step 5: Net Recipient Receives */}
                <div className="math-step-box highlight-total">
                  <div className="step-num">Final Result</div>
                  <div className="step-title">{t('transfers.mathStep5Title')}</div>
                  <div className="step-val" style={{ color: '#34d399', fontSize: '18px' }}>
                    {formatCurrency(activeQuote.recipient_amount_receive_currency, comparison.receive_currency, { locale })}
                  </div>
                  <div className="step-note">{t('transfers.mathStep5Note')}</div>
                </div>
              </div>
            </div>
          )}

          {/* 8. Educational Advisory Section */}
          <div className="fintech-card education-card">
            <div className="card-title-row">
              <div className="card-heading">
                <Info size={18} color="#38bdf8" />
                <span>{t('transfers.eduTitle')}</span>
              </div>
            </div>

            <div className="education-columns-grid">
              <div className="education-column">
                <h4 className="edu-col-title">{t('transfers.eduCol1Title')}</h4>
                <p className="edu-col-desc">{t('transfers.eduCol1Desc')}</p>
              </div>

              <div className="education-column">
                <h4 className="edu-col-title">{t('transfers.eduCol2Title')}</h4>
                <p className="edu-col-desc">{t('transfers.eduCol2Desc')}</p>
              </div>

              <div className="education-column">
                <h4 className="edu-col-title">{t('transfers.eduCol3Title')}</h4>
                <p className="edu-col-desc">{t('transfers.eduCol3Desc')}</p>
              </div>
            </div>
          </div>

          {/* Legal Compliance Notice */}
          <div className="disclaimer-callout">
            <ShieldCheck size={16} color="#14b8a6" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong>Compliance Notice:</strong> {t('transfers.complianceNotice')}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
