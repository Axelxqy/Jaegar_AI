export type AgentState = 
    | "IDLE" 
    | "THINKING" 
    | "RESPONDING";

export interface AgentResponse {
    message: string;
    state: AgentState;
}