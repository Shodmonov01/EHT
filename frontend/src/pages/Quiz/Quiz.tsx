import React, { useState } from 'react';
import { motion } from 'framer-motion';
import '../../styles/Quiz.css';
import yellowBg from '../../assets/images/yellow-bg.png';
import { Category } from '../../types/quizs';

export default function Quiz() {
  const [selectedAnswers, setSelectedAnswers] = useState<{[key: number]: number}>({});
  const categories: Category[] = [
    {
      name: "English",
      questions: [
        {
          id: 1,
          text: 'Complete the sentence: "______ a rainbow in the sky."',
          answers: [
            { id: 1, text: 'There was' },
            { id: 2, text: 'There were' },
            { id: 3, text: 'There' },
            { id: 4, text: 'There are' },
          ]
        },
        {
          id: 2,
          text: 'What is the past tense of "there are"?',
          answers: [
            { id: 5, text: 'There was' },
            { id: 6, text: 'There were' },
            { id: 7, text: 'There is' },
            { id: 8, text: 'There be' },
          ]
        }
      ]
    }
  ];

  const handleAnswerSelect = (questionId: number, answerId: number) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: answerId
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log(selectedAnswers);
  };

  return (
    <motion.div 
      className="quiz-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="title">
        Quiz
        <img className="title__img" src={yellowBg} alt="Background" />
      </div>

      <motion.div 
        className="quiz__description"
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        Привет, вы попали в систему Tesla Education Quizz, Коротко о правилах - будьте честны :)
      </motion.div>

      <form id="quizForm" onSubmit={handleSubmit}>
        <div className="quizContainer">
          {categories.map((category, index) => (
            <motion.div 
              key={category.name}
              className="category"
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.3 + index * 0.1 }}
            >
              <h2>{category.name}</h2>
              <ol>
                {category.questions.map((question, qIndex) => (
                  <motion.div 
                    key={question.id}
                    className="question"
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.4 + qIndex * 0.1 }}
                  >
                    <li>
                      <div className="question__title">{question.text}</div>
                    </li>
                    {question.image && (
                      <div className="question__image">
                        <img src={question.image} alt={question.text} />
                      </div>
                    )}
                    <div className="question__answers">
                      {question.answers.map(answer => (
                        <motion.div 
                          key={answer.id}
                          className="radio-container"
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <label className="radio-label">
                            <input
                              type="radio"
                              name={`question${question.id}`}
                              value={answer.id}
                              checked={selectedAnswers[question.id] === answer.id}
                              onChange={() => handleAnswerSelect(question.id, answer.id)}
                            />
                            <span className="radio-checkmark"></span>
                            {answer.text}
                          </label>
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>
                ))}
              </ol>
            </motion.div>
          ))}
          
          <motion.button
            className="submitButton"
            type="submit"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Готово!
          </motion.button>
        </div>
      </form>
    </motion.div>
  );
}
