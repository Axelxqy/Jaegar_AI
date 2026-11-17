import "./mainLayout.css";

import Orb from "../components/Orb/Orb";
import StatusDock from "../components/Orb/StatusDock";
import OrbStatus from "../components/Orb/OrbStatus";
import ConsoleDock from "../components/Orb/ConsoleDock";
import InputBar from "../components/Orb/InputBar";

import { useInteractionManager } from "../interaction/interactionManager";


function MainLayout() {

    const {
        messages,
        state,
        error,
        isProcessing,
        sendMessage,
    } = useInteractionManager();


    return (
        <div className="app">

            <div className="workspace">

                <div className="orb-area">

                    <Orb />

                    <OrbStatus
                        state={state}
                        error={error}
                    />

                </div>

                <div className="right-dock">

                    <StatusDock />

                    <ConsoleDock messages={messages} />

                </div>

            </div>

            <div className="input-panel">

                <InputBar
                    onSendMessage={sendMessage}
                    disabled={isProcessing}
                />

            </div>

        </div>
    );
}

export default MainLayout;