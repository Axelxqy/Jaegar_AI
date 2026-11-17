export type AgentState =
    | "IDLE"
    | "THINKING"
    | "RESPONDING"
    | "ERROR";

export interface AgentResponse {
    message: string;
}