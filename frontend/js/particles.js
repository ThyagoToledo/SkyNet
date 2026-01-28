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
        this.particleCount = 15000; // Mais partículas para esfera densa
        this.currentMode = 'sphere';
        this.currentState = 'idle';
        this.time = 0;
        this.targetPositions = [];
        this.originalPositions = []; // Posições originais para transições
        this.colors = [];
        this.baseColor = new THREE.Color(0xaa66ff); // Roxo claro
        this.accentColor = new THREE.Color(0x8844cc); // Violeta

        // Animation parameters
        this.expansionFactor = 1;
        this.rotationSpeed = 0.001;
        this.pulseSpeed = 0.02;
        this.transitionProgress = 1;
        this.transitionSpeed = 0.03;

        // Voice reactivity
        this.audioVolume = 0;
        this.volumeSmooth = 0;
        this.isUserSpeaking = false;

        // Intro animation state
        this.introAnimationDone = false;
        this.introPhase = 'sphere'; // 'sphere', 'text', 'back_to_sphere'

        // SKYNET text coordinates
        this.skynetTextCoords = [];

        this.init();
    }

    init() {
        // Scene setup
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000000); // Fundo preto puro
        this.scene.fog = new THREE.FogExp2(0x000000, 0.0005);

        // Camera setup
        this.camera = new THREE.PerspectiveCamera(
            75,
            window.innerWidth / window.innerHeight,
            0.1,
            2000
        );
        this.camera.position.z = 400;

        // Renderer setup
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.container.appendChild(this.renderer.domElement);

        // Generate SKYNET text coordinates
        this.generateSkynetTextCoords();

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

        // Start intro animation after 2 seconds
        this.startIntroSequence();
    }

    generateSkynetTextCoords() {
        // Gerar coordenadas para formar "SKYNET" com partículas
        const letters = {
            'S': [
                [0, 0], [1, 0], [2, 0], [3, 0],
                [0, 1],
                [0, 2], [1, 2], [2, 2], [3, 2],
                [3, 3],
                [0, 4], [1, 4], [2, 4], [3, 4]
            ],
            'K': [
                [0, 0], [0, 1], [0, 2], [0, 3], [0, 4],
                [3, 0], [2, 1], [1, 2], [2, 3], [3, 4]
            ],
            'Y': [
                [0, 0], [1, 1], [2, 2], [3, 1], [4, 0],
                [2, 3], [2, 4]
            ],
            'N': [
                [0, 0], [0, 1], [0, 2], [0, 3], [0, 4],
                [1, 1], [2, 2], [3, 3],
                [4, 0], [4, 1], [4, 2], [4, 3], [4, 4]
            ],
            'E': [
                [0, 0], [1, 0], [2, 0], [3, 0],
                [0, 1],
                [0, 2], [1, 2], [2, 2],
                [0, 3],
                [0, 4], [1, 4], [2, 4], [3, 4]
            ],
            'T': [
                [0, 0], [1, 0], [2, 0], [3, 0], [4, 0],
                [2, 1], [2, 2], [2, 3], [2, 4]
            ]
        };

        const word = 'SKYNET';
        const scale = 15;
        const spacing = 5 * scale;
        const totalWidth = word.length * spacing;
        const startX = -totalWidth / 2;

        this.skynetTextCoords = [];

        for (let i = 0; i < word.length; i++) {
            const letter = letters[word[i]];
            const offsetX = startX + i * spacing;

            for (const [x, y] of letter) {
                // Adicionar várias partículas por ponto para mais densidade
                for (let j = 0; j < 8; j++) {
                    this.skynetTextCoords.push({
                        x: offsetX + x * scale + (Math.random() - 0.5) * 8,
                        y: (2 - y) * scale + (Math.random() - 0.5) * 8,
                        z: (Math.random() - 0.5) * 20
                    });
                }
            }
        }
    }

    createParticles() {
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(this.particleCount * 3);
        const colors = new Float32Array(this.particleCount * 3);
        const sizes = new Float32Array(this.particleCount);

        // Initialize particles in dense sphere formation
        for (let i = 0; i < this.particleCount; i++) {
            const i3 = i * 3;

            // Esfera mais densa e fechada
            const radius = 100 + Math.random() * 30; // Raio menor e mais uniforme
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos((Math.random() * 2) - 1);

            positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i3 + 2] = radius * Math.cos(phi);

            // Color gradient - roxo/violeta
            const color = this.baseColor.clone();
            color.lerp(this.accentColor, Math.random() * 0.5);
            colors[i3] = color.r;
            colors[i3 + 1] = color.g;
            colors[i3 + 2] = color.b;

            sizes[i] = Math.random() * 2 + 0.5; // Partículas menores
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
                    gl_PointSize = size * (250.0 / -mvPosition.z);
                    gl_Position = projectionMatrix * mvPosition;
                }
            `,
            fragmentShader: `
                varying vec3 vColor;
                
                void main() {
                    float r = distance(gl_PointCoord, vec2(0.5));
                    if (r > 0.5) discard;
                    
                    float alpha = 1.0 - smoothstep(0.2, 0.5, r);
                    float glow = exp(-r * 3.0) * 0.5;
                    gl_FragColor = vec4(vColor + glow, alpha);
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
        this.originalPositions = positions.slice();
    }

    startIntroSequence() {
        // Fase 1: Mostrar esfera por 2 segundos
        setTimeout(() => {
            this.introPhase = 'text';
            this.setMode('skynet_text');
        }, 2000);

        // Fase 2: Mostrar texto por 3 segundos, depois voltar à esfera
        setTimeout(() => {
            this.introPhase = 'back_to_sphere';
            this.setMode('sphere');
            this.introAnimationDone = true;
        }, 5000);
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
                    const radius = 100 + Math.random() * 30;
                    const theta = Math.random() * Math.PI * 2;
                    const phi = Math.acos((Math.random() * 2) - 1);
                    x = radius * Math.sin(phi) * Math.cos(theta);
                    y = radius * Math.sin(phi) * Math.sin(theta);
                    z = radius * Math.cos(phi);
                    break;

                case 'skynet_text':
                    if (i < this.skynetTextCoords.length) {
                        const coord = this.skynetTextCoords[i];
                        x = coord.x;
                        y = coord.y;
                        z = coord.z;
                    } else {
                        // Partículas extras flutuam ao redor
                        const angle = Math.random() * Math.PI * 2;
                        const dist = 200 + Math.random() * 100;
                        x = Math.cos(angle) * dist;
                        y = (Math.random() - 0.5) * 100;
                        z = Math.sin(angle) * dist + (Math.random() - 0.5) * 50;
                    }
                    break;

                case 'atom':
                    const orbitRadius = 80 + (i % 4) * 30;
                    const orbitAngle = (i / this.particleCount) * Math.PI * 20;
                    const orbitTilt = (i % 3) * Math.PI / 3;
                    x = orbitRadius * Math.cos(orbitAngle);
                    y = orbitRadius * Math.sin(orbitAngle) * Math.cos(orbitTilt);
                    z = orbitRadius * Math.sin(orbitAngle) * Math.sin(orbitTilt);
                    break;

                case 'fireworks':
                    const burstRadius = Math.random() * 250;
                    const burstTheta = Math.random() * Math.PI * 2;
                    const burstPhi = Math.random() * Math.PI;
                    x = burstRadius * Math.sin(burstPhi) * Math.cos(burstTheta);
                    y = burstRadius * Math.sin(burstPhi) * Math.sin(burstTheta) - 80;
                    z = burstRadius * Math.cos(burstPhi);
                    break;

                case 'wave':
                    const waveX = (i % 120) * 4 - 240;
                    const waveZ = Math.floor(i / 120) * 4 - 125;
                    x = waveX;
                    y = Math.sin(waveX * 0.05) * 40 + Math.cos(waveZ * 0.05) * 40;
                    z = waveZ;
                    break;

                case 'helix':
                    const helixT = (i / this.particleCount) * Math.PI * 12;
                    const helixRadius = 80;
                    x = helixRadius * Math.cos(helixT);
                    y = (i / this.particleCount) * 350 - 175;
                    z = helixRadius * Math.sin(helixT);
                    break;

                case 'galaxy':
                    const arm = i % 4;
                    const armOffset = arm * (Math.PI * 2 / 4);
                    const galaxyRadius = Math.pow(Math.random(), 0.5) * 180;
                    const galaxyAngle = armOffset + galaxyRadius * 0.025 + Math.random() * 0.4;
                    x = galaxyRadius * Math.cos(galaxyAngle);
                    y = (Math.random() - 0.5) * 15 * (1 - galaxyRadius / 180);
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
                this.setColors(0xaa66ff, 0x8844cc); // Roxo
                break;

            case 'listening':
                this.rotationSpeed = 0.002;
                this.pulseSpeed = 0.05;
                this.expansionFactor = 1.1;
                this.setColors(0xbb77ff, 0x9955dd); // Roxo mais claro
                break;

            case 'thinking':
                this.rotationSpeed = 0.005;
                this.pulseSpeed = 0.1;
                this.expansionFactor = 0.9;
                this.setColors(0xff9944, 0xff6600); // Laranja
                break;

            case 'speaking':
                this.rotationSpeed = 0.003;
                this.pulseSpeed = 0.08;
                this.expansionFactor = 1.15;
                this.setColors(0x66ffaa, 0x44dd88); // Verde
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
        const volumeEffect = this.isUserSpeaking ? this.volumeSmooth * 40 : 0;

        const positions = this.particles.geometry.attributes.position.array;

        // Smooth transition to target positions
        if (this.transitionProgress < 1) {
            this.transitionProgress += this.transitionSpeed;

            for (let i = 0; i < positions.length; i++) {
                positions[i] += (this.targetPositions[i] - positions[i]) * 0.04;
            }

            this.particles.geometry.attributes.position.needsUpdate = true;
        }

        // Apply animations based on mode
        for (let i = 0; i < this.particleCount; i++) {
            const i3 = i * 3;

            // Pulse effect - enhanced by volume
            const basePulse = Math.sin(this.time * this.pulseSpeed + i * 0.01) * 3;
            const pulse = basePulse + volumeEffect;

            // Add slight movement - more when volume is higher
            const moveMult = 0.05 + volumeEffect * 0.01;
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
            const volumeExpansion = this.isUserSpeaking ? 1 + this.volumeSmooth * 2 : 1;

            if (dist > 0) {
                const targetDist = dist * this.expansionFactor * volumeExpansion;
                const factor = 1 + (targetDist - dist) / dist * 0.008;
                positions[i3] *= factor;
                positions[i3 + 1] *= factor;
                positions[i3 + 2] *= factor;
            }
        }

        this.particles.geometry.attributes.position.needsUpdate = true;

        // Rotate particles - faster when volume high
        const volumeRotation = this.isUserSpeaking ? this.volumeSmooth * 0.008 : 0;
        this.particles.rotation.y += this.rotationSpeed + volumeRotation;
        this.particles.rotation.x = this.mouse.y * 0.15;

        // Camera follows mouse slightly
        this.camera.position.x += (this.mouse.x * 80 - this.camera.position.x) * 0.015;
        this.camera.position.y += (this.mouse.y * 40 - this.camera.position.y) * 0.015;
        this.camera.lookAt(0, 0, 0);

        // Update shader time
        this.particles.material.uniforms.time.value = this.time;

        this.renderer.render(this.scene, this.camera);
    }

    // Trigger effects for specific events
    triggerExplosion() {
        this.expansionFactor = 1.8;
        setTimeout(() => {
            this.expansionFactor = 1;
        }, 500);
    }

    triggerImplosion() {
        this.expansionFactor = 0.4;
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

    // Replay intro animation
    replayIntro() {
        this.setMode('sphere');
        this.introPhase = 'sphere';
        this.introAnimationDone = false;
        this.startIntroSequence();
    }
}

// Export for use in other files
window.ParticleSystem = ParticleSystem;
