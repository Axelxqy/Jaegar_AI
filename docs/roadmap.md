Jaegar_AI RoadMap
----------------------------------------------
Phase 1: UI and Desktop Windows Development
- Design a preferred format for Jaegar AI
- Implement it using Tauri 
- User-prood it (testing if everything is in place)

    1.1
        React
        CSS

        Get the layout working:

        Fullscreen window
        Left/right panels
        Input area
        Logs
        General UI

    1.2
        Replace the CSS orb with a 3D particle orb:

        React
        React Three Fiber
        Three.js

        At this point, the orb is still just an idle animation.

    1.3
        Connect it to the AI's state.

        For example:

        Idle
            ↓
        Slow breathing

        Listening
            ↓
        Surface ripples

        Thinking
            ↓
        Particle swirl

        Speaking
            ↓
        Voice-reactive waves

        Executing
            ↓
        Energy pulses

        The orb becomes a visualization of what Jaegar is doing internally, rather than a decorative animation.

Phase 2: Agent Interaction with User (me)
- Animate all agent interactions (idle, speaking, listening, thinking)

Phase 3: Backend Integration
- Link backend to Jaegar
- Test and ensure it works

...