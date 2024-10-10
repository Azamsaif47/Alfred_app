import MainLayout from "./layouts/MainLayout.jsx";
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Chat from "./components/chat/Chat.jsx";

const App = () => {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<MainLayout />}>
                    <Route path="/thread/:thread_id" element={<Chat />} />
                </Route>
            </Routes>
        </Router>
    );
};

export default App;
