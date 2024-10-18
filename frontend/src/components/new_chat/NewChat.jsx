import { Button } from 'antd';
import { MessageOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import { useOutletContext } from 'react-router-dom';// Import the hook
import 'antd/dist/reset.css'; // Import Ant Design styles
import './NewChat.css'; // Import the CSS file

const NewChat = () => {
  const { handleStartChat } = useOutletContext();
  const { threadId } = useParams();
  return (
    <div className="container">
      <div className="card">
        <div className="header">
          <img
            src="https://via.placeholder.com/40" // Replace with your image URL
            alt="Avatar"
            className="avatar"
          />
          <h3 className="title">Alfred</h3>
        </div>
        <div className="footer">
          <Button
            type="primary"
            icon={<MessageOutlined />}
            size="large"
            onClick={handleStartChat}
          >
            Start Chat
          </Button>
        </div>
      </div>
    </div>
  );
};

export default NewChat;
