import { useTranslation } from 'react-i18next';
import { useAppDispatch } from '../redux/hooks';
import {useSelector} from 'react-redux';  
import { setLanguage } from '../redux/features/languageSlice';
import '../styles/LanguageSwitcher.css';
import { RootState } from '../redux/store';
import { useEffect } from 'react';

const LanguageSwitcher = () => {
  const { i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const currentLanguage = useSelector((state: RootState) => state.language.currentLanguage);

  const handleLanguageChange = (language: 'ru' | 'kz') => {
    dispatch(setLanguage(language));
    i18n.changeLanguage(language);
    localStorage.setItem('language', language);
  };

  useEffect(() => {
    const savedLanguage = localStorage.getItem('language') as 'ru' | 'kz';
    if (savedLanguage) {
      dispatch(setLanguage(savedLanguage));
      i18n.changeLanguage(savedLanguage);
    }
  }, []);

  return (
    <div className="language-switcher">
      <button
        className={`language-btn ${currentLanguage === 'kz' ? 'active' : ''}`}
        onClick={() => handleLanguageChange('kz')}
      >
        KZ
      </button>
      <button
        className={`language-btn ${currentLanguage === 'ru' ? 'active' : ''}`}
        onClick={() => handleLanguageChange('ru')}
      >
        RU
      </button>
    </div>
  );
};

export default LanguageSwitcher;