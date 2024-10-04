import React, { useState } from "react";

const Input = ({ onSendMessage, threadId, threadName }) => {
    const [inputValue, setInputValue] = useState("");

    // Handle the form submission
    const handleSubmit = (e) => {
        e.preventDefault();
        if (inputValue.trim() && threadId && threadName) {
            onSendMessage(inputValue, threadId, threadName); // Pass the inputValue along with threadId and threadName
            setInputValue(""); // Clear the input after sending
        } else {
            console.error("Thread ID or Thread Name is missing");
        }
    };

    // Handle key down events
    const handleKeyDown = (e) => {
        if (e.key === "Enter") {
            if (e.shiftKey) {
                // Allow new line
                return;
            }
            // Prevent the default action (which would add a new line)
            e.preventDefault();
            handleSubmit(e); // Call submit function
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <label htmlFor="chat-input" className="sr-only">
                Enter your prompt
            </label>
            <div className="relative">
                <textarea
                    id="chat-input"
                    className="block w-full resize-none rounded-xl border-none bg-slate-200 p-4 pr-16 text-sm text-slate-900 shadow-md focus:outline-none focus:ring-2 focus:ring-blue-600 sm:text-base"
                    placeholder="Enter your prompt"
                    rows="1"
                    value={inputValue} // Controlled input
                    onChange={(e) => setInputValue(e.target.value)} // Update state
                    onKeyDown={handleKeyDown} // Add the key down event handler
                    required
                ></textarea>
                <button
                    type="submit"
                    className="absolute bottom-2 right-2.5 rounded-lg bg-blue-700 p-2 text-sm font-medium text-slate-200 hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300 sm:text-base"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-6 w-6"
                        aria-hidden="true"
                        viewBox="0 0 24 24"
                        strokeWidth="2"
                        stroke="currentColor"
                        fill="none"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
                        <path d="M10 14l11 -11"></path>
                        <path
                            d="M21 3l-6.5 18a.55 .55 0 0 1 -1 0l-3.5 -7l-7 -3.5a.55 .55 0 0 1 0 -1l18 -6.5"
                        ></path>
                    </svg>
                    <span className="sr-only">Send message</span>
                </button>
            </div>
        </form>
    );
};

export default Input;
