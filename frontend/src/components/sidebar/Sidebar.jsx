import React, { useEffect, useState } from "react";
import axios from "axios";
import ChatItem from "../chat_item/ChatItem.jsx";
import { Button } from "antd";
import { MessageOutlined, LoadingOutlined } from '@ant-design/icons';
import {useNavigate} from "react-router-dom";
import "./Sidebar.css"


const Sidebar = ({ onSelectThread }) => {
    const [threads, setThreads] = useState([]);
    const baseURL = import.meta.env.VITE_API_URL;
    console.log(baseURL)
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedMenu, setSelectedMenu] = useState(null);
    const [selectedThreadId, setSelectedThreadId] = useState(null);
    const navigate = useNavigate();


    const handleSelectThread = (threadId, threadName) => {
        setSelectedThreadId(threadId);
        onSelectThread(threadId, threadName);
        navigate(`/thread/${threadId}`);
    };


    const renderPreviousChats = (threads) => {
        return threads.map((thread) => (
            <ChatItem
                key={thread.thread_id}
                thread={thread}
                onSelectThread={handleSelectThread}
                isSelected={selectedThreadId === thread.thread_id}
                selectedMenu={selectedMenu}
                setSelectedMenu={setSelectedMenu}
                setThreads={setThreads}
            />
        ));
    };
    useEffect(() => {
        const fetchThreads = async () => {
            try {
                const response = await axios.get(`${baseURL}/threads/`);
                console.log("Response data:", response.data); // Log the response

                // Check if response.data is an array and set it to state
                if (Array.isArray(response.data)) {
                    setThreads(response.data.reverse()); // Reverse the array before setting
                } else {
                    console.error("Expected an array but received:", response.data);
                }
            } catch (error) {
                console.error("Error fetching threads:", error);
            }
        };
        fetchThreads();
    }, []);

    const handleStartChat = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${baseURL}/create_thread/`);
            setThreads((prevThreads) => [
                {thread_id: response.data.thread_id, name: response.data.name},
                ...prevThreads,
            ]);
            console.log("New thread created:", response.data);

            onSelectThread(response.data.thread_id, response.data.name);
            navigate(`/thread/${response.data.thread_id}`);
        } catch (err) {
            setError("Error creating chat. Please try again.");
            console.error("Error creating chat:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <aside className="flex">
            <div
                className="flex h-[100svh] w-60 flex-col overflow-y-auto bg-slate-50 pt-8 dark:border-slate-700 dark:bg-slate-900 sm:h-[100vh] sm:w-64">
                <div className="flex px-4">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-7 w-7 text-blue-600"
                        fill="currentColor"
                        strokeWidth="1"
                        viewBox="0 0 24 24"
                    >
                    </svg>
                    <h2 className="px-5 text-lg font-medium text-slate-800 dark:text-slate-200">
                        Alfred
                        <span className="mx-2 rounded-full bg-blue-600 px-2 py-1 text-xs text-slate-200">
                        {threads.length}
                    </span>
                    </h2>
                </div>

                <div className="mx-2 mt-8">
                    <Button
                        onClick={handleStartChat}
                        className="flex w-full rounded-lg mb-2"
                        type="primary"
                        icon={loading ? <LoadingOutlined/> : <MessageOutlined/>}
                        loading={loading}
                    >
                        {loading ? "Creating..." : "New Chat"}
                    </Button>
                    {error && <p className="text-red-500 text-sm">{error}</p>}
                </div>

                <div
                    className="flex-1 space-y-4 custom-scroll overflow-y-auto border-b border-slate-300 px-2 py-4 dark:border-slate-700">
                    {renderPreviousChats(threads)}
                </div>

                <div className="w-full space-y-4 px-2 py-4">
                    <button
                        className="flex w-full gap-x-2 rounded-lg px-3 py-2 text-left text-sm font-medium text-slate-700 transition-colors duration-200 hover:bg-slate-200 focus:outline-none dark:text-slate-200 dark:hover:bg-slate-800">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-6 w-6"
                            viewBox="0 0 24 24"
                            strokeWidth="2"
                            stroke="currentColor"
                            fill="none"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                            <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"></path>
                            <path d="M12 10m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0"></path>
                            <path d="M6.168 18.849a4 4 0 0 1 3.832 -2.849h4a4 4 0 0 1 3.834 2.855"></path>
                        </svg>
                        User
                    </button>
                    <button
                        className="flex w-full gap-x-2 rounded-lg px-3 py-2 text-left text-sm font-medium text-slate-700 transition-colors duration-200 hover:bg-slate-200 focus:outline-none dark:text-slate-200 dark:hover:bg-slate-800">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-6 w-6"
                            viewBox="0 0 24 24"
                            strokeWidth="2"
                            stroke="currentColor"
                            fill="none"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                            <path
                                d="M19.875 6.27a2.225 2.225 0 0 1 1.125 1.948v7.284c0 .809 -.443 1.555 -1.158 1.948l-6.75 4.27a2.269 2.269 0 0 1 -2.184 0l-6.75 -4.27a2.225 2.225 0 0 1 -1.158 -1.948v-7.285c0 -.809 .443 -1.554 1.158 -1.947l6.75 -3.98a2.33 2.33 0 0 1 2.25 0l6.75 3.98h-.033z"
                            ></path>
                            <path d="M12 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0"></path>
                        </svg>
                        Settings
                    </button>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;