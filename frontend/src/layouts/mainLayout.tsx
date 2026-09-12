import { useState } from "react";
import "./mainLayout.css";

import Orb from "../components/Orb/Orb"
import StatusDock from "../components/Orb/StatusDock"
import OrbStatus from "../components/Orb/OrbStatus"
import ConsoleDock from "../components/Orb/ConsoleDock"
import InputBar from "../components/Orb/InputBar"

export interface ConversationMessage {
    sender: "user" | "agent";
    text: string;
}

function MainLayout() {
    // Messaging (Inout) Function
    const [messages, setMessages] = useState<ConversationMessage[]>([]);

    function handleSendMessage(text: string) {
        if (!text.trim()) {
            return;
        }

        const newMessage: ConversationMessage = {
            sender:"user",
            text: text,
        };

        setMessages((currentMessages) => [
            ...currentMessages,
            newMessage,
        ])
    }

    return (
        <div className="app">
            
            <div className="workspace">

                <div className="orb-area">
                    <Orb />

                    <OrbStatus />
                </div>

                <div className="right-dock">
                    
                    <StatusDock />

                    <ConsoleDock messages={messages} />

                </div>

            </div>

            <div className="input-panel">
                
                <InputBar onSendMessage={handleSendMessage} />

            </div>
        
        </div>
        
    )
}

export default MainLayout;