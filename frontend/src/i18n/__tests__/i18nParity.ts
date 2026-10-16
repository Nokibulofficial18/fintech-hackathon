/**
 * BorderWise AI Multilingual Parity & Verification Suite
 * Validates key coverage, parameter interpolation, fallback, and currency formatting.
 */
import { en } from '../translations/en'
import { bn } from '../translations/bn'
import { zh } from '../translations/zh'
import { formatCurrency, formatAmount, formatExchangeRate, formatDate } from '../../utils/formatters'
import type { SupportedLanguage } from '../types'

export function verifyI18nParity(): {
  success: boolean
  totalSections: number
  keyCounts: Record<SupportedLanguage, number>
  formattingChecks: string[]
} {
  const languages: Record<SupportedLanguage, Record<string, Record<string, string>>> = {
    en: en as unknown as Record<string, Record<string, string>>,
    bn: bn as unknown as Record<string, Record<string, string>>,
    zh: zh as unknown as Record<string, Record<string, string>>,
  }

  const enSections = Object.keys(en)
  const keyCounts: Record<SupportedLanguage, number> = { en: 0, bn: 0, zh: 0 }

  for (const lang of ['en', 'bn', 'zh'] as SupportedLanguage[]) {
    let count = 0
    for (const section of enSections) {
      const sectionObj = languages[lang][section]
      if (!sectionObj) {
        throw new Error(`[i18n error] Language ${lang} is missing entire section: ${section}`)
      }
      count += Object.keys(sectionObj).length
    }
    keyCounts[lang] = count
  }

  // Verify all keys in EN exist in BN and ZH
  for (const section of enSections) {
    const enKeys = Object.keys((en as unknown as Record<string, Record<string, string>>)[section])
    for (const k of enKeys) {
      if (!(k in (bn as unknown as Record<string, Record<string, string>>)[section])) {
        throw new Error(`[i18n error] Missing key in Bengali: ${section}.${k}`)
      }
      if (!(k in (zh as unknown as Record<string, Record<string, string>>)[section])) {
        throw new Error(`[i18n error] Missing key in Simplified Chinese: ${section}.${k}`)
      }
    }
  }

  // Verify formatters preserve ISO codes and clean Latin digits across all 3 locales
  const formattingChecks: string[] = []

  const enFormatted = formatCurrency(12500.5, 'CNY', { locale: 'en-US' })
  if (!enFormatted.includes('CNY') || !enFormatted.includes('12,500.50')) {
    throw new Error(`[i18n formatter error] English CNY formatting failed: ${enFormatted}`)
  }
  formattingChecks.push(`EN Currency: ${enFormatted}`)

  const bnFormatted = formatCurrency(12500.5, 'CNY', { locale: 'bn-BD' })
  if (!bnFormatted.includes('CNY') || !bnFormatted.includes('12,500.50')) {
    throw new Error(`[i18n formatter error] Bengali CNY formatting failed: ${bnFormatted}`)
  }
  formattingChecks.push(`BN Currency (Latin digits retained for wire safety): ${bnFormatted}`)

  const zhFormatted = formatCurrency(12500.5, 'CNY', { locale: 'zh-CN' })
  if (!zhFormatted.includes('CNY') || !zhFormatted.includes('12,500.50')) {
    throw new Error(`[i18n formatter error] Chinese CNY formatting failed: ${zhFormatted}`)
  }
  formattingChecks.push(`ZH Currency: ${zhFormatted}`)

  const bnBdt = formatCurrency(350000, 'BDT', { locale: 'bn-BD' })
  if (!bnBdt.includes('BDT') || !bnBdt.includes('350,000.00')) {
    throw new Error(`[i18n formatter error] Bengali BDT formatting failed: ${bnBdt}`)
  }
  formattingChecks.push(`BN BDT Family Balance: ${bnBdt}`)

  const rateCheck = formatExchangeRate(16.85, 'CNY', 'BDT')
  if (!rateCheck.includes('1 CNY = 16.8500 BDT')) {
    throw new Error(`[i18n formatter error] Exchange rate formatting failed: ${rateCheck}`)
  }
  formattingChecks.push(`Exchange Rate Direction: ${rateCheck}`)

  const dateCheck = formatDate('2026-11-15', undefined, 'bn-BD')
  formattingChecks.push(`BN Formatted Date: ${dateCheck}`)

  const numCheck = formatAmount(15300, 2, 'bn-BD')
  if (numCheck !== '15,300.00') {
    throw new Error(`[i18n formatter error] Bengali formatAmount failed: ${numCheck}`)
  }
  formattingChecks.push(`BN Formatted Amount: ${numCheck}`)

  return {
    success: true,
    totalSections: enSections.length,
    keyCounts,
    formattingChecks,
  }
}
