import { useState } from 'react';
import MainLayout from "./layouts/MainLayout.jsx";
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Chat from "./components/chat/Chat.jsx";
import NewChat from "./components/new_chat/NewChat.jsx";
import Check from "./components/Check.jsx";

const App = () => {
    const [threadId, setThreadId] = useState(null);

    return (
        <Router>
            <Routes>
                <Route
                    path="/"
                    element={
                        <MainLayout />
                    }
                >
                    <Route index element={<NewChat />} />
                    {/* Pass setThreadId and threadId to Outlet context */}
                    <Route
                        path="thread/:thread_id"
                        element={
                            <Chat />
                        }
                        context={{ threadId, setThreadId }}  // Pass context here
                    />
                    <Route path="checkout" element={<Check />} />
                </Route>
            </Routes>
        </Router>
    );
};

export default App;
