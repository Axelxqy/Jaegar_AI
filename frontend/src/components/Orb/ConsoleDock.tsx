import type { ConversationMessage } from "../../layouts/mainLayout"
import "./ConsoleDock.css"

interface ConsoleDockProps {
    messages: ConversationMessage[];
}

function ConsoleDock({ messages }: ConsoleDockProps) {
    return (
        <div className="console-dock">
            <div className="console-header">
                <span className="console-title">
                    Conversation Logs
                </span>
            </div>

            <div className="console-log">
                {messages.map((message, index) => (

                    <div className = {
                        message.sender === "user" ? "user-log":"agent-log"
                    } 
                    key = {index}
                    >
                        <span className = "log-speaker">
                            {message.sender === "user" ? "USER":"JAEGAR"}
                        </span>

                        <span className = "log-message">
                            {message.text}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    )

}

export default ConsoleDock;