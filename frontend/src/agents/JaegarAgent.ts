import type { AgentResponse } from "../types/AgentResponse";

class JaegarAgent {
    async respond(message: string): Promise<AgentResponse> {
        return {
            message: "Jaegar received your message.",
            state: "RESPONDING"
        };
    }
}

export default JaegarAgent;