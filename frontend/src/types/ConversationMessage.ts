export interface ConversationMessage {
    sender: "user" | "agent"
    text: string;
}