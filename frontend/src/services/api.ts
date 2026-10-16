import type {
  HealthStatus,
  FullStudentScenario,
  FinanceOverviewResponse,
  CashFlowForecastResponse,
  FundingGapResponse,
  TransferCompareResponse,
  RecommendationsResponse,
  SupportedCurrency,
  CopilotChatResponse,
} from '../types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = API_BASE ? `${API_BASE}${endpoint}` : endpoint
  const headers = {
    Accept: 'application/json',
    ...(options?.body ? { 'Content-Type': 'application/json' } : {}),
    ...options?.headers,
  }

  const response = await fetch(url, { ...options, headers })

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`
    try {
      const errJson = await response.json()
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail)
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail)
  }

  return response.json()
}

export async function checkBackendHealth(): Promise<{ data: HealthStatus; latencyMs: number }> {
  const start = performance.now()
  const data = await request<HealthStatus>('/api/health')
  const latencyMs = Math.round(performance.now() - start)
  return { data, latencyMs }
}

export async function fetchDemoScenario(): Promise<FullStudentScenario> {
  return request<FullStudentScenario>('/api/v1/demo/scenario')
}

export async function resetDemoScenario(scenario: string = 'china'): Promise<{ status: string; message: string; scenario: FullStudentScenario }> {
  return request<{ status: string; message: string; scenario: FullStudentScenario }>('/api/v1/demo/reset', {
    method: 'POST',
    body: JSON.stringify({ scenario }),
  })
}

export async function fetchFinanceOverview(): Promise<FinanceOverviewResponse> {
  return request<FinanceOverviewResponse>('/api/v1/finance/overview')
}

export async function fetchCashFlowForecast(horizonDays: number = 90): Promise<CashFlowForecastResponse> {
  return request<CashFlowForecastResponse>('/api/v1/finance/forecast', {
    method: 'POST',
    body: JSON.stringify({ forecast_days: horizonDays }),
  })
}

export async function fetchFundingGap(horizonDays: number = 90): Promise<FundingGapResponse> {
  return request<FundingGapResponse>('/api/v1/finance/funding-gap', {
    method: 'POST',
    body: JSON.stringify({ horizon_days: horizonDays }),
  })
}

export async function fetchTransferComparison(
  sendAmount: number,
  sendCurrency: SupportedCurrency,
  receiveCurrency: SupportedCurrency
): Promise<TransferCompareResponse> {
  return request<TransferCompareResponse>('/api/v1/transfers/compare', {
    method: 'POST',
    body: JSON.stringify({
      send_amount: sendAmount,
      send_currency: sendCurrency,
      receive_currency: receiveCurrency,
    }),
  })
}

export async function fetchRecommendations(): Promise<RecommendationsResponse> {
  return request<RecommendationsResponse>('/api/v1/recommendations')
}

export async function sendCopilotChat(
  message: string,
  simulateDelayedIncomeDays?: number
): Promise<CopilotChatResponse> {
  return request<CopilotChatResponse>('/api/v1/assistant/chat', {
    method: 'POST',
    body: JSON.stringify({
      message,
      simulate_delayed_income_days: simulateDelayedIncomeDays,
    }),
  })
}

