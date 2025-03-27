import { useTranslation } from 'react-i18next';
import { useAppDispatch } from '../redux/hooks';
import { setLanguage } from '../redux/features/languageSlice';
import '../styles/LanguageSwitcher.css';

const LanguageSwitcher = () => {
  const { i18n } = useTranslation();
  const dispatch = useAppDispatch();

  const handleLanguageChange = (language: string) => {
    dispatch(setLanguage(language));
    i18n.changeLanguage(language);
  };

  return (
    <div className="language-switcher">
      <button
        className={`language-btn ${i18n.language === 'kz' ? 'active' : ''}`}
        onClick={() => handleLanguageChange('kz')}
      >
        KZ
      </button>
      <button
        className={`language-btn ${i18n.language === 'ru' ? 'active' : ''}`}
        onClick={() => handleLanguageChange('ru')}
      >
        RU
      </button>
    </div>
  );
};

export default LanguageSwitcher;