import { createContext } from 'react'
import type { SupportedLanguage, LanguageMeta } from './types'

export interface I18nContextType {
  language: SupportedLanguage
  setLanguage: (lang: SupportedLanguage) => void
  t: (keyPath: string, params?: Record<string, string | number>) => string
  locale: string
  supportedLanguages: LanguageMeta[]
}

export const I18nContext = createContext<I18nContextType | null>(null)
