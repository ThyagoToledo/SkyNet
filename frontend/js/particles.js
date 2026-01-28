/**
 * Skynet 3D Particle System
 * Interactive particle visualization using Three.js
 */

class ParticleSystem {
    constructor(container) {
        this.container = container;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.particles = null;
        this.particleCount = 5000;
        this.currentMode = 'sphere';
        this.currentState = 'idle';
        this.time = 0;
        this.targetPositions = [];
        this.colors = [];
        this.baseColor = new THREE.Color(0x00ff66);
        this.accentColor = new THREE.Color(0x00cc44);

        // Animation parameters
        this.expansionFactor = 1;
        this.rotationSpeed = 0.001;
        this.pulseSpeed = 0.02;
        this.transitionProgress = 1;

        // Voice reactivity
        this.audioVolume = 0;
        this.volumeSmooth = 0;
        this.isUserSpeaking = false;

        this.init();
    }

    init() {
        // Scene setup
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a0a);
        this.scene.fog = new THREE.FogExp2(0x0a0a0a, 0.0008);

        // Camera setup
        this.camera = new THREE.PerspectiveCamera(
            75,
            window.innerWidth / window.innerHeight,
            0.1,
            2000
        );
        this.camera.position.z = 500;

        // Renderer setup
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.container.appendChild(this.renderer.domElement);

        // Create particles
        this.createParticles();

        // Add ambient light
        const ambientLight = new THREE.AmbientLight(0x404040);
        this.scene.add(ambientLight);

        // Event listeners
        window.addEventListener('resize', () => this.onResize());

        // Mouse interaction
        this.mouse = new THREE.Vector2();
        window.addEventListener('mousemove', (e) => this.onMouseMove(e));

