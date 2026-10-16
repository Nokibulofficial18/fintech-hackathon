export type SupportedLanguage = 'en' | 'bn' | 'zh'

export interface LanguageMeta {
  code: SupportedLanguage
  label: string
  nativeName: string
  flag: string
  locale: string
}

export const SUPPORTED_LANGUAGES: LanguageMeta[] = [
  {
    code: 'en',
    label: 'English',
    nativeName: 'English',
    flag: '🇬🇧',
    locale: 'en-US',
  },
  {
    code: 'bn',
    label: 'Bengali',
    nativeName: 'বাংলা',
    flag: '🇧🇩',
    locale: 'bn-BD',
  },
  {
    code: 'zh',
    label: 'Chinese',
    nativeName: '简体中文',
    flag: '🇨🇳',
    locale: 'zh-CN',
  },
]
