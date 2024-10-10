import React, { useEffect, useState } from 'react';
import { Layout } from 'antd';
import Sidebar from "../components/sidebar/Sidebar.jsx";
import { v4 as uuidv4 } from "uuid";
import axios from "axios";
import Input from "../components/input/Input.jsx";
import Chat from "../components/chat/Chat.jsx";

const { Sider, Content, Footer } = Layout;

const MainLayout = () => {
    const [selectedThread, setSelectedThread] = useState({ id: null, name: null });
    const [messages, setMessages] = useState([
        { id: uuidv4(), role: "AI", message_content: "Welcome! How can I assist you today?", avatar: "https://example.com/ai-avatar.png" },
    ]);
    const [loading, setLoading] = useState(false);
    const [source, setSource] = useState([]);
    const baseURL = import.meta.env.VITE_API_URL;
    const [threads, setThreads] = useState([]);

    useEffect(() => {
        console.log("Updated source:", source);
    }, [source]);

    useEffect(() => {
        // Fetch threads and set the first one as default
        const fetchThreads = async () => {
            try {
                const response = await axios.get(`${baseURL}/threads/`);
                const threadData = response.data;
                setThreads(threadData);

                if (threadData.length > 0) {
                    setSelectedThread({ id: threadData[0].thread_id, name: threadData[0].name });
                }
            } catch (error) {
                console.error("Error fetching threads:", error);
            }
        };

        fetchThreads();
    }, []);

    const handleSelectThread = (threadId, threadName) => {
        setSelectedThread({ id: threadId, name: threadName });
        setMessages([]);
    };

    const handleSendMessage = async (message, threadId, threadName) => {
        const newMessage = {
            id: uuidv4(),
            role: "Human",
            message_content: message,
            avatar: "https://example.com/human-avatar.png",
        };

        // Update messages with new human message
        setMessages((prevMessages) => [...prevMessages, newMessage]);
        setLoading(true);

        try {
            const response = await axios.post(`${baseURL}/run_ai_thread/`, {
                user_input: message,
                thread_id: threadId,
                thread_name: threadName,
            });

            const aiResponse = response.data.response;
            const aiSource = response.data.sources;

            const aiMessage = {
                id: uuidv4(),
                role: "AI",
                message_content: aiResponse,
                avatar: "https://example.com/ai-avatar.png",
                sources: aiSource,
            };
            setMessages((prevMessages) => [...prevMessages, aiMessage]);
            setSource(aiSource);
            console.log(setSource)
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
                <Sidebar onSelectThread={handleSelectThread} threads={threads} />
            </Sider>
            <Layout>
                <Content style={{ padding: '10px 10px', display: "flex", flexDirection: "column", backgroundColor: "#F8FAFC", flexGrow: 1 }}>
                    {selectedThread ? (
                        <Chat
                            selectedThread={selectedThread}
                            messages={messages}
                            setMessages={setMessages}
                        />
                    ) : (
                        <div>Select a thread to view the messages.</div>
                    )}
                </Content>
                <Footer style={{ padding: '5px 7px', backgroundColor: "#F8FAFC" }}>
                    {selectedThread && (
                        <Input
                            onSendMessage={handleSendMessage}
                            threadId={selectedThread.id}
                            threadName={selectedThread.name}
                        />
                    )}
                </Footer>
            </Layout>
        </Layout>
    );
};

export default MainLayout;
