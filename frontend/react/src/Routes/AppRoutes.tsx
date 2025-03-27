import { Routes, Route } from "react-router-dom";
import Form from "../pages/Form/Form";
const AppRoutes = () => {
    return (
        <Routes>
            <Route path="/" element={<Form />} />
        </Routes>
    )
}

export default AppRoutes;
