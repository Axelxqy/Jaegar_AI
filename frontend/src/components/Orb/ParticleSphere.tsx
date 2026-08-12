import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import type { Particle } from "./Types.ts";

const particleCount = 500;
const sphereRadius = 1.2;

export default function ParticleSphere() {
    const pointsRef = useRef < THREE.Points | null > (null);

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
                size = {0.035}
                sizeAttenuation
                transparent
                opacity = {0.9}
                depthWrite = {false}
                blending = {THREE.AdditiveBlending}
            />
        </points>
    );
}

