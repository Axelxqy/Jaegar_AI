import "./mainLayout.css";
import Orb from "../components/Orb/Orb"
import StatusDock from "../components/Orb/StatusDock"
import OrbStatus from "../components/Orb/OrbStatus"
import ConsoleDock from "../components/Orb/ConsoleDock"
import InputBar from "../components/Orb/InputBar"

function MainLayout() {
    return (
        <div className="app">
            
            <div className="workspace">

                <div className="orb-area">
                    <Orb />

                    <OrbStatus />
                </div>

                <div className="right-dock">
                    
                    <StatusDock />

                    <ConsoleDock />

                </div>

            </div>

            <div className="input-panel">
                
                <InputBar />

            </div>
        
        </div>
        
    )
}

export default MainLayout;