        // Start animation
        this.animate();
    }

    createParticles() {
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(this.particleCount * 3);
        const colors = new Float32Array(this.particleCount * 3);
        const sizes = new Float32Array(this.particleCount);

        // Initialize particles in sphere formation
        for (let i = 0; i < this.particleCount; i++) {
            const i3 = i * 3;

            // Random sphere distribution
            const radius = 150 + Math.random() * 50;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos((Math.random() * 2) - 1);

            positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i3 + 2] = radius * Math.cos(phi);

            // Color gradient
            const color = this.baseColor.clone();
            color.lerp(this.accentColor, Math.random() * 0.3);
            colors[i3] = color.r;
            colors[i3 + 1] = color.g;
            colors[i3 + 2] = color.b;

            sizes[i] = Math.random() * 3 + 1;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        // Custom shader material
        const material = new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 },
                pixelRatio: { value: this.renderer.getPixelRatio() }
            },
            vertexShader: `
                attribute float size;
                varying vec3 vColor;
                uniform float time;
                
                void main() {
                    vColor = color;
                    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                    gl_PointSize = size * (300.0 / -mvPosition.z);
                    gl_Position = projectionMatrix * mvPosition;
                }
            `,
            fragmentShader: `
                varying vec3 vColor;
                
                void main() {
                    float r = distance(gl_PointCoord, vec2(0.5));
                    if (r > 0.5) discard;
                    
                    float alpha = 1.0 - smoothstep(0.3, 0.5, r);
                    gl_FragColor = vec4(vColor, alpha);
                }
            `,
            transparent: true,
            vertexColors: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        this.particles = new THREE.Points(geometry, material);
        this.scene.add(this.particles);

        // Store initial positions
        this.targetPositions = positions.slice();
    }

    setMode(mode) {
        this.currentMode = mode;
        this.transitionProgress = 0;
        this.calculateTargetPositions();
    }

    calculateTargetPositions() {
        const positions = this.particles.geometry.attributes.position.array;

        for (let i = 0; i < this.particleCount; i++) {
            const i3 = i * 3;
            let x, y, z;

            switch (this.currentMode) {
                case 'sphere':
                    const radius = 150 + Math.random() * 50;
                    const theta = Math.random() * Math.PI * 2;
                    const phi = Math.acos((Math.random() * 2) - 1);
                    x = radius * Math.sin(phi) * Math.cos(theta);
                    y = radius * Math.sin(phi) * Math.sin(theta);
                    z = radius * Math.cos(phi);
                    break;

                case 'atom':
                    const orbitRadius = 100 + (i % 4) * 40;
                    const orbitAngle = (i / this.particleCount) * Math.PI * 20;
                    const orbitTilt = (i % 3) * Math.PI / 3;
                    x = orbitRadius * Math.cos(orbitAngle);
                    y = orbitRadius * Math.sin(orbitAngle) * Math.cos(orbitTilt);
                    z = orbitRadius * Math.sin(orbitAngle) * Math.sin(orbitTilt);
                    break;

                case 'fireworks':
                    const burstRadius = Math.random() * 300;
                    const burstTheta = Math.random() * Math.PI * 2;
                    const burstPhi = Math.random() * Math.PI;
                    x = burstRadius * Math.sin(burstPhi) * Math.cos(burstTheta);
                    y = burstRadius * Math.sin(burstPhi) * Math.sin(burstTheta) - 100;
                    z = burstRadius * Math.cos(burstPhi);
                    break;

                case 'wave':
                    const waveX = (i % 100) * 5 - 250;
                    const waveZ = Math.floor(i / 100) * 5 - 125;
                    x = waveX;
                    y = Math.sin(waveX * 0.05) * 50 + Math.cos(waveZ * 0.05) * 50;
                    z = waveZ;
                    break;

                case 'helix':
                    const helixT = (i / this.particleCount) * Math.PI * 10;
                    const helixRadius = 100;
                    x = helixRadius * Math.cos(helixT);
                    y = (i / this.particleCount) * 400 - 200;
                    z = helixRadius * Math.sin(helixT);
                    break;

                case 'galaxy':
                    const arm = i % 3;
                    const armOffset = arm * (Math.PI * 2 / 3);
                    const galaxyRadius = Math.pow(Math.random(), 0.5) * 200;
                    const galaxyAngle = armOffset + galaxyRadius * 0.02 + Math.random() * 0.5;
                    x = galaxyRadius * Math.cos(galaxyAngle);
                    y = (Math.random() - 0.5) * 20 * (1 - galaxyRadius / 200);
                    z = galaxyRadius * Math.sin(galaxyAngle);
                    break;

                default:
                    x = positions[i3];
                    y = positions[i3 + 1];
                    z = positions[i3 + 2];
            }

            this.targetPositions[i3] = x;
            this.targetPositions[i3 + 1] = y;
            this.targetPositions[i3 + 2] = z;
        }
    }

    setState(state) {
        this.currentState = state;

        switch (state) {
            case 'idle':
                this.rotationSpeed = 0.001;
                this.pulseSpeed = 0.02;
                this.expansionFactor = 1;
                this.setColors(0x00ff66, 0x00aa44);
                break;

            case 'listening':
                this.rotationSpeed = 0.002;
                this.pulseSpeed = 0.05;
                this.expansionFactor = 1.1;
                this.setColors(0x00ff88, 0x00dd66);
                break;

            case 'thinking':
                this.rotationSpeed = 0.005;
                this.pulseSpeed = 0.1;
                this.expansionFactor = 0.9;
                this.setColors(0xffaa00, 0xff6600);
                break;

            case 'speaking':
                this.rotationSpeed = 0.003;
                this.pulseSpeed = 0.08;
                this.expansionFactor = 1.2;
                this.setColors(0x44ff88, 0x00ff66);
                break;
        }
    }

    setColors(primaryHex, secondaryHex) {
        this.baseColor = new THREE.Color(primaryHex);
        this.accentColor = new THREE.Color(secondaryHex);

        const colors = this.particles.geometry.attributes.color.array;

        for (let i = 0; i < this.particleCount; i++) {
            const i3 = i * 3;
            const color = this.baseColor.clone();
            color.lerp(this.accentColor, Math.random() * 0.5);
            colors[i3] = color.r;
            colors[i3 + 1] = color.g;
            colors[i3 + 2] = color.b;
        }

        this.particles.geometry.attributes.color.needsUpdate = true;
    }

    onMouseMove(event) {
        this.mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
        this.mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
    }

    onResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        this.time += 0.016;

        // Smooth volume changes
        this.volumeSmooth += (this.audioVolume - this.volumeSmooth) * 0.1;

        // Apply volume-based effects when user is speaking
        const volumeEffect = this.isUserSpeaking ? this.volumeSmooth * 50 : 0;

        const positions = this.particles.geometry.attributes.position.array;

        // Smooth transition to target positions
        if (this.transitionProgress < 1) {
            this.transitionProgress += 0.02;

            for (let i = 0; i < positions.length; i++) {
                positions[i] += (this.targetPositions[i] - positions[i]) * 0.05;
            }

            this.particles.geometry.attributes.position.needsUpdate = true;
        }

        // Apply animations based on mode
        for (let i = 0; i < this.particleCount; i++) {
            const i3 = i * 3;

            // Pulse effect - enhanced by volume
            const basePulse = Math.sin(this.time * this.pulseSpeed + i * 0.01) * 5;
            const pulse = basePulse + volumeEffect;

            // Add slight movement - more when volume is higher
            const moveMult = 0.1 + volumeEffect * 0.02;
            positions[i3] += Math.sin(this.time + i) * moveMult;
            positions[i3 + 1] += Math.cos(this.time + i) * moveMult;
            positions[i3 + 2] += Math.sin(this.time * 0.5 + i) * moveMult;

            // Apply expansion - react to voice volume
            const dist = Math.sqrt(
                positions[i3] ** 2 +
                positions[i3 + 1] ** 2 +
                positions[i3 + 2] ** 2
            );

            // Expand/contract based on volume
            const volumeExpansion = this.isUserSpeaking ? 1 + this.volumeSmooth * 3 : 1;

            if (dist > 0) {
                const targetDist = dist * this.expansionFactor * volumeExpansion;
                const factor = 1 + (targetDist - dist) / dist * 0.01;
                positions[i3] *= factor;
                positions[i3 + 1] *= factor;
                positions[i3 + 2] *= factor;
            }
        }

        this.particles.geometry.attributes.position.needsUpdate = true;

        // Rotate particles - faster when volume high
        const volumeRotation = this.isUserSpeaking ? this.volumeSmooth * 0.01 : 0;
        this.particles.rotation.y += this.rotationSpeed + volumeRotation;
        this.particles.rotation.x = this.mouse.y * 0.2;

        // Camera follows mouse slightly
        this.camera.position.x += (this.mouse.x * 100 - this.camera.position.x) * 0.02;
        this.camera.position.y += (this.mouse.y * 50 - this.camera.position.y) * 0.02;
        this.camera.lookAt(0, 0, 0);

        // Update shader time
        this.particles.material.uniforms.time.value = this.time;

        this.renderer.render(this.scene, this.camera);
    }

    // Trigger effects for specific events
    triggerExplosion() {
        this.expansionFactor = 2;
        setTimeout(() => {
            this.expansionFactor = 1;
        }, 500);
    }

    triggerImplosion() {
        this.expansionFactor = 0.3;
        setTimeout(() => {
            this.expansionFactor = 1;
        }, 500);
    }

    triggerColorFlash(hexColor) {
        const originalBase = this.baseColor.clone();
        const originalAccent = this.accentColor.clone();

        this.setColors(hexColor, hexColor);

        setTimeout(() => {
            this.baseColor = originalBase;
            this.accentColor = originalAccent;
        }, 200);
    }

    // Voice reactivity methods
    setVolume(volume) {
        this.audioVolume = Math.min(1, Math.max(0, volume * 10));  // Normalize
    }

    setSpeaking(isSpeaking) {
        this.isUserSpeaking = isSpeaking;
        if (!isSpeaking) {
            this.audioVolume = 0;
        }
    }
}

// Export for use in other files
window.ParticleSystem = ParticleSystem;
