import { motion } from "framer-motion";
import "../../styles/Form.css";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import { useTranslation } from "react-i18next";
import yellowBg from "../../assets/images/yellow-bg.png";
import { useQuery, useMutation } from "@tanstack/react-query";
import { fetchCategories, startQuiz } from "../../api/request.api";
import { useState, useEffect } from "react";
import { QuizStartRequest, QuizResult, Category } from "../../types/quizs";
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { setQuizData } from "../../redux/features/quizSlice";
import Select from 'react-select';
import { RootState } from "../../redux/store";
import Loader from "../../components/Loader";
import LoadingButton from "../../components/LoadingButton";

export default function Form() {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const currentLanguage = useSelector((state: RootState) => state.language.currentLanguage);
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
    refetch
  } = useQuery({
    queryKey: ["categories", currentLanguage],
    queryFn: async () => {
      const data = await fetchCategories();
      return data;
    },
  });
  

  useEffect(() => {
    refetch();
  }, [currentLanguage, refetch]);

  const { mutate: startQuizMutation, isPending: isStarting } = useMutation<
    QuizResult,
    Error,
    QuizStartRequest
  >({
    mutationFn: startQuiz,
    onSuccess: (data) => {
      dispatch(
        setQuizData({
          token: data.token,
          category_set_id: data.category_set_id,
        })
      );
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
      startQuizMutation(quizData);
    }
  };

  if (isLoading) {
    return <Loader />;
  }

  if (isError) {
    return (
      <div className="error-container">
        <div className="error">{t("form.error")}</div>
      </div>
    );
  }

  return (
    <div className="form-wrapper">
      <LanguageSwitcher />
      <div className="quiz-title">
        <img src={yellowBg} alt="Background" className="yellow-bg" />
        <h1>{t("form.title")}</h1>
      </div>

      <motion.div
        className="form-container"
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="quiz__description">{t("form.description")}</div>

        <div className="form-content">
          <h2 className="form-subtitle">{t("form.aboutYou")}</h2>

          <form id="quizForm" onSubmit={handleSubmit}>
            <div className="input-group">
              <input
                type="text"
                name="parents_fullname"
                placeholder={t("form.parentName")}
                required
                value={formData.parents_fullname}
                onChange={handleChange}
                disabled={isStarting}
              />

              <input
                type="text"
                name="name"
                placeholder={t("form.fullName")}
                required
                value={formData.name}
                onChange={handleChange}
                disabled={isStarting}
              />

              <input
                type="text"
                name="phone_number"
                placeholder={t("form.phone")}
                required
                value={formData.phone_number}
                onChange={handleChange}
                disabled={isStarting}
              />
            </div>

            <div className="input-group category-select">
              <label htmlFor="category">{t("form.selectClass")}:</label>
              <Select
                id="category"
                options={categories?.map((category: Category) => ({
                  value: category.id,
                  label: category.name,
                }))}
                onChange={(selectedOption) => setSelectedCategory(selectedOption?.value || null)}
                required
                isDisabled={isStarting}
                className="custom-select"
                placeholder={t("form.selectSubject")}
              />
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
              <label htmlFor="dataAgreement">{t("form.dataAgreement")}</label>
            </div>

            <LoadingButton
              type="submit"
              isLoading={isStarting}
              disabled={!selectedCategory}
            >
              {t("form.startForm")}
            </LoadingButton>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
