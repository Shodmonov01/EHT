import { motion } from 'framer-motion'
import '../../styles/Form.css'
import LanguageSwitcher from '../../components/LanguageSwitcher'
import { useTranslation } from 'react-i18next'
// import yellowBg from '../../assets/images/yellow-bg.png'
import { useQuery, useMutation } from '@tanstack/react-query'
import { startQuiz } from '../../api/request.api'
import { useState, useEffect } from 'react'
import { QuizStartRequest, QuizResult, Category } from '../../types/quizs'
import { useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { setQuizData } from '../../redux/features/quizSlice'
import Select from 'react-select'
import { RootState } from '../../redux/store'
import Loader from '../../components/Loader'
import LoadingButton from '../../components/LoadingButton'
// import { div } from 'framer-motion/client'

export default function FormSt() {
    const { t } = useTranslation()
    const dispatch = useDispatch()
    const currentLanguage = useSelector((state: RootState) => state.language.currentLanguage)
    const [selectedCategory, setSelectedCategory] = useState<number | null>(null)
    const [formData, setFormData] = useState({
        name: '',
        parents_fullname: '',
        phone_number: ''
    })
    const [isAgreed, setIsAgreed] = useState(false)
    const token = localStorage.getItem('token')

    const navigate = useNavigate()
    console.log('selectedCategory', selectedCategory)
    console.log('currentLanguage', currentLanguage)

    // const {
    //     data: subject,
    //     isError,
    //     isLoading,
    //     refetch
    // } = useQuery({
    //     queryKey: ['subjects', currentLanguage],
    //     queryFn: async () => {
    //         const response = await fetch(`http://185.191.141.172:8001/quiz/subjects`)
    //         if (!response.ok) {
    //             throw new Error('Network response was not ok')
    //         }
    //         const data = await response.json()
    //         return data
    //     }
    // })

    // console.log('subject', subject)

    const { data: point } = useQuery({
        queryKey: ['points', currentLanguage, selectedCategory],
        queryFn: async () => {
            const response = await fetch(`http://185.191.141.172:8001/quiz/subjects/result/${token}/`)

            if (!response.ok) {
                throw new Error('Network response was not ok')
            }

            const data = await response.json()
            return data
        },
        enabled: !!selectedCategory
    })

    console.log('point', point)

    // useEffect(() => {
    //     refetch()
    // }, [currentLanguage, refetch])

    const { mutate: startQuizMutation, isPending: isStarting } = useMutation<QuizResult, Error, QuizStartRequest>({
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

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        const quizData: QuizStartRequest = {
            name: formData.name,
            parents_fullname: formData.parents_fullname,
            phone_number: formData.phone_number,
            category_set_id: selectedCategory || 0,
            is_agreed: isAgreed
        }

        if (selectedCategory) {
            startQuizMutation(quizData)
        }
    }

    // if (isLoading) {
    //     return <Loader />
    // }

    // if (isError) {
    //     return (
    //         <div className='error-container'>
    //             <div className='error'>{t('form.error')}</div>
    //         </div>
    //     )
    // }

    return (
        <div className='main-container'>
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
                                name='parents_fullname'
                                placeholder={t('form.name')}
                                required
                                value={formData.parents_fullname}
                                onChange={handleChange}
                                disabled={isStarting}
                            />

                            <input
                                type='text'
                                name='name'
                                placeholder={t('form.phone')}
                                required
                                value={formData.name}
                                onChange={handleChange}
                                disabled={isStarting}
                            />
                        </div>

                        <div style={{ display: 'flex', gap: '20px', flexDirection: 'column' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <input
                                    type='text'
                                    value='История Казахстана'
                                    readOnly
                                    className='form-subtitle'
                                    style={{ whiteSpace: 'nowrap', marginRight: '30px' }}
                                />
                                <input type='number' />
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <input
                                    type='text'
                                    value='Математическая грамотность'
                                    readOnly
                                    className='form-subtitle'
                                    style={{ whiteSpace: 'nowrap', marginRight: '30px' }}
                                />
                                <input type='number' />
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <input
                                    type='text'
                                    value='Грамотность чтения'
                                    readOnly
                                    className='form-subtitle'
                                    style={{ whiteSpace: 'nowrap', marginRight: '30px' }}
                                />
                                <input type='number' />
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: '20px' }} className=''>
                            <div style={{ width: '100%' }}>
                                <div className=' text-cont'>
                                    <label style={{ marginBlock: '20px' }} htmlFor='category' className='form-subtitle'>
                                        {/* {t('form.selectClass')}: */}
                                        Профильный предмет №1
                                    </label>
                                </div>
                                <Select
                                    id='category'
                                    // options={categories?.map((category: Category) => ({
                                    //     value: category.id,
                                    //     label: category.name
                                    // }))}
                                    // onChange={selectedOption => setSelectedCategory(selectedOption?.value || null)}
                                    required
                                    isDisabled={isStarting}
                                    className='custom-select'
                                    placeholder={t('form.selectSubject')}
                                />
                            </div>
                            <div style={{ width: '100%', display: 'flex', alignItems: 'end' }}>
                                <input type='number' />
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: '20px' }} className=''>
                            <div style={{ width: '100%' }}>
                                <div className=' text-cont'>
                                    <label style={{ marginBlock: '20px' }} htmlFor='category' className='form-subtitle'>
                                        {/* {t('form.selectClass')}: */}
                                        Профильный предмет №2
                                    </label>
                                </div>
                                <Select
                                    id='category'
                                    // options={categories?.map((category: Category) => ({
                                    //     value: category.id,
                                    //     label: category.name
                                    // }))}
                                    // onChange={selectedOption => setSelectedCategory(selectedOption?.value || null)}
                                    required
                                    isDisabled={isStarting}
                                    className='custom-select'
                                    placeholder={t('form.selectSubject')}
                                />
                            </div>
                            <div style={{ width: '100%', display: 'flex', alignItems: 'end' }}>
                                <input type='number' />
                            </div>
                        </div>

                        <p style={{ marginTop: '50px' }}>
                            <strong>Суммарное количество возможных баллов: 140</strong>
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

                        <LoadingButton type='submit' isLoading={isStarting} disabled={!selectedCategory}>
                            {t('form.sendData')}
                        </LoadingButton>
                    </form>
                </div>
            </motion.div>
        </div>
    )
}
