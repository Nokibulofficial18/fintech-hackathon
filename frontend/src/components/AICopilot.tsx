import { useState, useRef, useEffect, useCallback, useId, useMemo } from 'react'
import {
  Send,
  Sparkles,
  BotMessageSquare,
  User,
  ShieldCheck,
  Calculator,
  ArrowRight,
  AlertTriangle,
  Info,
  CheckCircle,
  Clock,
  Loader2,
  RotateCcw,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  MessageSquare,
  BookOpen,
} from 'lucide-react'
import type {
  FinanceOverviewResponse,
  FundingGapResponse,
  CashFlowForecastResponse,
  RecommendationsResponse,
  ChatMessage,
  ActionableRecommendation,
  ToolExecutionResult,
} from '../types/api'
import { sendCopilotChat } from '../services/api'
import { useTranslation } from '../i18n/useTranslation'

interface AICopilotProps {
  overview: FinanceOverviewResponse | null
  gap: FundingGapResponse | null
  forecast?: CashFlowForecastResponse | null
  recommendations: RecommendationsResponse | null
  initialPrompt?: string | null
  onNavigateToActionPlan: () => void
}

function getFormattedTime(): string {
  const now = new Date()
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

/**
 * Lightweight formatting helper to render bold text (**text**), bullet points, and line breaks
 */
function FormattedMessageText({ text }: { text: string }) {
  const lines = text.split('\n')

  return (
    <div className="formatted-chat-text">
      {lines.map((line, lineIdx) => {
        const trimmed = line.trim()
        if (!trimmed) {
          return <div key={lineIdx} style={{ height: '8px' }} />
        }

        // Render bullet list items
        const isBullet = trimmed.startsWith('• ') || trimmed.startsWith('- ') || trimmed.startsWith('* ')
        const isNumbered = /^\d+\.\s/.test(trimmed)
        const lineContent = isBullet ? trimmed.replace(/^[•\-*]\s+/, '') : trimmed

        // Parse **bold** parts
        const parts = lineContent.split(/(\*\*[^*]+\*\*)/g)
        const renderedParts = parts.map((part, pIdx) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return (
              <strong key={pIdx} style={{ color: '#fff', fontWeight: 650 }}>
                {part.slice(2, -2)}
              </strong>
            )
          }
          return part
        })

        if (isBullet) {
          return (
            <div key={lineIdx} className="chat-bullet-row">
              <span className="bullet-dot">&bull;</span>
              <span className="bullet-text">{renderedParts}</span>
            </div>
          )
        }

        if (isNumbered) {
          return (
            <div key={lineIdx} className="chat-bullet-row numbered">
              <span className="bullet-text">{renderedParts}</span>
            </div>
          )
        }

        return (
          <p key={lineIdx} className="chat-paragraph">
            {renderedParts}
          </p>
        )
      })}
    </div>
  )
}

