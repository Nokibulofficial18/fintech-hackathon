import React, { useState, useEffect, useMemo, useCallback } from 'react'
import type { SupportedLanguage } from './types'
import { SUPPORTED_LANGUAGES } from './types'
import { en } from './translations/en'
import { bn } from './translations/bn'
import { zh } from './translations/zh'
import { I18nContext } from './context'

const TRANSLATIONS = {
  en,
  bn,
  zh,
}

const STORAGE_KEY = 'borderwise_lang'

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<SupportedLanguage>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved === 'en' || saved === 'bn' || saved === 'zh') {
        return saved
      }
    } catch {
      // ignore localStorage error
    }
    return 'en'
  })

  const setLanguage = useCallback((lang: SupportedLanguage) => {
    setLanguageState(lang)
    try {
      localStorage.setItem(STORAGE_KEY, lang)
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    document.documentElement.lang = language
  }, [language])

  const currentMeta = useMemo(() => {
    return SUPPORTED_LANGUAGES.find((l) => l.code === language) || SUPPORTED_LANGUAGES[0]
  }, [language])

  const t = useCallback(
    (keyPath: string, params?: Record<string, string | number>): string => {
      const keys = keyPath.split('.')
      
      // Look up in active language first
      let val: unknown = TRANSLATIONS[language]
      for (const k of keys) {
        if (val && typeof val === 'object' && k in val) {
          val = (val as Record<string, unknown>)[k]
        } else {
          val = undefined
          break
        }
      }

      // Fallback to English if missing or not a string
      if (typeof val !== 'string') {
        let fallbackVal: unknown = TRANSLATIONS.en
        for (const k of keys) {
          if (fallbackVal && typeof fallbackVal === 'object' && k in fallbackVal) {
            fallbackVal = (fallbackVal as Record<string, unknown>)[k]
          } else {
            fallbackVal = undefined
            break
          }
        }
        val = fallbackVal
      }

      if (typeof val !== 'string') {
        return keyPath
      }

      // Parameter replacement {paramName}
      let result = val
      if (params) {
        for (const [pKey, pVal] of Object.entries(params)) {
          result = result.replace(new RegExp(`\\{${pKey}\\}`, 'g'), String(pVal))
        }
      }
      return result
    },
    [language]
  )

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      t,
      locale: currentMeta.locale,
      supportedLanguages: SUPPORTED_LANGUAGES,
    }),
    [language, setLanguage, t, currentMeta.locale]
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}
