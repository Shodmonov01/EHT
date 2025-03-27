import React from "react";
import { motion } from "framer-motion";
import "../../styles/Form.css";
import yellowBg from "../../assets/images/yellow-bg.png";
import logo from "../../assets/images/logores.svg";

export default function Form() {
  return (
    <div className="form-wrapper">
      <div className="header">
        <img src={logo} alt="Logo" className="logo" />
        <h1 className="title">Quiz</h1>
      </div>

      <motion.div
        className="form-container"
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="quiz__description">
          Привет, вы попали в систему Tesla Education Quiz, 
          Коротко о правилах - Не знаете ответа, не отвечайте! :)
        </div>

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
              
              <input 
                type="text" 
                id="name" 
                placeholder="ФИО"
                required 
              />
              
              <input 
                type="text" 
                id="phone" 
                placeholder="Номер телефона"
                required 
              />
              
              <select id="grade" required>
                <option value="">Выберите класс</option>
                <option value="1">Класс 1</option>
                <option value="2">Класс 2</option>
                <option value="3">Класс 3</option>
              </select>
            </div>

            <div className="agreement">
              <input 
                type="checkbox" 
                id="dataAgreement" 
                required 
              />
              <label htmlFor="dataAgreement">
                Я согласен(а) с <a href="#">условиями хранения и обработки персональных данных</a>
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
