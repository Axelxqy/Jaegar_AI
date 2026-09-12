export interface Point3D {
    x: number;
    y: number;
    z: number;
}

export interface Particle {
    position: Point3D;
    homePosition: Point3D;
    size: number;
    brightness: number;
}

export interface ConversationMessage {
    sender: "user" | "agent";
    text: string;
}