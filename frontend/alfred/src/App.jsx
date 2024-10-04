import React, { useState, useEffect } from "react";
import { Layout, Alert } from "antd";
import Sidebar from "./components/sidebar/Sidebar.jsx";
import Chat from "./components/chat/Chat.jsx";
import Input from "./components/input/Input.jsx";
import axios from "axios";
import { v4 as uuidv4 } from 'uuid';

const { Sider, Content, Footer } = Layout;

const App = () => {
    const [selectedThread, setSelectedThread] = useState({ id: null, name: null });
    const [messages, setMessages] = useState([
        { id: uuidv4(), role: "AI", message_content: "Welcome! How can I assist you today?", avatar: "https://example.com/ai-avatar.png" },
    ]);
    const [loading, setLoading] = useState(false);
    const [threads, setThreads] = useState([]); // State to hold the chat threads

    useEffect(() => {
        // Fetch threads and set the first one as default
        const fetchThreads = async () => {
            try {
                const response = await axios.get("http://127.0.0.1:9000/threads/");
                const threadData = response.data; // Assume this returns an array of thread objects

                // Set the threads state with the fetched data
                setThreads(threadData);

                if (threadData.length > 0) {
                    // Set the first thread as the selected thread
                    setSelectedThread({ id: threadData[0].thread_id, name: threadData[0].name });
                }
            } catch (error) {
                console.error("Error fetching threads:", error);
            }
        };

        fetchThreads();
    }, []); // Empty dependency array to run on mount

    const handleSelectThread = (threadId, threadName) => {
        setSelectedThread({ id: threadId, name: threadName });
        setMessages([]); // Clear messages on thread switch
    };

    const handleSendMessage = async (message, threadId, threadName) => {
        const newMessage = {
            id: uuidv4(),
            role: "Human",
            message_content: message,
            avatar: "https://example.com/human-avatar.png",
        };

        setMessages((prevMessages) => [...prevMessages, newMessage]);
        setLoading(true);

        try {
            const response = await axios.post("http://127.0.0.1:9000/run_ai_thread/", {
                user_input: message,
                thread_id: threadId,
                thread_name: threadName,
            });

            const aiResponse = response.data.response;
            const aiMessage = {
                id: uuidv4(),
                role: "AI",
                message_content: aiResponse,
                avatar: "https://example.com/ai-avatar.png",
            };

            setMessages((prevMessages) => [...prevMessages, aiMessage]);
        } catch (error) {
            console.error("Error sending message:", error);
            const errorMessage = {
                id: uuidv4(),
                role: "AI",
                message_content: "Sorry, something went wrong. Please try again.",
                avatar: "https://example.com/error-avatar.png",
            };
            setMessages((prevMessages) => [...prevMessages, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Layout style={{ height: "100vh" }}>
            <Sider width={250} style={{ background: "#E2E8F0" }}>
                <Sidebar onSelectThread={handleSelectThread} threads={threads} /> {/* Pass threads to Sidebar */}
            </Sider>
            <Layout>
                <Content style={{ padding: '10px 10px', display: "flex", flexDirection: "column", backgroundColor: "#F8FAFC" }}>
                    <Chat
                        chatId={selectedThread.id}
                        messages={messages}
                        setMessages={setMessages}
                        loading={loading}
                        style={{ flexGrow: 1, overflowY: "auto", padding: '5px 5px', backgroundColor: "#F8FAFC" }}
                    /> {/* Directly pass styles to the Chat component */}
                    <Footer style={{ padding: '5px 1px', backgroundColor: "#F8FAFC" }}> {/* Reduced footer padding */}
                        <Input onSendMessage={handleSendMessage} threadId={selectedThread.id} threadName={selectedThread.name} />
                    </Footer>
                </Content>


            </Layout>
        </Layout>
    );
};

export default App;
