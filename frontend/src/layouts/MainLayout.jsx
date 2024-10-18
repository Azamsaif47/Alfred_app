import { useEffect, useState } from 'react';
import { Layout } from 'antd';
import Sidebar from "../components/sidebar/Sidebar.jsx";
import { v4 as uuidv4 } from "uuid";
import axios from "axios";
import Input from "../components/input/Input.jsx";
import {Outlet, useNavigate, useParams } from "react-router-dom";

const { Sider, Content, Footer } = Layout;

const MainLayout = () => {
    const [selectedThread, setSelectedThread] = useState({id: null, name: null});
    const [isAIThinking, setIsAIThinking] = useState(false);
    const [messages, setMessages] = useState([]); // No initial AI message
    const [loading, setLoading] = useState(false);
    const [source, setSource] = useState([]);
    const baseURL = import.meta.env.VITE_API_URL;
    const [threads, setThreads] = useState([]);
    const [error, setError] = useState(null);
    const navigate = useNavigate()
    const threadId = useParams();
    console.log(`on top selected thread: ${JSON.stringify(threadId)}`);

    // Extracting the thread_id from the threadId object
    const { thread_id } = threadId;


    useEffect(() => {
        console.log("Updated source:", source);
    }, [source]);


    useEffect(() => {
    const fetchThreads = async () => {
        try {
            const response = await axios.get(`${baseURL}/threads/`);
            const threadData = response.data;
            setThreads(threadData);

            if (threadId) {
                const existingThread = threadData.find(t => t.thread_id === threadId);
                if (existingThread) {
                    setSelectedThread({ id: existingThread.thread_id, name: existingThread.name });
                }
            }
        } catch (error) {
            console.error("Error fetching threads:", error);
        }
    };

    fetchThreads();
}, [threadId]);

    console.log(threadId)
    const handleSelectThread = (threadId, threadName) => {
        console.log(`inside the function ${threadId}`)
        setSelectedThread({id: threadId, name: threadName});
        console.log(selectedThread.id)
        setMessages([]); // Reset messages when a new thread is selected
        navigate(`/thread/${threadId}`); // Update the URL with the selected threadId
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
        setIsAIThinking(true);

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
            console.log(setSource);
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

    const handleStartChat = async () => {
        console.log("the handle start function is called")
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${baseURL}/create_thread/`);
            const newThread = {thread_id: response.data.thread_id, name: response.data.name};

            setThreads((prevThreads) => [newThread, ...prevThreads]);

            handleSelectThread(newThread.thread_id, newThread.name);
        } catch (err) {
            setError("Error creating chat. Please try again.");
            console.error("Error creating chat:", err);
        } finally {
            setLoading(false);
            setIsAIThinking(false);
        }
    };


    const shouldRenderFooter = thread_id
    console.log(`the selected thread is ${shouldRenderFooter}`)

    return (
        <Layout style={{ height: "100vh" }}>
            <Sider width={250} style={{ background: "#E2E8F0" }}>
                <Sidebar
                    onSelectThread={handleSelectThread}
                    threads={threads}
                    onStartChat={handleStartChat}
                />
            </Sider>
            <Layout>
                <Content style={{
                    padding: '10px 10px',
                    display: "flex",
                    flexDirection: "column",
                    backgroundColor: "#F8FAFC",
                    flexGrow: 1
                }}>
                    <Outlet context={{
                        selectedThread,
                        messages,
                        setMessages,
                        isAIThinking,
                        handleStartChat
                    }} />
                </Content>

                {/* Conditionally render footer */}
                {shouldRenderFooter ? (
                    <Footer style={{ padding: '5px 7px', backgroundColor: "#F8FAFC" }}>
                        <Input
                            onSendMessage={handleSendMessage}
                            threadId={selectedThread.id}
                            threadName={selectedThread.name}
                        />
                    </Footer>
                ) : (
                    <div></div> // Empty div when no chat is selected
                )}
            </Layout>
        </Layout>
    );
};
export default MainLayout;