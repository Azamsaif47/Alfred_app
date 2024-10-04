import React, { useState } from 'react';
import { Layout } from 'antd';
import Sidebar from "../components/sidebar/Sidebar.jsx";
import Chat from "../components/chat/Chat.jsx";

const { Sider, Content } = Layout;

const MainLayout = () => {
    const [currentChat, setCurrentChat] = useState('Chat 1'); // Default selected chat

    const handleSelectChat = (chatId) => {
        setCurrentChat(chatId); // Update the current chat when a chat is selected
    };

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Sider width={250} style={{ background: '#f0f2f5', height: '100vh', position: 'fixed' }}>
                <Sidebar onSelectChat={handleSelectChat} /> {/* Pass the chat selection handler */}
            </Sider>
            <Layout style={{ marginLeft: 250 }}>
                <Content style={{ margin: '0 16px', overflow: 'initial' }}>
                    <div style={{ padding: 10, background: '#fff', minHeight: '100vh', overflowY: 'auto' }}>
                        <Chat chatId={currentChat} /> {/* Pass the selected chat ID to the Chat component */}
                    </div>
                </Content>
            </Layout>
        </Layout>
    );
};

export default MainLayout;
