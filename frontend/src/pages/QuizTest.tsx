import React, { useEffect, useState } from 'react'
import { useParams, useNavigate, Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useSelector, useDispatch } from 'react-redux'
import '../styles/QuizTest.css'
import { fetchQuestions, submitQuiz } from '../api/request.api'
import { setQuizData } from '../redux/features/quizSlice'
import { RootState } from '../redux/store'

function QuizTest() {
    const { categorySetId } = useParams<{ categorySetId: string }>()
    const navigate = useNavigate()
    const dispatch = useDispatch()

    const quizData = useSelector((state: RootState) => state.quiz)
    const currentLanguage = useSelector((state: RootState) => state.language.currentLanguage)

    const [selectedAnswers, setSelectedAnswers] = useState<{ [key: number]: number[] }>({})
    const [isSubmitting, setIsSubmitting] = useState(false)

    useEffect(() => {
        const token = localStorage.getItem('quiz_token')
        const categoryId = localStorage.getItem('quiz_category_id')

        if (token && categoryId && !quizData.token) {
            dispatch(setQuizData({ token, category_set_id: categoryId }))
        }
    }, [dispatch, quizData.token])

    const {
        data: questionsData,
        isLoading,
        isError,
        refetch
    } = useQuery({
        queryKey: ['new-quiz', categorySetId, currentLanguage],
        queryFn: () => fetchQuestions(Number(categorySetId)),
        enabled: !!(categorySetId && (quizData.token || localStorage.getItem('quiz_token')))
    })

    useEffect(() => {
        if (currentLanguage) {
            refetch()
        }
    }, [currentLanguage, refetch])

    if (!quizData.token && !localStorage.getItem('quiz_token')) {
        return <Navigate to='/' />
    }

    const handleCheckboxChange = (questionId: number, answerId: number) => {
        setSelectedAnswers(prev => {
            const current = prev[questionId] || []

            return {
                ...prev,
                [questionId]: current.includes(answerId)
                    ? current.filter(id => id !== answerId)
                    : [...current, answerId]
            }
        })
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        const token = quizData.token || localStorage.getItem('quiz_token')
        if (!token) return

        const answerIds = Object.values(selectedAnswers).flat()
        const unanswered =
            questionsData?.flatMap(cat => cat.questions.filter(q => !selectedAnswers[q.id]?.length).map(q => q.id)) ||
            []

        setIsSubmitting(true)

        try {
            await submitQuiz(token, answerIds, unanswered)
            localStorage.removeItem('quiz_token')
            localStorage.removeItem('quiz_category_id')
            navigate('/test-submit')
        } catch (error) {
            console.error('Error submitting quiz:', error)
        } finally {
            setIsSubmitting(false)
        }
    }

    if (isLoading) return <div className='qt-loader'>Loading...</div>
    if (isError) return <div className='qt-error'>Failed to load questions.</div>
    if (!questionsData?.length) return <div className='qt-empty'>No questions available.</div>

    return (
        <>
            <div className='qt-page' />
            <div className='qt-scroll'>
                <div className='qt-container'>
                    <h1 className='qt-title'>Quiz Test</h1>
                    <form onSubmit={handleSubmit} className='qt-form'>
                        {questionsData.map(category => (
                            <div key={category.category_id} className='qt-category'>
                                <h2 className='qt-category-title'>{category.category_name}</h2>
                                {category.questions.map(question => (
                                    <div key={question.id} className='qt-question-block'>
                                        <p className='qt-question-text'>{question.text}</p>
                                        <div className='qt-answers'>
                                            {question.answers.map(answer => (
                                                <label key={answer.id} className='qt-answer'>
                                                    <input
                                                        type='checkbox'
                                                        value={answer.id}
                                                        checked={
                                                            selectedAnswers[question.id]?.includes(answer.id) || false
                                                        }
                                                        onChange={() => handleCheckboxChange(question.id, answer.id)}
                                                    />
                                                    <span>{answer.text}</span>
                                                </label>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ))}
                        <button type='submit' className='qt-submit-btn' disabled={isSubmitting}>
                            {isSubmitting ? 'Submitting...' : 'Submit Quiz'}
                        </button>
                    </form>
                </div>
            </div>
        </>
    )
}

export default QuizTest
