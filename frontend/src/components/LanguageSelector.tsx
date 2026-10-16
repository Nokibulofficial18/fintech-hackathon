import { useState, useRef, useEffect } from 'react'
import { Globe, Check, ChevronDown } from 'lucide-react'
import { useTranslation } from '../i18n/useTranslation'
import type { SupportedLanguage } from '../i18n/types'

export function LanguageSelector() {
  const { language, setLanguage, supportedLanguages, t } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement | null>(null)

  const currentLang = supportedLanguages.find((l) => l.code === language) || supportedLanguages[0]

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown)
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleSelect = (code: SupportedLanguage) => {
    setLanguage(code)
    setIsOpen(false)
  }

  return (
    <div className="language-selector-container" ref={containerRef} style={{ position: 'relative' }}>
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="btn-language-trigger"
        aria-label={t('common.selectLanguage')}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <Globe size={14} className="globe-icon" />
        <span className="lang-flag">{currentLang.flag}</span>
        <span className="lang-name-text">{currentLang.nativeName}</span>
        <ChevronDown size={12} className={`lang-chevron ${isOpen ? 'open' : ''}`} />
      </button>

      {isOpen && (
        <div
          className="language-dropdown-menu"
          role="listbox"
          aria-label={t('common.selectLanguage')}
        >
          <div className="language-menu-header">
            <span>{t('common.language')}</span>
          </div>
          {supportedLanguages.map((lang) => {
            const isSelected = lang.code === language
            return (
              <button
                key={lang.code}
                type="button"
                role="option"
                aria-selected={isSelected}
                onClick={() => handleSelect(lang.code)}
                className={`language-menu-item ${isSelected ? 'selected' : ''}`}
              >
                <span className="lang-item-flag">{lang.flag}</span>
                <div className="lang-item-labels">
                  <span className="lang-item-native">{lang.nativeName}</span>
                  <span className="lang-item-en">{lang.label}</span>
                </div>
                {isSelected && <Check size={14} className="lang-item-check" />}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
