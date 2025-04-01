import { motion } from "framer-motion";
import "../../styles/Form.css";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import { useTranslation } from "react-i18next";
import yellowBg from "../../assets/images/yellow-bg.png";
import { useQuery, useMutation } from "@tanstack/react-query";
import { fetchCategories, startQuiz } from "../../api/request.api";
import { useState } from "react";
import { QuizStartRequest, QuizResult, Category } from "../../types/quizs";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { setQuizData } from "../../redux/features/quizSlice";

export default function Form() {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    parents_fullname: "",
    phone_number: "",
  });
  const [isAgreed, setIsAgreed] = useState(false);
  const navigate = useNavigate();

  const {
    data: categories,
    isError,
    isLoading,
  } = useQuery({
    queryKey: ["categories"],
    queryFn: async () => {
      const data = await fetchCategories();
      console.log(data);
      return data;
    },
  });

  const { mutate: startQuizMutation, isPending: isStarting } = useMutation<
    QuizResult,
    Error,
    QuizStartRequest
  >({
    mutationFn: startQuiz,
    onSuccess: (data) => {
      console.log("Quiz started successfully:", data);
      dispatch(setQuizData({
        token: data.token,
        category_set_id: data.category_set_id
      }));
      navigate(`/quiz/${data.category_set_id}`);
    },
    onError: (error) => {
      console.error("Quiz start error:", error);
      alert("Произошла ошибка при начале теста. Пожалуйста, попробуйте снова.");
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setIsAgreed(e.target.checked);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedCategory) {
      const quizData: QuizStartRequest = {
        name: formData.name,
        parents_fullname: formData.parents_fullname,
        phone_number: formData.phone_number,
        category_set_id: selectedCategory,
        is_agreed: isAgreed,
      };
      console.log('Sending data:', quizData);
      startQuizMutation(quizData);
    }
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading">Загрузка категорий...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="error-container">
        <div className="error">
          Ошибка при загрузке категорий. Пожалуйста, обновите страницу.
        </div>
      </div>
    );
  }

  return (
    <div className="form-wrapper">
      <LanguageSwitcher />
      <div className="quiz-title">
        <img src={yellowBg} alt="Background" className="yellow-bg" />
        <h1>Quiz</h1>
      </div>

      <motion.div
        className="form-container"
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="quiz__description">{t("form.description")}</div>

        <div className="form-content">
          <h2 className="form-subtitle">Расскажите нам о себе</h2>

          <form id="quizForm" onSubmit={handleSubmit}>
            <div className="input-group">
              <input
                type="text"
                name="parents_fullname"
                placeholder="ФИО Родителя"
                required
                value={formData.parents_fullname}
                onChange={handleChange}
                disabled={isStarting}
              />

              <input
                type="text"
                name="name"
                placeholder="ФИО"
                required
                value={formData.name}
                onChange={handleChange}
                disabled={isStarting}
              />

              <input
                type="text"
                name="phone_number"
                placeholder="Номер телефона"
                required
                value={formData.phone_number}
                onChange={handleChange}
                disabled={isStarting}
              />
            </div>

            <div className="input-group category-select">
              <label htmlFor="category">Выберите предмет:</label>
              <select
                id="category"
                onChange={(e) => setSelectedCategory(Number(e.target.value))}
                required
                disabled={isStarting}
                className="custom-select"
              >
                <option value="">Выберите предмет</option>
                {categories?.map((category: Category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="agreement">
              <input
                type="checkbox"
                id="dataAgreement"
                required
                disabled={isStarting}
                checked={isAgreed}
                onChange={handleCheckboxChange}
              />
              <label htmlFor="dataAgreement">
                Я согласен(а) с{" "}
                <a href="#">
                  условиями хранения и обработки персональных данных
                </a>
              </label>
            </div>

            <motion.button
              type="submit"
              className="submit-button"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              disabled={isStarting || !selectedCategory}
            >
              {isStarting ? "Загрузка..." : "Приступить!"}
            </motion.button>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
