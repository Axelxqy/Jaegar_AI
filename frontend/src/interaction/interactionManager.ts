import { useRef, useState } from "react";

import JaegarAgent from "../agents/JaegarAgent";
import type { AgentState } from "../types/AgentResponse";
import type { ConversationMessage } from "../types/ConversationMessage"

export function useInteractionManager() {
    const [messages, setMessages] = useState<ConversationMessage[]>([]);
    const [state, setState] = useState<AgentState>("IDLE");
    const [error, setError] = useState<string | null>(null);
    const agent = useRef(new JaegarAgent());
    const requestInFlight = useRef(false);
    const [isProcessing, setIsProcessing] = useState(false);

    async function sendMessage(text: string): Promise<void> {
        const message = text.trim();

        if(!message || requestInFlight.current) {
            return;
        }

        requestInFlight.current = true;
        setIsProcessing(true);

        setError(null);

        setMessages((currentMessages) => [
            ...currentMessages,
            {
                sender: "user",
                text: message,
            },
        ]);

        setState("THINKING");

        try {
            const response = await agent.current.respond(message);

            setState("RESPONDING");

            setMessages((currentMessages) => [
                ...currentMessages,
                {
                    sender: "agent",
                    text: response.message,
                },
            ]);

            setState("IDLE");

        } catch (error) {
            const errorMessage = 
                error instanceof Error
                    ? error.message
                    : "An unexpected interaction error occurred.";

            setError(errorMessage);

            setState("ERROR");

        } finally {
            requestInFlight.current = false;
            setIsProcessing(false);
        }
    }

    return {
        messages,
        state,
        error,
        isProcessing,
        sendMessage,
    };
}