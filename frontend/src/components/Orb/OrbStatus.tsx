import type { AgentState } from "../../types/AgentResponse";
import "./OrbStatus.css";

interface OrbStatusProps {
    state: AgentState;
    error: string | null;
}

function OrbStatus({ state, error }: OrbStatusProps) {

    const statusText: Record<AgentState, string> = {
        IDLE: "IDLE",
        THINKING: "THINKING",
        RESPONDING: "RESPONDING",
        ERROR: "ERROR",
    };

    return (
        <div className="orb-status">

            <span className="status-text">
                {state === "ERROR" && error
                    ? `${statusText[state]}: ${error}`
                    : statusText[state]}
            </span>

        </div>
    );
}

export default OrbStatus;