import { useState, useEffect } from "react";
import { useParams, Navigate, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { fetchQuestions, submitQuiz } from "../../api/request.api";
import "../../styles/Quiz.css";
import yellowBg from "../../assets/images/yellow-bg.png";
import { useSelector } from "react-redux";
import { RootState } from "../../redux/store";
import { useTranslation } from "react-i18next";
import Loader from "../../components/Loader";
import LoadingButton from "../../components/LoadingButton";

interface Answer {
  id: number;
  text: string;
  image?: string;
}

export default function Quiz() {
  const { categorySetId } = useParams<{ categorySetId: string }>();
  const quizData = useSelector((state: RootState) => state.quiz);
  const currentLanguage = useSelector(
    (state: RootState) => state.language.currentLanguage
  );
  const [selectedAnswers, setSelectedAnswers] = useState<{
    [key: number]: number[];
  }>({});
  const [showRequired, setShowRequired] = useState<{ [key: number]: boolean }>(
    {}
  );
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {}, [currentLanguage]);

  if (!quizData.token) {
    return <Navigate to="/" />;
  }

  const {
    data: questionsData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["questions", categorySetId, currentLanguage],
    queryFn: () => fetchQuestions(Number(categorySetId)),
    enabled: !!categorySetId && !!quizData.token,
  });
  console.log(questionsData);

  useEffect(() => {
    if (currentLanguage) {
      refetch();
    }
  }, [currentLanguage, refetch]);

  if (isLoading) {
    return <Loader />;
  }

  if (isError) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="error"
      >
        {t("form.questionError")}
      </motion.div>
    );
  }

  if (!questionsData?.length) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="no-questions"
      >
        {t("form.categoryNotF")}
      </motion.div>
    );
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const userToken = quizData.token;
    if (!userToken) {
      return;
    }

    setIsSubmitting(true);

    const answerIds = Object.values(selectedAnswers).flat();

    const unansweredQuestionIds = questionsData.flatMap((category) =>
      category.questions
        .filter(
          (question) =>
            !selectedAnswers[question.id] ||
            selectedAnswers[question.id].length === 0
        )
        .map((q) => q.id)
    );

    const requestData = {
      user_token: userToken,
      answer_ids: answerIds,
      unanswered_question_ids: unansweredQuestionIds,
    };
    console.log("Yuborilayotgan ma'lumotlar:", requestData);

    submitQuiz(userToken, answerIds, unansweredQuestionIds)
      .then((response) => {
        console.log("Muvaffaqiyatli yuborildi:", response);
        navigate(`/quiz-submit`);
      })
      .catch((error) => {
        console.error("Xatolik yuz berdi:", error);
        console.log("Xatolik tafsilotlari:", error.response?.data);
      })
      .finally(() => {
        setIsSubmitting(false);
      });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="quiz-container"
    >
      <motion.div
        className="title quiz_title"
        initial={{ opacity: 0, x: -50 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.2 }}
      >
        <h1>{t("form.title")}</h1>
        <img className="title__img" src={yellowBg} alt="Background" />
      </motion.div>

      <motion.div
        className="quiz__description"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        {t("form.description")}
      </motion.div>

      <form onSubmit={handleSubmit}>
        <div className="quizContainer">
          <AnimatePresence>
            {questionsData.map((category, categoryIndex) => (
              <motion.div
                key={category.category_id}
                className="category"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 * categoryIndex }}
              >
                <h2>{category.category_name}</h2>
                <ol>
                  {category.questions.map((question, questionIndex) => (
                    <motion.div
                      key={question.id}
                      className="question"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 * questionIndex }}
                    >
                      <li>
                        <div className="question__title">
                          {question.text}
                          {question.correct_answers_count &&
                            question.correct_answers_count > 1 && (
                              <span className="multiple-answers-hint">
                                (
                                {t("form.multipleAnswers", {
                                  count: question.correct_answers_count,
                                })}
                                )
                              </span>
                            )}
                        </div>
                      </li>
                      {question.image && (
                        <motion.div
                          className="question__image"
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: 0.2 }}
                        >
                          <img src={question.image} alt={question.text} />
                        </motion.div>
                      )}
                      <div className="question__answers">
                        {question.answers.map((answer: Answer) => (
                          <motion.label
                            key={answer.id}
                            className="radio-container"
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                          >
                            <input
                              type="checkbox"
                              name={`question${question.id}`}
                              value={answer.id}
                              checked={
                                selectedAnswers[question.id]?.includes(
                                  answer.id
                                ) || false
                              }
                              onChange={() => {
                                setSelectedAnswers((prev) => {
                                  const currentAnswers =
                                    prev[question.id] || [];

                                  if (currentAnswers.includes(answer.id)) {
                                    return {
                                      ...prev,
                                      [question.id]: currentAnswers.filter(
                                        (a) => a !== answer.id
                                      ),
                                    };
                                  } else {
                                    return {
                                      ...prev,
                                      [question.id]: [
                                        ...currentAnswers,
                                        answer.id,
                                      ],
                                    };
                                  }
                                });

                                setShowRequired((prev) => ({
                                  ...prev,
                                  [question.id]: false,
                                }));
                              }}
                            />
                            <span className="radio-checkmark"></span>
                            <span className="radio-label">{answer.text}</span>
                            {answer.image && (
                              <img
                                src={answer.image}
                                alt={answer.text}
                                className="answer-image"
                              />
                            )}
                          </motion.label>
                        ))}
                        {showRequired[question.id] && (
                          <motion.div
                            className="required-message"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                          >
                            {t("form.requiredAnswer")}
                          </motion.div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </ol>
              </motion.div>
            ))}
          </AnimatePresence>
          <LoadingButton
            type="submit"
            isLoading={isSubmitting}
            disabled={isSubmitting}
          >
            {t("form.quizReadyBtn")}
          </LoadingButton>
        </div>
      </form>
    </motion.div>
  );
}
