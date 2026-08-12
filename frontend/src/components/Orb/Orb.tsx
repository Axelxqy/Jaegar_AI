import { Canvas } from "@react-three/fiber";
import ParticleSphere from "./ParticleSphere"
import "./Orb.css";

function Orb() {
    return (
        <div className="orb-container">
            
            <Canvas>

                <ParticleSphere />

            </Canvas>
            
        </div>
    );
}

export default Orb;