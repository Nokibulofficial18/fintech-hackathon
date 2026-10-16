export type SupportedCurrency = 'CNY' | 'BDT' | 'USD' | 'EUR' | 'GBP' | 'INR' | 'CAD' | 'AUD' | 'SGD'
export type QuoteProvenance = 'SIMULATED' | 'PROVIDER_PUBLISHED' | 'LIVE_API'
export type RecommendationPriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
export type RecommendationUrgency = 'IMMEDIATE' | 'UPCOMING' | 'PLANNING' | 'INFORMATIONAL'
export type RecommendationCategory =
  | 'TUITION_PRESERVATION'
  | 'FUNDING_GAP_ALERT'
  | 'TRANSFER_OPTIMIZATION'
  | 'EXPENSE_DISCIPLINE'
  | 'LIQUIDITY_BUFFER'

export interface HealthStatus {
  status: string
  app_name: string
  version: string
  environment: string
  timestamp_utc: string
  database: string
  ai_mode: string
}

export interface DatedFXQuote {
  base_currency: SupportedCurrency
  quote_currency: SupportedCurrency
  rate: number | string
  timestamp_utc: string
  source: string
  provenance: QuoteProvenance
  is_stale: boolean
  staleness_warning?: string | null
}

export interface AccountBalance {
  account_name: string
  currency: SupportedCurrency
  actual_balance: number | string
  as_of_date: string
  is_projected: boolean
}

export interface ExpectedIncome {
  source_name: string
  amount: number | string
  currency: SupportedCurrency
  expected_date: string
  is_recurring: boolean
  recurrence_interval_days?: number | null
  notes?: string | null
}

export interface LivingExpenseItem {
  category: string
  monthly_amount: number | string
  currency: SupportedCurrency
  due_day_of_month: number
  is_fixed: boolean
}

export interface TuitionObligation {
  term: string
  amount_due: number | string
  currency: SupportedCurrency
  due_date: string
  grace_period_days: number
  late_penalty_fee: number | string
}

export interface PlannedRemittance {
  plan_name: string
  planned_date: string
  send_amount: number | string
  send_currency: SupportedCurrency
  target_currency: SupportedCurrency
  estimated_received_amount?: number | string | null
  notes?: string | null
}

export interface StudentProfileData {
  student_id: string
  full_name: string
  home_country: string
  study_country: string
  home_currency: SupportedCurrency
  study_currency: SupportedCurrency
  university_name: string
  program_name: string
  intake_term: string
}

export interface FullStudentScenario {
  profile: StudentProfileData
  available_balances: AccountBalance[]
  expected_income: ExpectedIncome[]
  monthly_living_expenses: LivingExpenseItem[]
  tuition_obligations: TuitionObligation[]
  planned_remittances: PlannedRemittance[]
  is_synthetic_demo: boolean
}

export interface FinanceOverviewResponse {
  student_id: string
  student_name: string
  home_currency: SupportedCurrency
  study_currency: SupportedCurrency
  as_of_date: string
  balances_by_currency: Record<string, number | string>
  tuition_amount_due: number | string
  tuition_due_date: string
  days_until_tuition_due: number
  obligations_next_30_days_study_currency: number | string
  obligations_next_90_days_study_currency: number | string
  monthly_living_burn_study_currency: number | string
  study_currency_standalone_runway_months: number | string
  has_imminent_shortfall: boolean
  has_funding_gap: boolean
  summary_alert: string
}

export interface TimelineEvent {
  event_id: string
  event_date: string
  event_type: string
  description: string
  currency: SupportedCurrency
  amount: number | string
  is_projected: boolean
}

export interface DailyCurrencyBalance {
  date: string
  currency: SupportedCurrency
  starting_balance: number | string
  total_inflow: number | string
  total_outflow: number | string
  ending_balance: number | string
  is_projected: boolean
  is_shortfall: boolean
  shortfall_amount: number | string
}

export interface ShortfallEvent {
  shortfall_id: string
  shortfall_date: string
  currency: SupportedCurrency
  projected_balance: number | string
  shortfall_amount: number | string
  trigger_event: string
  days_from_start: number
  urgency: string
}

export interface DataCompletenessReport {
  completeness_score: number
  has_verified_actual_balances: boolean
  has_scheduled_income: boolean
  has_itemized_living_expenses: boolean
  has_tuition_deadline: boolean
  has_planned_remittances: boolean
  missing_elements: string[]
  notes: string
}

