import { useEffect, useState } from 'react';
import {Layout, message} from 'antd';
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
    const [source, setSource] = useState([]);
    const baseURL = import.meta.env.VITE_API_URL;
    const [threads, setThreads] = useState([]);
    const navigate = useNavigate()
    const threadId = useParams();
    const { thread_id } = threadId;

    useEffect(() => {
        const savedThread = localStorage.getItem("selectedThread");
        if (savedThread) {
            setSelectedThread(JSON.parse(savedThread)); // Set state from localStorage
        }
    }, []);



    useEffect(() => {
    }, [source]);


    useEffect(() => {
        const fetchThreads = async () => {
            try {
                const response = await axios.get(`${baseURL}/threads/`);
                const threadData = response.data;
                setThreads(threadData);
            } catch (error) {
                console.error("Error fetching threads:", error);
            }
        };

        fetchThreads();
    }, []);

    const handleSelectThread = (thread_id) => {
        setMessages([]); // Clear messages when a new thread is selected
        setSelectedThread((prevSelectedThread) => {
            const updatedThread = { ...prevSelectedThread, id: thread_id };
            // Save the selected thread to localStorage
            localStorage.setItem("selectedThread", JSON.stringify(updatedThread));
            return updatedThread;
        });
    };

    useEffect(() => {
        if (selectedThread.id) { // Only fetch if thread_id is valid
            const fetchThreadName = async () => {
                try {
                    const response = await axios.get(`${baseURL}/threads/`);
                    const threadData = response.data;

                    // Find the thread with the matching thread_id
                    const foundThread = threadData.find(thread => thread.thread_id === selectedThread.id);

                    // If thread is found, update selectedThread state
                    if (foundThread) {
                        setSelectedThread({ id: foundThread.thread_id, name: foundThread.name });
                    } else {
                        console.error("Thread not found");
                    }
                } catch (error) {
                    console.error("Error fetching threads:", error);
                }
            };

            fetchThreadName();
        }
    }, [selectedThread.id]);

    const handleSendMessage = async (message, threadId, threadName) => {
        const newMessage = {
            id: uuidv4(),
            role: "Human",
            message_content: message,
            avatar: "https://example.com/human-avatar.png",
        };

        setMessages((prevMessages) => [...prevMessages, newMessage]);
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
        } catch (error) {
            console.error("Error sending message:", error);

            const errorMessage = {
                id: uuidv4(),
                role: "AI",
                message_content: "Sorry, something went wrong. Please try again.",
                avatar: "https://example.com/error-avatar.png",
            };

            setMessages((prevMessages) => [...prevMessages, errorMessage]);
        }
    };

    const handleStartChat = async () => {
        try {
            const response = await axios.post(`${baseURL}/create_thread/`);
            const newThread = {thread_id: response.data.thread_id, name: response.data.name};

            setThreads((prevThreads) => [newThread, ...prevThreads]);

            handleSelectThread(newThread.thread_id, newThread.name);
            navigate(`/thread/${newThread.thread_id}`);
            message.success('Chat created successfully.');
        } catch (err) {
            console.error("Error creating chat:", err);
        } finally {
            setIsAIThinking(false);
        }
    };

    const shouldRenderFooter = thread_id
    return (
        <Layout style={{ height: "100vh" }}>
            <Sider width={250} style={{ background: "#E2E8F0" }}>
                <Sidebar
                    onSelectThread={handleSelectThread}
                    threads={threads}
                    threadId ={selectedThread.id}
                    threadName={selectedThread.name}
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
                {shouldRenderFooter ? (
                    <Footer style={{ padding: '5px 7px',marginBottom:'8px', backgroundColor: "#F8FAFC" }}>
                        <Input
                            onSendMessage={handleSendMessage}
                            threadId={selectedThread.id}
                            threadName={selectedThread.name}
                        />
                    </Footer>
                ) : (
                    <div></div>
                )}
            </Layout>
        </Layout>
    );
};
export default MainLayout;