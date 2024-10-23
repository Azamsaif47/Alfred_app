import React,{ useEffect, useRef, useState } from "react";
import axios from "axios";
import ReactMarkdown from 'react-markdown';
import {Button, Tooltip, Modal } from 'antd'
import { UserOutlined, RobotOutlined, InfoCircleOutlined,FilePdfOutlined } from '@ant-design/icons';
import {useOutletContext, useParams} from "react-router-dom";
import "./Chat.css";
import remarkGfm from 'remark-gfm';

const Chat = () => {
    const { messages = [], setMessages } = useOutletContext();
    const { thread_id } = useParams();
    const baseURL = import.meta.env.VITE_API_URL;
    const messagesEndRef = useRef(null);
    const [loading, setLoading] = useState(false);
    const [open, setOpen] = useState(false);
    const [selectedSource, setSelectedSource] = useState(null);

    const handleSourceClick = (source) => {
        setSelectedSource(source.page_content);
        setOpen(true);
    };


    const closeModal = () => {
        setOpen(false);
        setSelectedSource(null);
    };

    useEffect(() => {
        const fetchMessages = async () => {
            if (thread_id) {
                setLoading(true);
                try {
                    const response = await axios.post(`${baseURL}/messages/`, {
                        thread_id: thread_id,
                    });

                    // Step 1: Create a mapping of sources by message_id
                    const sourceMap = {};

                    // Populate the sourceMap with sources
                    response.data.sources.forEach(source => {
                        const { message_id, source: sourceName, page_content } = source;

                        // Initialize the array for this message_id if it doesn't exist
                        if (!sourceMap[message_id]) {
                            sourceMap[message_id] = [];
                        }

                        // Push the source object to the array, keeping both page_content and metadata.source
                        sourceMap[message_id].push({
                            page_content: page_content || '', // Direct access to page_content for modal display
                            metadata: {
                                source: sourceName || '', // Store source name in metadata for title
                            },
                        });
                    });

                    // Step 2: Process the response data to merge messages with their sources
                    const messagesWithMetadata = response.data.response.map((message, index) => {
                        const msgObj = {
                            ...message,
                            id: message.id || index, // Assign an id if not present
                            sources: [], // Initialize sources as an empty array
                        };

                        // Check if the message is from AI
                        if (message.role === "AI") {
                            // Use the message_id to find corresponding sources
                            const sourcesForMessage = sourceMap[message.message_id]; // Match on message_id
                            if (sourcesForMessage) {
                                msgObj.sources = sourcesForMessage; // Merge sources with message
                            }
                        }

                        return msgObj; // Return the processed message object
                    });

                    // Update state with the processed messages
                    setMessages(messagesWithMetadata);
                } catch (error) {
                    console.error("Error fetching messages:", error);
                } finally {
                    setLoading(false);
                }
            }
        };

        fetchMessages();
    }, [thread_id, setMessages]);





    const handleJsonDisplay = (jsonData) => {
        alert(JSON.stringify(jsonData, null, 2));
    };

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
                                className={`relative rounded-b-xl rounded-tr-xl p-4 ${
                                    msg.role === "AI" ? "bg-slate-50 dark:bg-slate-800" : "bg-blue-50 dark:bg-blue-800"
                                } sm:max-w-md md:max-w-2xl`}
                            >
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.message_content}</ReactMarkdown>

                                {msg.sources && msg.sources.length > 0 && (
                                    <>
                                        <div className="mt-4">
                                            <span className="font-semibold">Source</span>
                                            <div className="border-t border-gray-300 mt-1"></div>
                                        </div>

                                        <div className="mt-2 flex space-x-2"> {/* Use flex container for buttons */}
                                            {msg.sources.map((source, index) => {
                                                return (
                                                    <Tooltip
                                                        key={index}
                                                        title={source.metadata.source.split("\\").pop()} // Display the file name in the tooltip
                                                        placement="top"
                                                    >
                                                        <Button
                                                            type="primary"
                                                            size="small" // Set button size to small
                                                            className="flex items-center"
                                                            onClick={() => handleSourceClick(source)}
                                                            style={{
                                                                backgroundColor: '#1890ff', // Ant Design primary color
                                                                borderColor: '#1890ff',
                                                                borderRadius: '5px', // Match border color to primary
                                                                color: 'white', // Set text color to white
                                                                maxWidth: '150px', // Set a smaller maximum width
                                                                overflow: 'hidden',
                                                                whiteSpace: 'nowrap', // Keep text on one line
                                                                textOverflow: 'ellipsis', // Add ellipsis for overflow text
                                                                marginRight: '8px', // Add space between buttons
                                                                padding: '6px 8px', // Add padding to the button (top-bottom, left-right)
                                                                display: 'inline-flex', // Use inline-flex for proper alignment
                                                                alignItems: 'center', // Center align items
                                                            }}
                                                        >
                                                            <FilePdfOutlined className="mr-1"/>
                                                            <span style={{
                                                                flex: '1 1 auto', // Allow it to grow and shrink
                                                                overflow: 'hidden', // Hide overflow
                                                                textOverflow: 'ellipsis', // Show ellipsis
                                                                whiteSpace: 'nowrap', // Prevent text wrap
                                                            }}>{source.metadata.source.split("\\").pop()}</span>
                                                        </Button>
                                                    </Tooltip>
                                                );
                                            })}
                                        </div>

                                    </>
                                )}

                                {msg.role === "AI" && (
                                    <InfoCircleOutlined
                                        className="absolute top-2 right-2 cursor-pointer"
                                        onClick={handleJsonDisplay}
                                    />
                                )}

                                {open && selectedSource && (
                                    <Modal
                                        title="Source Content"
                                        open={open}
                                        onOk={closeModal}
                                        onCancel={closeModal}

                                    >
                                        <p>{selectedSource}</p>
                                    </Modal>
                                )}
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