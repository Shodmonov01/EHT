import { useState } from "react";
import { useParams, Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { fetchQuestions, submitQuiz } from "../../api/request.api";
import "../../styles/Quiz.css";
import yellowBg from "../../assets/images/yellow-bg.png";
import { useSelector } from "react-redux";
import { RootState } from "../../redux/store";
import { useTranslation } from "react-i18next";
interface Answer {
  id: number;
  text: string;
  image?: string;
}
export default function Quiz() {
  
  const { categorySetId } = useParams<{ categorySetId: string }>();
  const quizData = useSelector((state: RootState) => state.quiz);
  const [selectedAnswers, setSelectedAnswers] = useState<{
    [key: number]: number;
  }>({});
  const [showRequired, setShowRequired] = useState<{ [key: number]: boolean }>({});
  const { t } = useTranslation();

  if (!quizData.token) {
    return <Navigate to="/" />;
  }

  const {
    data: questionsData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["questions", categorySetId],
    queryFn: () => fetchQuestions(Number(categorySetId)),
    enabled: !!categorySetId && !!quizData.token,
  });
console.log(questionsData);

  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="loading"
      >
        {t("form.loadQuestion")}
      </motion.div>
    );
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

    // Collect the selected answer IDs
    const answerIds = Object.values(selectedAnswers);
    
    // Log the selected answers for debugging
    console.log("Selected answers:", answerIds);

    const userToken = quizData.token;
    if (!userToken) {
      console.error("User token is null");
      alert(t("form.tokenError"));
      return;
    }

    // Prepare unanswered question IDs if needed
    const unansweredQuestionIds = questionsData.flatMap(category =>
      category.questions
        .filter(question => !selectedAnswers[question.id])
        .map(q => q.id)
    );

    console.log("Sending answers:", { userToken, answerIds, unansweredQuestionIds });

    // Submit the quiz with the selected answers
    submitQuiz(userToken, answerIds, unansweredQuestionIds)
      .then(response => {
        console.log("Quiz submitted successfully:", response);
        // Handle successful submission (e.g., navigate to results page)
      })
      .catch(error => {
        console.error("Error submitting quiz:", error);
        alert(t("form.submitError"));
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
        className="title"
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
                        <div className="question__title">{question.text}</div>
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
                              type="radio"
                              name={`question${question.id}`}
                              value={answer.id}
                              checked={selectedAnswers[question.id] === answer.id}
                              onChange={() => {
                                setSelectedAnswers((prev) => ({
                                  ...prev,
                                  [question.id]: answer.id,
                                }));
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
          <motion.button
            type="submit"
            className="submitButton"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {t("form.quizReadyBtn")}
          </motion.button>
        </div>
      </form>
    </motion.div>
  );
}
