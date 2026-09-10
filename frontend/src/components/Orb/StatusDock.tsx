import "./StatusDock.css";

function StatusDock() {
    return (
        <div className="status-dock">
            <div className="status-dock-header">
                <span className="status-dock-title">
                    STATUS
                </span>

                <button className="status-dock-toggle">
                    -
                </button>
            </div>

            <div className="status-dock-content">
                
                <div className="status-item">
                    <span className="status-label">
                        Agent
                    </span>

                    <span className="status-value">
                        Offline
                    </span>
                </div>
                
                <div className="status-item">
                    <span className="status-label">
                        Connection
                    </span>

                    <span className="status-value">
                        -
                    </span>
                </div>
            </div>
            
        </div>
    );

}

export default StatusDock;