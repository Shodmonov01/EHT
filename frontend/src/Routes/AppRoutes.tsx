import { Routes, Route } from "react-router-dom";
import Form from "../pages/Form/Form";
import Quiz from "../pages/Quiz/Quiz";
import QlientResult from "../pages/Result/QlientResult";
import QuizResult from "../pages/Result/QuizResult";
import SubmitResult from "../pages/Result/SubmitResult";
const AppRoutes = () => {
    return (    
        <Routes>
            <Route path="/" element={<Form />} />
            <Route path="/quiz/:categorySetId" element={<Quiz />} />
            <Route path="/qlient-result" element={<QlientResult correctQuestions={0} totalQuestions={0} percentageScore={0} quizName={""} quizResultId={""} />} />
            <Route path="/quiz-result" element={<QuizResult correctQuestions={0} totalQuestions={0}  quizName={""} quizResultId={""} />} />
            <Route path="/quiz-submit" element={<SubmitResult />} />
        </Routes>
    )
}
export default AppRoutes; 