import type { SupportedCurrency } from '../types/api'

export interface CurrencyFormatOptions {
  /** If true (default), appends the currency code like 'CNY' or 'BDT' */
  showCode?: boolean
  /** If true (default), prepends the currency symbol like '¥' or '৳' */
  showSymbol?: boolean
  /** If true, appends '(RMB)' when currency is CNY */
  showFullLabel?: boolean
  /** Explicit number of decimal places (default is 2, or 0 if whole number request) */
  decimals?: number
  /** Minimum decimal places (default is decimals or 2) */
  minDecimals?: number
  /** Maximum decimal places (default is decimals or 2) */
  maxDecimals?: number
  /** If true, shows sign prefix '+ ' or '- ' for positive/negative numbers */
  showExplicitSign?: boolean
  /** Optional locale override (default 'en-US') */
  locale?: string
}

const CURRENCY_CONFIG: Record<
  string,
  { symbol: string; code: string; fullLabel: string; name: string }
> = {
  CNY: { symbol: '¥', code: 'CNY', fullLabel: 'CNY (RMB)', name: 'Chinese Yuan' },
  BDT: { symbol: '৳', code: 'BDT', fullLabel: 'BDT', name: 'Bangladeshi Taka' },
  USD: { symbol: '$', code: 'USD', fullLabel: 'USD', name: 'US Dollar' },
  GBP: { symbol: '£', code: 'GBP', fullLabel: 'GBP', name: 'British Pound' },
  EUR: { symbol: '€', code: 'EUR', fullLabel: 'EUR', name: 'Euro' },
  INR: { symbol: '₹', code: 'INR', fullLabel: 'INR', name: 'Indian Rupee' },
  CAD: { symbol: 'CA$', code: 'CAD', fullLabel: 'CAD', name: 'Canadian Dollar' },
  AUD: { symbol: 'A$', code: 'AUD', fullLabel: 'AUD', name: 'Australian Dollar' },
  SGD: { symbol: 'S$', code: 'SGD', fullLabel: 'SGD', name: 'Singapore Dollar' },
}

/**
 * Standardized currency formatter using Intl.NumberFormat.
 * Guarantees consistent currency symbols, decimal places, and unambiguous ISO currency codes.
 */
export function formatCurrency(
  amount: number | string | null | undefined,
  currency: SupportedCurrency | string = 'CNY',
  options: CurrencyFormatOptions = {}
): string {
  const {
    showCode = true,
    showSymbol = true,
    showFullLabel = false,
    decimals = 2,
    minDecimals,
    maxDecimals,
    showExplicitSign = false,
    locale = 'en-US',
  } = options

  const num = typeof amount === 'number' ? amount : parseFloat(String(amount ?? 0))
  if (isNaN(num)) {
    return '—'
  }

  const isNegative = num < 0
  const absNum = Math.abs(num)

  const minimumFractionDigits = minDecimals ?? decimals
  const maximumFractionDigits = maxDecimals ?? decimals

  // For Bengali locale, use Latin numerals in financial contexts to prevent ambiguity in wire transfers
  const effectiveLocale = locale.startsWith('bn') ? 'bn-BD-u-nu-latn' : locale

  const formattedNum = new Intl.NumberFormat(effectiveLocale, {
    minimumFractionDigits,
    maximumFractionDigits,
  }).format(absNum)

  const conf = CURRENCY_CONFIG[currency] || {
    symbol: '',
    code: currency,
    fullLabel: currency,
    name: currency,
  }

  const symbolPart = showSymbol && conf.symbol ? conf.symbol : ''
  const codePart = showCode ? ` ${showFullLabel ? conf.fullLabel : conf.code}` : ''

  let signPart = ''
  if (isNegative) {
    signPart = '-'
  } else if (showExplicitSign && num > 0) {
    signPart = '+'
  }

  return `${signPart}${symbolPart}${formattedNum}${codePart}`
}

/**
 * Formats a plain numerical amount using Intl.NumberFormat without currency symbol.
 */
export function formatAmount(
  amount: number | string | null | undefined,
  decimals = 2,
  locale = 'en-US'
): string {
  const num = typeof amount === 'number' ? amount : parseFloat(String(amount ?? 0))
  if (isNaN(num)) {
    return '0.00'
  }

  const effectiveLocale = locale.startsWith('bn') ? 'bn-BD-u-nu-latn' : locale

  return new Intl.NumberFormat(effectiveLocale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num)
}

/**
 * Formats an exchange rate explicitly showing direction: e.g. 1 CNY = 16.8500 BDT
 */
export function formatExchangeRate(
  rate: number | string | null | undefined,
  fromCurr = 'CNY',
  toCurr = 'BDT',
  decimals = 4,
  locale = 'en-US'
): string {
  const num = typeof rate === 'number' ? rate : parseFloat(String(rate ?? 0))
  if (isNaN(num)) {
    return `1 ${fromCurr} = — ${toCurr}`
  }

  const effectiveLocale = locale.startsWith('bn') ? 'bn-BD-u-nu-latn' : locale

  const formattedRate = new Intl.NumberFormat(effectiveLocale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num)

  return `1 ${fromCurr} = ${formattedRate} ${toCurr}`
}

/**
 * Formats percentage with standard decimals (e.g. 2.60%)
 */
export function formatPercent(
  pct: number | string | null | undefined,
  decimals = 2
): string {
  const num = typeof pct === 'number' ? pct : parseFloat(String(pct ?? 0))
  if (isNaN(num)) {
    return '0.00%'
  }

  return `${num.toFixed(decimals)}%`
}

/**
 * Formats an ISO date string (e.g. "2026-11-15") into human-readable date.
 */
export function formatDate(
  dateStr: string | null | undefined,
  options?: Intl.DateTimeFormatOptions,
  locale = 'en-US'
): string {
  if (!dateStr) return '—'

  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr

    const defaultOptions: Intl.DateTimeFormatOptions = {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      ...options,
    }

    return new Intl.DateTimeFormat(locale, defaultOptions).format(d)
  } catch {
    return dateStr
  }
}

/**
 * Returns the currency symbol (e.g. '¥' for CNY, '৳' for BDT).
 */
export function getCurrencySymbol(currency: string): string {
  return CURRENCY_CONFIG[currency]?.symbol || ''
}

/**
 * Returns the human-readable currency label (e.g. 'CNY (RMB)' for CNY).
 */
export function getCurrencyLabel(currency: string): string {
  return CURRENCY_CONFIG[currency]?.fullLabel || currency
}
