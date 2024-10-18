import MainLayout from "./layouts/MainLayout.jsx";
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Chat from "./components/chat/Chat.jsx";
import NewChat from "./components/new_chat/NewChat.jsx";

const App = () => {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<MainLayout />}>
                    {/* Render NewChat on the base URL */}
                    <Route index element={<NewChat />} />

                    {/* Render Chat on thread route */}
                    <Route path="thread/:thread_id" element={<Chat />} />
                </Route>
            </Routes>
        </Router>
    );
};

export default App;
