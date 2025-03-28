import { motion } from "framer-motion";
import "../../styles/Form.css";
import LanguageSwitcher from "../../components/LanguageSwitcher";
import { useTranslation } from "react-i18next";
import yellowBg from "../../assets/images/yellow-bg.png";
export default function Form() {
  const { t } = useTranslation();

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

          <form id="quizForm">
            <div className="input-group">
              <input
                type="text"
                id="parentName"
                placeholder="ФИО Родителя"
                required
              />

              <input type="text" id="name" placeholder="ФИО" required />

              <input
                type="text"
                id="phone"
                placeholder="Номер телефона"
                required
              />
            </div>

            <div className="agreement">
              <input type="checkbox" id="dataAgreement" required />
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
            >
              Приступить!
            </motion.button>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
