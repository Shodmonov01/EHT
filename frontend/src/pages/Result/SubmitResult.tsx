import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import '../../styles/submit.css'
// import yellowBg from '../../assets/images/yellow-bg.png'
import { useTranslation } from 'react-i18next'

const QuizResult: React.FC = () => {
    const { t } = useTranslation()
    return (
        <motion.div
            className='quiz-result-container'
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
        >
            <div className='logo-container-result'>
                <img src='/logo.svg' alt='' />
            </div>
            <div className='title'>
                <h1>{t('quizResult.title')}</h1>
                {/* <img className='title__img' src={yellowBg} alt='Background' /> */}
            </div>
            <Link to='/' className='back-button'>
                {t('quizResult.backButton')}
            </Link>
        </motion.div>
    )
}

export default QuizResult
