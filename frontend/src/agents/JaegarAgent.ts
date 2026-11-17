import type { AgentResponse } from "../types/AgentResponse";

class JaegarAgent {
    private readonly API_URL = "http://localhost:8000/message";

    async respond(message: string): Promise<AgentResponse> {
        const response = await fetch(this.API_URL, {
            method: "POST",
            headers: {
                "content-type": "application/json",
            },
            body: JSON.stringify({ message }),
        });

        const data: unknown = await response.json();

        if (!response.ok) {
            const detail =
                typeof data === "object" &&
                data !== null &&
                "detail" in data &&
                typeof data.detail === "string"
                    ? data.detail
                    : "Backend request failed.";

            throw new Error(detail);
        }

        if (
            typeof data !== "object" ||
            data === null ||
            !("message" in data) ||
            typeof data.message !== "string"
        ) {
            throw new Error("Invalid response received from backend.");
        }

        return {
            message: data.message,
        };
    }
}

export default JaegarAgent;