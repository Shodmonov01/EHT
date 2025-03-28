import { motion } from "framer-motion";
import "../../styles/QlientResults.css";
import yellowBg from "../../assets/images/yellow-bg.png";
import { ResultProps } from "../../types/quizs";

  

export default function QlientResult({
  correctQuestions = 0,
  totalQuestions = 0,
  percentageScore = 0,
  quizName = "",
  quizResultId = "",
}: ResultProps) {
  return (
    <motion.div
      className="result-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <motion.div
        className="title"
        initial={{ y: -50 }}
        animate={{ y: 0 }}
        transition={{ delay: 0.2, type: "spring" }}
      >
        <h1>Благодарим за честность!</h1>
        <img className="title__img" src={yellowBg} alt="Background" />
      </motion.div>

      <motion.div
        className="result-content"
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        <motion.div className="score-card" whileHover={{ scale: 1.02 }}>
          <h2>Ваши результаты</h2>
          <motion.div
            className="score-details"
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            <p>
              Правильных ответов:{" "}
              <strong>
                {correctQuestions} из {totalQuestions}
              </strong>
            </p>
            <p>
              Процент выполнения: <strong>{percentageScore}%</strong>
            </p>
            <p>
              Название теста: <strong>{quizName}</strong>
            </p>
          </motion.div>
        </motion.div>

        <motion.div
          className="download-section"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.8 }}
        >
          <h2>Мы уже генерируем ваши результаты!</h2>
          <div className="button-group">
            <motion.a
              href={`/summary-pdf/${quizResultId}`}
              className="download-button"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              target="_blank"
            >
              Посмотреть диагностику
            </motion.a>
            <motion.a
              href={`/table-pdf/${quizResultId}`}
              className="download-button secondary"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              target="_blank"
            >
              Посмотреть результаты по темам
            </motion.a>
          </div>
        </motion.div>
      </motion.div>
    </motion.div>
  );
}