export interface CashFlowForecastResponse {
  forecast_start_date: string
  forecast_end_date: string
  horizon_days: number
  actual_balances_as_of: string
  initial_actual_balances: Record<string, number | string>
  projected_end_balances: Record<string, number | string>
  total_inflows_by_currency: Record<string, number | string>
  total_outflows_by_currency: Record<string, number | string>
  timeline_events: TimelineEvent[]
  daily_summaries: DailyCurrencyBalance[]
  shortfalls: ShortfallEvent[]
  assumptions: string[]
  data_completeness: DataCompletenessReport
}

export interface SingleCurrencyPosition {
  currency: SupportedCurrency
  actual_liquid_balance: number | string
  expected_inflows: number | string
  total_available_resources: number | string
  total_obligations: number | string
  net_position: number | string
  has_direct_gap: boolean
  direct_gap_amount: number | string
}

export interface CurrencyObligationItem {
  title: string
  category: string
  due_date: string
  currency: SupportedCurrency
  amount: number | string
  is_mandatory: boolean
}

export interface CrossCurrencyConversionOption {
  source_currency: SupportedCurrency
  target_currency: SupportedCurrency
  available_surplus_in_source: number | string
  dated_fx_quote: DatedFXQuote
  estimated_provider_fee: number | string
  net_convertible_in_target: number | string
  can_cover_full_gap: boolean
  remaining_gap_after_conversion: number | string
  conversion_caveats: string[]
}

export interface FundingGapResponse {
  analysis_date: string
  horizon_days: number
  study_currency: SupportedCurrency
  home_currency: SupportedCurrency
  currency_positions: Record<string, SingleCurrencyPosition>
  obligations: CurrencyObligationItem[]
  target_currency_has_shortfall: boolean
  target_currency_shortfall_amount: number | string
  cross_currency_remedy?: CrossCurrencyConversionOption | null
  has_stale_rate_warning: boolean
  rate_warnings: string[]
  summary_status: 'CRITICAL_DEFICIT' | 'COVERABLE_VIA_TRANSFER' | 'FULLY_FUNDED'
  audit_notes: string[]
}

export interface DetailedTransferQuote {
  provider_name: string
  provider_type: 'TRADITIONAL_BANK' | 'DIGITAL_SPECIALIST' | 'CAMPUS_PARTNER' | 'P2P_FINTECH'
  quote_provenance: QuoteProvenance
  quote_timestamp_utc: string
  offered_exchange_rate: number | string
  mid_market_reference_rate: number | string
  fx_markup_percentage: number | string
  fx_markup_amount: number | string
  upfront_transfer_fee: number | string
  other_disclosed_fees: number | string
  total_fee_cost: number | string
  amount_debited_send_currency: number | string
  recipient_amount_receive_currency: number | string
  estimated_delivery_time: string
  delivery_hours_estimate: number
  payment_methods_supported: string[]
  quote_notes: string
}

export interface TransferCompareResponse {
  send_amount: number | string
  send_currency: SupportedCurrency
  receive_currency: SupportedCurrency
  mid_market_rate: number | string
  quotes_timestamp_utc: string
  all_quotes_provenance: QuoteProvenance
  quotes: DetailedTransferQuote[]
  recommended_cheapest: string
  recommended_fastest: string
  potential_savings_vs_bank: number | string
  disclaimer: string
}

export interface ActionableRecommendation {
  id: string
  priority: RecommendationPriority
  urgency: RecommendationUrgency
  category: RecommendationCategory
  title: string
  reason: string
  supporting_numbers: Record<string, unknown>
  assumptions: string[]
  uncertainty: string
  suggested_action: string
}

export interface RecommendationsResponse {
  generated_at_utc: string
  total_recommendations: number
  critical_count: number
  high_count: number
  recommendations: ActionableRecommendation[]
  compliance_disclaimer: string
}

export interface ToolExecutionResult {
  tool_name: string
  arguments: Record<string, unknown>
  output: Record<string, unknown>
  timestamp_utc: string
  execution_status: string
}

export interface CopilotChatResponse {
  message: string
  tool_results: ToolExecutionResult[]
  recommendations: ActionableRecommendation[]
  assumptions: string[]
  warnings: string[]
  data_timestamps: Record<string, string>
  is_demo_mode: boolean
  requires_confirmation: boolean
  confirmation_preview?: Record<string, unknown> | null
}

export interface ChatMessage {
  id: string
  sender: 'user' | 'assistant'
  timestamp: string
  text: string
  recommendationLink?: ActionableRecommendation
  calculationEvidence?: Record<string, string | number>
  toolResults?: ToolExecutionResult[]
  assumptions?: string[]
  warnings?: string[]
  confirmationPreview?: Record<string, unknown> | null
  isDemoMode?: boolean
}
