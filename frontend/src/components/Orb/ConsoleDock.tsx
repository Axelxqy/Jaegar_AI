import "./ConsoleDock.css"

function ConsoleDock() {
    return (
        <div className="console-dock">
            <div className="console-header">
                <span className="console-title">
                    Conversation Logs
                </span>
            </div>

            <div className="console-log">
                <div className="user-log">
                    <span className="log-speaker">
                        YOU
                    </span>

                    <span className="log-message">
                        Hello Jaegar.
                    </span>
                </div>
                
                <div className="agent-log">
                    <span className="log-speaker">
                        JAEGAR
                    </span>

                    <span className="log-message">
                        Hello, How can I help you?
                    </span>
                </div>
            </div>
        </div>
    )

}

export default ConsoleDock;