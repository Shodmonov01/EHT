import { Routes, Route } from "react-router-dom";
import Form from "../pages/Form/Form";
import Quiz from "../pages/Quiz/Quiz";
import QlientResult from "../pages/Result/QlientResult";
// import QuizResult from "../pages/Result/QuizResult";
import SubmitResult from "../pages/Result/SubmitResult";
import QuizTest from "../pages/QuizTest";
const AppRoutes = () => {
    return (    
        <Routes>
            <Route path="/" element={<Form />} />
            <Route path="/test/:categorySetId" element={<Quiz />} />
            <Route path="/qlient-result" element={<QlientResult correctQuestions={0} totalQuestions={0} percentageScore={0} quizName={""} quizResultId={""} />} />
            {/* <Route path="/test-result" element={<QuizResult correctQuestions={0} totalQuestions={0}  quizName={""} quizResultId={""} />} /> */}
            <Route path="/test-submit" element={<SubmitResult />} />
        </Routes>
    )
}
export default AppRoutes; 