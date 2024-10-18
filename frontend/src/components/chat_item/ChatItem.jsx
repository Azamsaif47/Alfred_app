import React, {useEffect, useRef, useState} from "react";
import axios from "axios";
import {message} from "antd";

const ChatItem = ({ thread, onSelectThread, selectedMenu, setSelectedMenu, setThreads, isSelected }) => {
    const menuRef = useRef(null);
    const baseURL = import.meta.env.VITE_API_URL;
    const [newThreadName, setNewThreadName] = useState(thread.name);
    const [isEditing, setIsEditing] = useState(false);
    const inputRef = useRef(null);

    const toggleMenu = () => {
        setSelectedMenu(selectedMenu === thread.thread_id ? null : thread.thread_id);
    };

    const handleClickOutside = (event) => {
        if (menuRef.current && !menuRef.current.contains(event.target)) {
            setSelectedMenu(null);
            if (isEditing) {
                setIsEditing(false);
            }
        }
    };
    useEffect(() => {

        const savedThreadId = localStorage.getItem('selectedThreadId');
        if (savedThreadId === thread.thread_id) {
            setSelectedMenu(thread.thread_id);
        }
    }, [thread.thread_id]);


    const handleDelete = async () => {
        try {
            const response = await axios.delete(`${baseURL}/delete_thread/`, {
                data: {
                    thread_id: thread.thread_id,
                    name: thread.name,
                },
            });
            setThreads((prevThreads) => prevThreads.filter((t) => t.thread_id !== thread.thread_id));
            message.success('Thread deleted successfully.');
        } catch (err) {
            message.error('Error deleting thread.');
        }
    };

    const handleUpdateThreadName = async () => {
        try {
            await axios.put(`${baseURL}/update_thread_name/`, {
                thread_id: thread.thread_id,
                new_name: newThreadName,
            });
            setThreads((prevThreads) =>
                prevThreads.map((t) =>
                    t.thread_id === thread.thread_id ? {...t, name: newThreadName} : t
                )
            );
            message.success('Thread name updated successfully.');
            setIsEditing(false);
        } catch (err) {
            message.error('Error updating thread name.');
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && isEditing) {
            e.preventDefault();
            handleUpdateThreadName();
        }
    };

    useEffect(() => {
        if (selectedMenu === thread.thread_id) {
            document.addEventListener("mousedown", handleClickOutside);
        } else {
            document.removeEventListener("mousedown", handleClickOutside);
        }

        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [selectedMenu]);

    useEffect(() => {
        if (isEditing) {
            inputRef.current.focus();
        }
    }, [isEditing]);

    return (
        <div
            className={`relative rounded-lg border border-slate-300 p-0.5 dark:border-slate-700 cursor-pointer flex justify-between items-center ${isSelected ? 'bg-[#E2E8F0] text-black' : 'text-black'}`} onClick={() => {
            // Prevent selecting if already selected
            if (!isSelected) {
                onSelectThread(thread.thread_id, thread.name);
            }
        }}

        >
            <div
                className="flex p-1 rounded-lg transition-colors duration-200"
            >
                {isEditing ? (
                    <input
                        ref={inputRef}
                        type="text"
                        value={newThreadName}
                        onChange={(e) => setNewThreadName(e.target.value)}
                        onKeyDown={handleKeyDown}
                        onClick={(e) => e.stopPropagation()}
                        className="border border-gray-300 rounded px-2 py-1"
                        placeholder="Enter new thread name"
                    />
                ) : (
                    thread.name
                )}
            </div>

            <div className="relative">
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        toggleMenu();
                    }}
                    className="text-slate-600 dark:text-slate-300"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth={1.5}
                        stroke="currentColor"
                        className="w-5 h-5"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M12 6.75v.008M12 12v.008m0 5.242v.008"
                        />
                    </svg>
                </button>

                {selectedMenu === thread.thread_id && (
                    <div
                        ref={menuRef}
                        className="absolute right-0 z-10 mt-2 w-28 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none dark:bg-slate-800"
                    >
                        <div className="py-1">
                            <button
                                className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700 w-full text-left"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setIsEditing(true);
                                }}
                            >
                                Edit
                            </button>
                            <button
                                className="block px-4 py-2 text-sm text-red-600 hover:bg-slate-100 dark:hover:bg-slate-700 w-full text-left"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleDelete();
                                }}
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ChatItem;