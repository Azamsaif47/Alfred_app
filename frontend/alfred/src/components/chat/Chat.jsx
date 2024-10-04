import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import ReactMarkdown from 'react-markdown';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import "./Chat.css";

const Chat = ({ chatId, messages, setMessages }) => {
    const messagesEndRef = useRef(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchMessages = async () => {
            if (chatId) {
                setLoading(true);
                setMessages([]);
                try {
                    const response = await axios.post(`http://127.0.0.1:9000/messages/`, {
                        thread_id: chatId,
                    });
                    setMessages(response.data);
                } catch (error) {
                    console.error("Error fetching messages:", error);
                } finally {
                    setLoading(false);
                }
            }
        };

        fetchMessages();
    }, [chatId, setMessages]);

    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages]);

    return (
        <div className="flex-1 space-y-6 rounded-xl bg-slate-200 p-4 text-sm leading-6 text-slate-900 shadow-sm dark:bg-slate-900 dark:text-slate-300 sm:text-base sm:leading-7">
            {loading ? (
                <div className="loading-dots">
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
            ) : messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full">
                    <UserOutlined className="text-6xl text-gray-400 mb-4" />
                    <p className="text-xl text-gray-500">
                        Start the conversation!
                    </p>
                </div>
            ) : (
                <div className="scrollable pb-4">
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex items-start ${msg.role === "AI" ? "justify-start" : "justify-end"} mb-4`}
                        >
                            {msg.role === "AI" && (
                                <RobotOutlined className="mr-2 h-8 w-8 text-gray-600"/>
                            )}
                            <div
                                className={`flex rounded-b-xl rounded-tr-xl p-4 ${
                                    msg.role === "AI"
                                        ? "bg-slate-50 dark:bg-slate-800"
                                        : "bg-blue-50 dark:bg-blue-800"
                                } sm:max-w-md md:max-w-2xl`}
                            >
                                <p><ReactMarkdown>{msg.message_content}</ReactMarkdown></p>
                            </div>
                            {msg.role === "Human" && (
                                <UserOutlined className="ml-2 h-8 w-8 text-gray-600"/>
                            )}
                        </div>
                    ))}
                    <div ref={messagesEndRef}/>
                </div>
            )}
        </div>
    );
};

export default Chat;
