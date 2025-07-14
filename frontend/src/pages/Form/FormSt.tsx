import { motion } from 'framer-motion'
import '../../styles/Form.css'
import LanguageSwitcher from '../../components/LanguageSwitcher'
import { useTranslation } from 'react-i18next'
// import yellowBg from '../../assets/images/yellow-bg.png'
import { useQuery, useMutation } from '@tanstack/react-query'
import { startQuiz } from '../../api/request.api'
import { useEffect, useState } from 'react'
import { QuizStartRequest, QuizResult, Category } from '../../types/quizs'
import { Link, useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { setQuizData } from '../../redux/features/quizSlice'
import Select from 'react-select'
import { RootState } from '../../redux/store'
import LoadingButton from '../../components/LoadingButton'
import Loader from '../../components/Loader'
import axios from 'axios'
// import { div } from 'framer-motion/client'

export default function FormSt() {
    const { t } = useTranslation()
    const dispatch = useDispatch()
    const currentLanguage = useSelector((state: RootState) => state.language.currentLanguage)
    const [selectedCategory] = useState<number | null>(null)
    const [formData, setFormData] = useState({
        name: '',
        phone: '',
        history_kazakhstan: '',
        math_literacy: '',
        reading_literacy: '',
        profile_subject_1: {
            name: '',
            score: ''
        },
        profile_subject_2: {
            name: '',
            score: ''
        }
    })

    const [isAgreed, setIsAgreed] = useState(false)
    const token = localStorage.getItem('token')
    console.log('formData', formData)

    const navigate = useNavigate()
    console.log('selectedCategory', selectedCategory)
    console.log('currentLanguage', currentLanguage)

    const {
        data: subject,
        isError,
        isLoading,
        refetch
    } = useQuery({
        queryKey: ['subjects', currentLanguage],
        queryFn: async () => {
            const response = await fetch(`http://localhost:8000/quiz/subjects`)
            if (!response.ok) {
                throw new Error('Network response was not ok')
            }
            const data = await response.json()
            return data
        }
    })

    console.log('subject', subject)

    const { data: point } = useQuery({
        queryKey: ['points', currentLanguage, selectedCategory],
        queryFn: async () => {
            const response = await fetch(`http://localhost:8000/quiz/subjects/result/${token}/`)

            if (!response.ok) {
                throw new Error('Network response was not ok')
            }

            const data = await response.json()
            return data
        },
        enabled: !!selectedCategory
    })

    console.log('point', point)

    useEffect(() => {
        refetch()
    }, [currentLanguage, refetch])

    const { isPending: isStarting } = useMutation<QuizResult, Error, QuizStartRequest>({
        mutationFn: startQuiz,
        onSuccess: data => {
            dispatch(
                setQuizData({
                    token: data.token,
                    category_set_id: data.category_set_id
                })
            )
            navigate(`/test/${data.category_set_id}`)
        },
        onError: error => {
            console.error('Quiz start error:', error)
            alert('Произошла ошибка при начале теста. Пожалуйста, попробуйте снова.')
        }
    })

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target
        setFormData(prev => ({ ...prev, [name]: value }))
    }

    const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setIsAgreed(e.target.checked)
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        try {
            await axios.post(
                'http://localhost:8000/quiz/ent-diagnosis/',
                { ...formData },
                {
                    headers: {
                        'Accept-Language': currentLanguage
                    }
                }
            )
            alert('Данные успешно отправлены!')
            setFormData({
                name: '',
                phone: '',
                history_kazakhstan: '',
                math_literacy: '',
                reading_literacy: '',
                profile_subject_1: {
                    name: '',
                    score: ''
                },
                profile_subject_2: {
                    name: '',
                    score: ''
                }
            })
        } catch (error) {
            console.error('Error sending data:', error)
        }
    }

    if (isLoading) {
        return <Loader />
    }

    if (isError) {
        return (
            <div className='error-container'>
                <div className='error'>{t('form.error')}</div>
            </div>
        )
    }

    return (
        <div className='main-container'>
            <Link
                to='/'
                style={{
                    marginTop: '20px',
                    display: 'inline-block',
                    padding: '10px 20px',
                    backgroundColor: '#ed9e37', // yashil tugma
                    color: '#fff',
                    borderRadius: '8px',
                    textDecoration: 'none',
                    fontWeight: 'bold',
                    fontSize: '16px',
                    transition: 'background-color 0.3s ease',
                    textAlign: 'center'
                }}
                onMouseOver={e => (e.currentTarget.style.backgroundColor = '#45a049')}
                onMouseOut={e => (e.currentTarget.style.backgroundColor = '#4CAF50')}
            >
                {t('quizResult.backButton')}
            </Link>
            <LanguageSwitcher />

            {/* <div className='quiz-title'>
                <img src={yellowBg} alt='Background' className='yellow-bg' />
                <h1>{t('form.title')}</h1>
            </div> */}

            <div className='logo-container'>
                <img src='/logo.svg' alt='' />
            </div>

            <motion.div
                className='form-container'
                initial={{ opacity: 0, y: -50 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <div className='quiz__description'>{t('form.description')}</div>

                <div className='form-content'>
                    <div style={{ marginBottom: '10px' }} className=' text-cont'>
                        <h2 className='form-subtitle'>{t('form.yourDetails')}</h2>
                    </div>

                    <form id='' onSubmit={handleSubmit}>
                        <div className='input-group'>
                            <input
                                type='text'
                                name='name'
                                placeholder={t('form.name')}
                                required
                                value={formData.name}
                                onChange={handleChange}
                                disabled={isStarting}
                            />

                            <input
                                type='text'
                                name='phone'
                                placeholder={t('form.phone')}
                                required
                                value={formData.phone}
                                onChange={handleChange}
                                disabled={isStarting}
                            />
                        </div>

                        <div style={{ display: 'flex', gap: '20px', flexDirection: 'column' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <input
                                    name=''
                                    type='text'
                                    value={t('form.his')}
                                    readOnly
                                    className='form-subtitle'
                                    style={{ whiteSpace: 'nowrap', marginRight: '30px' }}
                                />
                                <input
                                    type='number'
                                    required
                                    max={20}
                                    name='history_kazakhstan'
                                    placeholder={t('form.point')}
                                    value={formData.history_kazakhstan}
                                    onChange={handleChange}
                                    disabled={isStarting}
                                />
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <input
                                    type='text'
                                    value={t('form.math')}
                                    readOnly
                                    className='form-subtitle'
                                    style={{ whiteSpace: 'nowrap', marginRight: '30px' }}
                                />
                                <input
                                    type='number'
                                    required
                                    max={10}
                                    name='math_literacy'
                                    placeholder={t('form.point')}
                                    value={formData.math_literacy}
                                    onChange={handleChange}
                                    disabled={isStarting}
                                />
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <input
                                    type='text'
                                    value={t('form.read')}
                                    readOnly
                                    className='form-subtitle'
                                    style={{ whiteSpace: 'nowrap', marginRight: '30px' }}
                                />
                                <input
                                    type='number'
                                    required
                                    max={10}
                                    name='reading_literacy'
                                    placeholder={t('form.point')}
                                    value={formData.reading_literacy}
                                    onChange={handleChange}
                                    disabled={isStarting}
                                />
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: '20px' }} className=''>
                            <div style={{ width: '100%' }}>
                                <div className=' text-cont'>
                                    <label
                                        style={{ marginBlock: '20px' }}
                                        htmlFor='category1'
                                        className='form-subtitle'
                                    >
                                        {t('form.prof1')}
                                    </label>
                                </div>
                                <Select
                                    id='category1'
                                    options={subject?.map((category: Category) => ({
                                        value: category.id,
                                        label: category.name
                                    }))}
                                    onChange={(selectedOption: any) => {
                                        setFormData(prev => ({
                                            ...prev,
                                            profile_subject_1: {
                                                ...prev.profile_subject_1,
                                                name: selectedOption?.label || ''
                                            }
                                        }))
                                    }}
                                    required
                                    isDisabled={isStarting}
                                    className='custom-select'
                                    placeholder={t('form.selectSubject')}
                                />
                            </div>
                            <div style={{ width: '100%', display: 'flex', alignItems: 'end' }}>
                                <input
                                    type='number'
                                    required
                                    max={50}
                                    value={formData.profile_subject_1.score}
                                    onChange={e =>
                                        setFormData(prev => ({
                                            ...prev,
                                            profile_subject_1: {
                                                ...prev.profile_subject_1,
                                                score: e.target.value
                                            }
                                        }))
                                    }
                                    placeholder={t('form.point')}
                                    disabled={isStarting}
                                />
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: '20px' }} className=''>
                            <div style={{ width: '100%' }}>
                                <div className=' text-cont'>
                                    <label
                                        style={{ marginBlock: '20px' }}
                                        htmlFor='category2'
                                        className='form-subtitle'
                                    >
                                        {t('form.prof2')}
                                    </label>
                                </div>
                                <Select
                                    id='category2'
                                    options={subject?.map((category: Category) => ({
                                        value: category.id,
                                        label: category.name
                                    }))}
                                    onChange={(selectedOption: any) => {
                                        setFormData(prev => ({
                                            ...prev,
                                            profile_subject_2: {
                                                ...prev.profile_subject_2,
                                                name: selectedOption?.label || ''
                                            }
                                        }))
                                    }}
                                    required
                                    isDisabled={isStarting}
                                    className='custom-select'
                                    placeholder={t('form.selectSubject')}
                                />
                            </div>
                            <div style={{ width: '100%', display: 'flex', alignItems: 'end' }}>
                                <input
                                    type='number'
                                    required
                                    max={50}
                                    value={formData.profile_subject_2.score}
                                    onChange={e =>
                                        setFormData(prev => ({
                                            ...prev,
                                            profile_subject_2: {
                                                ...prev.profile_subject_2,
                                                score: e.target.value
                                            }
                                        }))
                                    }
                                    placeholder={t('form.point')}
                                    disabled={isStarting}
                                />
                            </div>
                        </div>

                        <p style={{ marginTop: '50px' }}>
                            <strong>{t('form.ball')} </strong>
                        </p>

                        <div className='agreement'>
                            <input
                                type='checkbox'
                                id='dataAgreement'
                                required
                                disabled={isStarting}
                                checked={isAgreed}
                                onChange={handleCheckboxChange}
                            />
                            <label htmlFor='dataAgreement'>{t('form.dataAgreement')}</label>
                        </div>

                        <LoadingButton type='submit' isLoading={isStarting}>
                            {t('form.sendData')}
                        </LoadingButton>
                    </form>
                </div>
            </motion.div>
        </div>
    )
}
