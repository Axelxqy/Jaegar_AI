import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import type { Particle } from "./Types.ts";

const particleCount = 750;
const sphereRadius = 2;

//Particle Texture
function createParticleTexture() {
    const canvas = document.createElement("canvas");

    canvas.width = 64;
    canvas.height = 64;

    //Get 2D tools
    const context = canvas.getContext("2d");

    if (!context) {
        throw new Error("Could not render 2D canvas context")
    }

    const center = 32;

    //Set Gradient starting from in towards out
    const gradient = context.createRadialGradient(
        center,
        center,
        0,
        center,
        center,
        32
    );

    //Color of Gradient
    gradient.addColorStop(0, "rgba(255, 255, 255, 1)");
    gradient.addColorStop(0.15, "rgba(255, 255, 255, 0.95)");
    gradient.addColorStop(0.35, "rgba(255, 255, 255, 0.35)");
    gradient.addColorStop(1, "rgba(255, 255, 255, 0)");

    context.fillStyle = gradient;
    context.fillRect(0, 0, 64, 64);

    //Draw Star Rays
    context.strokeStyle = "white";
    context.lineWidth = 2;

    context.beginPath();

    //Vertical Ray
    context.moveTo(center, 4);
    context.lineTo(center, 60);

    //Horizontal Ray
    context.moveTo(4, center);
    context.lineTo(60, center);

    context.stroke();

    //Convert into THREE.js texture
    return new THREE.CanvasTexture(canvas);
}

export default function ParticleSphere() {
    const pointsRef = useRef < THREE.Points | null > (null);

    const starTexture = useMemo(() => {
        return createParticleTexture();
    }, []);

    const { geometry, particles } = useMemo(() => {
        const particles: Particle[] = [];
        const positions = new Float32Array(particleCount * 3);

        const goldenAngle = Math.PI * (3 -Math.sqrt(5));

        for (let i = 0; i < particleCount; i++) {
            const y = 1 - (i / (particleCount - 1)) * 2;

            const radiusAtY = Math.sqrt(1 - y * y);

            const theta = goldenAngle * i;

            const x = Math.cos(theta) * radiusAtY;
            const z = Math.sin(theta) * radiusAtY;

            const position = {
                x: x * sphereRadius,
                y: y * sphereRadius,
                z: z * sphereRadius,
            }

            particles.push({
                position: { ...position },
                homePosition: { ...position },
                size: 1,
                brightness: 1
            })

            const index = i * 3;

            positions[index] = position.x;
            positions[index + 1] = position.y;
            positions[index + 2] = position.z;
        }

        const geometry = new THREE.BufferGeometry();

        geometry.setAttribute(
            "position",
            new THREE.BufferAttribute(positions, 3)
        );

        return {
            geometry,
            particles
        };
    }, []);

    useFrame((_, delta) => {
        if (!pointsRef.current)
            return;

        //Orb Rptation
        pointsRef.current.rotation.y += delta * 0.12;
        pointsRef.current.rotation.x += delta * 0.015;

        //Position Buffer
        const positionAttribute = 
            pointsRef.current.geometry.attributes.position;

        const array = 
            positionAttribute.array as Float32Array;

        //Particle Movements
        for (let i = 0; i < particles.length; i++) {
            const particle = particles[i];
            const index = i * 3;
            const time = performance.now() * 0.001;
            const ripple = 
                Math.sin(
                    time * 1.5 + 
                    i * 0.35
                ) * 0.015;

            const direction = new THREE.Vector3(
                particle.homePosition.x,
                particle.homePosition.y,
                particle.homePosition.z
            ).normalize();

            array[index] = 
                particle.homePosition.x + direction.x * ripple;

            array[index + 1] = 
                particle.homePosition.y + direction.y * ripple;

            array[index + 2] = 
                particle.homePosition.z + direction.z * ripple;
        }

        positionAttribute.needsUpdate = true;
    });

    return (
        <points
            ref = {pointsRef}
            geometry = {geometry}
        >
            <pointsMaterial
                color = "#ffffff"
                size = {0.1}
                sizeAttenuation
                transparent
                opacity = {0.9}
                depthWrite = {false}
                blending = {THREE.AdditiveBlending}
                map = {starTexture}
                alphaTest = {0.01}
            />
        </points>
    );
}