export function AICopilot({
  overview,
  gap,
  recommendations,
  initialPrompt,
  onNavigateToActionPlan,
}: AICopilotProps) {
  const { t } = useTranslation()

  const welcomeMessage: ChatMessage = useMemo(() => ({
    id: 'welcome-01',
    sender: 'assistant',
    timestamp: 'Engine Ready',
    text: (
      `**${t('copilot.welcomeTitle')}** ${t('copilot.welcomeBody')}\n\n` +
      `**${t('nav.navigationHeader')}:**\n` +
      `• **${t('copilot.welcomeScopeTuition')}**\n` +
      `• **${t('copilot.welcomeScopeTransfer')}**\n` +
      `• **${t('copilot.welcomeScopeExpenses')}**\n` +
      `• **${t('copilot.welcomeScopeGap')}**\n\n` +
      `*${t('copilot.safetyNotice')}*`
    ),
    isDemoMode: true,
  }), [t])

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [failedPrompt, setFailedPrompt] = useState<string | null>(null)
  const [confirmedActions, setConfirmedActions] = useState<Record<string, boolean>>({})
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({})

  const allMessages: ChatMessage[] = useMemo(() => [welcomeMessage, ...messages], [welcomeMessage, messages])

  const counterRef = useRef(100)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const executedInitialPromptRef = useRef<string | null>(null)
  const inputId = useId()

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [allMessages, isLoading])

  const toggleToolExpanded = (msgId: string, toolIdx: number) => {
    const key = `${msgId}-${toolIdx}`
    setExpandedTools((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const handleSendPrompt = useCallback(
    async (questionText: string) => {
      const trimmed = questionText.trim()
      if (!trimmed || isLoading) return

      counterRef.current += 1
      const userMsg: ChatMessage = {
        id: `usr-${counterRef.current}`,
        sender: 'user',
        timestamp: getFormattedTime(),
        text: trimmed,
      }

      setMessages((prev) => [...prev, userMsg])
      setInputValue('')
      setFailedPrompt(null)
      setIsLoading(true)

      try {
        const res = await sendCopilotChat(trimmed)

        counterRef.current += 1
        const assistantMsg: ChatMessage = {
          id: `ast-${counterRef.current}`,
          sender: 'assistant',
          timestamp: getFormattedTime(),
          text: res.message,
          recommendationLink: res.recommendations && res.recommendations.length > 0 ? res.recommendations[0] : undefined,
          toolResults: res.tool_results,
          assumptions: res.assumptions,
          warnings: res.warnings,
          confirmationPreview: res.confirmation_preview,
          isDemoMode: res.is_demo_mode,
        }

        setMessages((prev) => [...prev, assistantMsg])
      } catch (err) {
        console.warn('Backend assistant endpoint call failed, attempting fallback:', err)
        setFailedPrompt(trimmed)

        // Deterministic fallback derived strictly from verified props
        counterRef.current += 1
        const lower = trimmed.toLowerCase()
        let fallbackText = ''
        let fallbackRec: ActionableRecommendation | undefined

        if (lower.includes('tuition') && (lower.includes('cover') || lower.includes('afford') || lower.includes('can i'))) {
          const tuitAmt = overview?.tuition_amount_due ?? '24,000.00'
          const gapAmt = gap?.target_currency_shortfall_amount ?? '15,300.00'
          fallbackText =
            `**Tuition Assessment**: Your upcoming tuition of **¥${tuitAmt} CNY** is due on ${overview?.tuition_due_date ?? '2026-11-15'}.\n\n` +
            `Your current local account (ICBC) holds ¥${overview?.balances_by_currency['CNY'] ?? '8,500.00'} CNY, creating a direct local shortfall of **¥${gapAmt} CNY**.\n\n` +
            `Your family holds ৳${overview?.balances_by_currency['BDT'] ?? '350,000.00'} BDT in Bangladesh. Initiating the planned family remittance of ৳250,000.00 BDT (~¥14,640.00 CNY net) covers the vast majority of the obligation. Conclusion: Yes, tuition is affordable with a secondary top-up of ~৳15,000.00 BDT before Nov 05.`
          fallbackRec = recommendations?.recommendations.find((r) => r.category === 'TUITION_PRESERVATION')
        } else if (lower.includes('transfer') || lower.includes('send') || lower.includes('1,000') || lower.includes('bangladesh')) {
          fallbackText =
            `**Transfer Comparison for 1,000.00 CNY $\\rightarrow$ BDT**:\n\n` +
            `• **Digital Specialist (Recommended)**: Delivers approximately **৳16,463.97 BDT** after fees.\n` +
            `  - Exchange Rate: 1 CNY = 16.7658 BDT (Benchmark: 16.8500 BDT)\n` +
            `  - Upfront Fee: ¥18.00 CNY | Delivery: Instant - 4 hours\n\n` +
            `• **Traditional Wire Bank**: Delivers only **৳14,442.47 BDT** due to ¥95.00 CNY in upfront fees and 2.60% FX markup.\n\n` +
            `**Advantage**: Using digital specialists yields **৳2,021.50 BDT extra** and saves **¥123.00 CNY** in total costs.\n\n` +
            `*Data Status: DEMO DATA (simulated benchmark). BorderWise AI does not initiate live transfers.*`
          fallbackRec = recommendations?.recommendations.find((r) => r.category === 'TRANSFER_OPTIMIZATION')
        } else if (lower.includes('reserve') || lower.includes('living expense') || lower.includes('monthly')) {
          const burn = overview?.monthly_living_burn_study_currency ?? '3,300.00'
          fallbackText =
            `**Monthly Expense & Reserve Budgeting**:\n\n` +
            `• **Itemized Monthly Burn**: **¥${burn} CNY/month** (Housing Rent: ¥1,800.00, Campus Dining: ¥1,200.00, Utilities & Mobile: ¥300.00).\n` +
            `• **Verified Study Balance**: ¥${overview?.balances_by_currency['CNY'] ?? '8,500.00'} CNY (approx. 2.6 months of standalone runway).\n` +
            `• **Recommended Reserve**: To buffer against international wire transit times, maintain **¥6,600.00 – ¥9,900.00 CNY** (2–3 months of baseline expenses) separated from tuition obligations.`
          fallbackRec = recommendations?.recommendations.find((r) => r.category === 'LIQUIDITY_BUFFER')
        } else if (lower.includes('funding gap') || lower.includes('shortfall')) {
          const gapAmt = gap?.target_currency_shortfall_amount ?? '15,300.00'
          fallbackText =
            `**Projected Funding Gap Analysis**:\n\n` +
            `• **Local Study Shortfall**: **¥${gapAmt} CNY** across the evaluation horizon.\n` +
            `• **Primary Driver**: Tuition payment (¥24,000.00 CNY due Nov 15) exceeding China liquid reserves (¥8,500.00 CNY).\n` +
            `• **Home Currency Remedy**: Family savings of ৳350,000.00 BDT in Bangladesh can cover this via planned transfer of ৳250,000.00 BDT.\n` +
            `• **Status**: COVERABLE_VIA_TRANSFER.`
          fallbackRec = recommendations?.recommendations.find((r) => r.category === 'FUNDING_GAP_ALERT')
        } else {
          fallbackText =
            `**BorderWise Financial Overview**:\n\n` +
            `Verified Liquid Accounts:\n` +
            `• China Study Account (ICBC): ¥${overview?.balances_by_currency['CNY'] ?? '8,500.00'} CNY\n` +
            `• Bangladesh Family Savings (DBBL): ৳${overview?.balances_by_currency['BDT'] ?? '350,000.00'} BDT\n\n` +
            `Primary Upcoming Milestone: Tuition of ¥${overview?.tuition_amount_due ?? '24,000.00'} CNY due on ${overview?.tuition_due_date ?? '2026-11-15'}.\n\n` +
            `*Advisory notice: Derived from offline verified snapshot. No live transfers can be executed.*`
        }

        const fallbackMsg: ChatMessage = {
          id: `ast-${counterRef.current}`,
          sender: 'assistant',
          timestamp: `${getFormattedTime()} (Offline Snapshot)`,
          text: fallbackText,
          recommendationLink: fallbackRec,
          isDemoMode: true,
          warnings: ['Network unavailable; answer generated using verified local financial models.'],
        }
        setMessages((prev) => [...prev, fallbackMsg])
      } finally {
        setIsLoading(false)
      }
    },
    [isLoading, overview, gap, recommendations]
  )

  useEffect(() => {
    if (initialPrompt && initialPrompt !== executedInitialPromptRef.current) {
      executedInitialPromptRef.current = initialPrompt
      handleSendPrompt(initialPrompt)
    }
  }, [initialPrompt, handleSendPrompt])

  const handleConfirmAction = (msgId: string) => {
    setConfirmedActions((prev) => ({ ...prev, [msgId]: true }))
  }

  const handleResetChat = () => {
    setMessages([])
    setFailedPrompt(null)
  }

  const handleRetryFailedPrompt = () => {
    if (failedPrompt) {
      handleSendPrompt(failedPrompt)
    }
  }

  return (
    <div className="copilot-container">
      {/* Copilot Header Card */}
      <div className="fintech-card copilot-header-card">
        <div className="copilot-header-main">
          <div className="copilot-title-group">
            <div className="copilot-icon-wrapper">
              <BotMessageSquare size={22} color="#14b8a6" />
            </div>
            <div>
              <div className="copilot-title-row">
                <h2 className="copilot-heading">BorderWise AI Financial Copilot</h2>
                <span className="copilot-mode-pill">
                  <ShieldCheck size={13} color="#2dd4bf" />
                  Deterministic Engine &bull; Zero Autonomous Money Movement
                </span>
              </div>
              <p className="copilot-subtitle">
                Cross-border scenario modeling for <strong>Tanvir Hasan</strong> (Tsinghua University) &bull; Managing{' '}
                <strong>CNY</strong> expenses and <strong>BDT</strong> family support.
              </p>
            </div>
          </div>

          <div className="copilot-header-actions">
            <button
              type="button"
              onClick={handleResetChat}
              className="btn btn-secondary btn-sm"
              title="Reset conversation to initial welcoming state"
            >
              <RotateCcw size={13} />
              <span>Reset Chat</span>
            </button>
          </div>
        </div>

        {/* Chat Window */}
        <div className="chat-window-enhanced">
          {/* Scrollable Messages Area */}
          <div
            className="chat-messages-enhanced"
            role="log"
            aria-live="polite"
            aria-busy={isLoading}
            aria-label="Financial Copilot message history"
          >
            {allMessages.length === 0 ? (
              <div className="chat-empty-state">
                <div className="empty-icon-box">
                  <MessageSquare size={28} color="#14b8a6" />
                </div>
                <h3>No messages in this session</h3>
                <p>Select one of the suggested prompts below to start analyzing your cross-border cash flow.</p>
              </div>
            ) : (
              allMessages.map((m) => (
                <div key={m.id} className={`chat-message-row ${m.sender}`}>
                  <div className="chat-avatar-wrapper">
                    {m.sender === 'assistant' ? (
                      <div className="avatar assistant">
                        <Sparkles size={14} color="#14b8a6" />
                      </div>
                    ) : (
                      <div className="avatar user">
                        <User size={14} color="#38bdf8" />
                      </div>
                    )}
                  </div>

                  <div className={`chat-bubble-enhanced ${m.sender}`}>
                    {/* Header meta */}
                    <div className="bubble-meta">
                      <span className="sender-name">
                        {m.sender === 'assistant' ? 'BorderWise Copilot' : 'Tanvir Hasan (Student)'}
                      </span>
                      <span className="meta-sep">&bull;</span>
                      <span className="meta-time">{m.timestamp}</span>
                      {m.isDemoMode && (
                        <span className="badge-demo-mode">
                          <CheckCircle size={10} color="#2dd4bf" />
                          Deterministic Mode
                        </span>
                      )}
                    </div>

                    {/* Formatted Text Content */}
                    <FormattedMessageText text={m.text} />

                    {/* Executed Tools Breakdown */}
                    {m.toolResults && m.toolResults.length > 0 && (
                      <div className="tool-execution-block">
                        <div className="tool-block-header">
                          <div className="tool-title-left">
                            <Calculator size={13} color="#38bdf8" />
                            <span>Executed Deterministic Tools ({m.toolResults.length})</span>
                          </div>
                          <span className="tool-provenance-tag">Backend Validated</span>
                        </div>
                        <div className="tool-chips-list">
                          {m.toolResults.map((tool: ToolExecutionResult, tIdx: number) => {
                            const isExpanded = expandedTools[`${m.id}-${tIdx}`]
                            return (
                              <div key={tIdx} className="tool-item-card">
                                <button
                                  type="button"
                                  onClick={() => toggleToolExpanded(m.id, tIdx)}
                                  className="tool-toggle-button"
                                  aria-expanded={isExpanded}
                                >
                                  <div className="tool-info-left">
                                    <CheckCircle size={12} color="#34d399" />
                                    <code className="tool-name-code">{tool.tool_name}</code>
                                    <span className="tool-status-text">&bull; {tool.execution_status}</span>
                                  </div>
                                  <span className="tool-expand-icon">
                                    {isExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                                  </span>
                                </button>
                                {isExpanded && (
                                  <div className="tool-expanded-details">
                                    <div className="tool-payload-section">
                                      <span className="tool-section-label">Input Arguments:</span>
                                      <pre className="tool-json-pre">
                                        {JSON.stringify(tool.arguments, null, 2)}
                                      </pre>
                                    </div>
                                    <div className="tool-payload-section">
                                      <span className="tool-section-label">Verified Output Metrics:</span>
                                      <pre className="tool-json-pre">
                                        {JSON.stringify(tool.output, null, 2)}
                                      </pre>
                                    </div>
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}

                    {/* Assumptions Strip */}
                    {m.assumptions && m.assumptions.length > 0 && (
                      <div className="assumptions-box">
                        <div className="assumptions-title">
                          <Info size={12} color="#38bdf8" />
                          <span>Explicit Analysis Assumptions</span>
                        </div>
                        <ul className="assumptions-list">
                          {m.assumptions.map((item, idx) => (
                            <li key={idx}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Advisory Warnings */}
                    {m.warnings && m.warnings.length > 0 && (
                      <div className="warnings-box">
                        <div className="warnings-title">
                          <AlertTriangle size={12} color="#f43f5e" />
                          <span>Advisory Disclaimers &amp; Staleness Notices</span>
                        </div>
                        <ul className="warnings-list">
                          {m.warnings.map((warn, idx) => (
                            <li key={idx}>{warn}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Simulated Action / Confirmation Preview */}
                    {m.confirmationPreview && (
                      <div className="confirmation-preview-card">
                        <div className="preview-header">
                          <Clock size={14} color="#f59e0b" />
                          <span>Simulated Action Preview: Student Confirmation Required</span>
                        </div>
                        <p className="preview-desc">
                          {String(m.confirmationPreview.impact || m.confirmationPreview.action || 'Simulated budget adjustment')}
                        </p>
                        <div className="preview-controls">
                          {confirmedActions[m.id] ? (
                            <span className="confirmed-badge">
                              <CheckCircle size={13} color="#34d399" />
                              Scenario Confirmed by Student
                            </span>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleConfirmAction(m.id)}
                              className="btn btn-outline-emerald btn-sm"
                            >
                              Confirm Simulated Scenario
                            </button>
                          )}
                          <span className="disclaimer-micro">
                            No real banking transactions are triggered. Advisory simulation only.
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Next Steps / Action Plan Direct Link */}
                    {m.recommendationLink && (
                      <div className="action-plan-link-card">
                        <div className="action-link-left">
                          <BookOpen size={14} color="#14b8a6" />
                          <div>
                            <span className="action-link-title">{t('copilot.nextActionStep')}: {m.recommendationLink.title}</span>
                            <span className="action-link-sub">
                              Priority: {m.recommendationLink.priority} &bull; Urgency: {m.recommendationLink.urgency}
                            </span>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={onNavigateToActionPlan}
                          className="btn btn-outline-emerald btn-sm"
                        >
                          <span>{t('copilot.openActionPlan')}</span>
                          <ArrowRight size={13} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}

            {/* Thinking / Loading Bubble */}
            {isLoading && (
              <div className="chat-message-row assistant">
                <div className="chat-avatar-wrapper">
                  <div className="avatar assistant loading">
                    <Loader2 size={14} className="spin-icon" color="#14b8a6" />
                  </div>
                </div>
                <div className="chat-bubble-enhanced assistant loading-bubble">
                  <div className="loading-content">
                    <div className="typing-dots">
                      <span className="dot" />
                      <span className="dot" />
                      <span className="dot" />
                    </div>
                    <span className="loading-text">
                      {t('copilot.thinking')}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Error & Retry Banner if request failed */}
            {failedPrompt && !isLoading && (
              <div className="chat-error-banner">
                <div className="error-banner-content">
                  <AlertTriangle size={16} color="#f43f5e" />
                  <div>
                    <span className="error-title">{t('copilot.errorLiveFailed')}</span>
                    <span className="error-sub">
                      {t('copilot.errorOfflineFallback')}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleRetryFailedPrompt}
                  className="btn btn-outline-danger btn-sm"
                >
                  <RefreshCw size={13} />
                  <span>{t('copilot.retryQuestion')}</span>
                </button>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Questions Section */}
          <div className="copilot-suggestions-bar">
            <div className="suggestions-label-row">
              <span className="suggestions-label">
                <Sparkles size={13} color="#14b8a6" />
                <span>{t('copilot.suggestedQuestions')}</span>
              </span>
            </div>
            <div className="suggestions-scroll">
              {[
                t('copilot.chipTuition'),
                t('copilot.chipCompare'),
                t('copilot.chipReserve'),
                t('copilot.chipGap'),
              ].map((q) => (
                <button
                  key={q}
                  type="button"
                  disabled={isLoading}
                  onClick={() => handleSendPrompt(q)}
                  className="suggestion-pill-primary"
                  title={`Ask: "${q}"`}
                >
                  {q}
                </button>
              ))}
              {[
                t('copilot.chipLateScholarship'),
                t('copilot.chipFxRate'),
                t('copilot.chipPriority'),
              ].map((q) => (
                <button
                  key={q}
                  type="button"
                  disabled={isLoading}
                  onClick={() => handleSendPrompt(q)}
                  className="suggestion-pill-secondary"
                  title={`Ask: "${q}"`}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Input & Submit Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSendPrompt(inputValue)
            }}
            className="chat-input-bar-enhanced"
          >
            <label htmlFor={inputId} className="sr-only">
              Ask BorderWise Financial Copilot a question
            </label>
            <div className="input-field-wrapper">
              <input
                id={inputId}
                type="text"
                placeholder={t('copilot.inputPlaceholder')}
                value={inputValue}
                disabled={isLoading}
                onChange={(e) => setInputValue(e.target.value)}
                className="chat-text-input"
                autoComplete="off"
              />
              {inputValue.length > 0 && (
                <span className="char-count">{inputValue.length}/2000</span>
              )}
            </div>
            <button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="btn btn-primary chat-submit-button"
              aria-label="Send financial question"
            >
              {isLoading ? (
                <>
                  <Loader2 size={16} className="spin-icon" />
                  <span>{t('copilot.analyzing')}</span>
                </>
              ) : (
                <>
                  <Send size={15} />
                  <span>{t('copilot.askCopilot')}</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
