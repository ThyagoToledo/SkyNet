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
        this.baseColor = new THREE.Color(0x00ff88); // Verde claro
        this.accentColor = new THREE.Color(0x00cc66); // Verde

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
        // Gerar coordenadas para formar "SKYNET" com partículas - Letras mais densas e legíveis
        const letters = {
            'S': [
                // Topo
                [1, 0], [2, 0], [3, 0], [4, 0],
                [0, 0.5], [0, 1],
                // Meio
                [1, 2], [2, 2], [3, 2],
                // Baixo direita
                [4, 2.5], [4, 3], [4, 3.5],
                // Base
                [0, 4], [1, 4], [2, 4], [3, 4]
            ],
            'K': [
                // Linha vertical
                [0, 0], [0, 0.5], [0, 1], [0, 1.5], [0, 2], [0, 2.5], [0, 3], [0, 3.5], [0, 4],
                // Diagonal superior
                [1, 1.5], [2, 1], [3, 0.5], [4, 0],
                // Diagonal inferior
                [1, 2.5], [2, 3], [3, 3.5], [4, 4]
            ],
            'Y': [
                // Braço esquerdo
                [0, 0], [0.5, 0.5], [1, 1], [1.5, 1.5],
                // Braço direito
                [4, 0], [3.5, 0.5], [3, 1], [2.5, 1.5],
                // Tronco central
                [2, 2], [2, 2.5], [2, 3], [2, 3.5], [2, 4]
            ],
            'N': [
                // Linha esquerda
                [0, 0], [0, 0.5], [0, 1], [0, 1.5], [0, 2], [0, 2.5], [0, 3], [0, 3.5], [0, 4],
                // Diagonal
                [0.5, 0.5], [1, 1], [1.5, 1.5], [2, 2], [2.5, 2.5], [3, 3], [3.5, 3.5],
                // Linha direita
                [4, 0], [4, 0.5], [4, 1], [4, 1.5], [4, 2], [4, 2.5], [4, 3], [4, 3.5], [4, 4]
            ],
            'E': [
                // Linha vertical
                [0, 0], [0, 0.5], [0, 1], [0, 1.5], [0, 2], [0, 2.5], [0, 3], [0, 3.5], [0, 4],
                // Topo
                [1, 0], [2, 0], [3, 0], [4, 0],
                // Meio
                [1, 2], [2, 2], [3, 2],
                // Base
                [1, 4], [2, 4], [3, 4], [4, 4]
            ],
            'T': [
                // Topo horizontal
                [0, 0], [1, 0], [2, 0], [3, 0], [4, 0],
                // Tronco central
                [2, 0.5], [2, 1], [2, 1.5], [2, 2], [2, 2.5], [2, 3], [2, 3.5], [2, 4]
            ]
        };

        const word = 'SKYNET';
        const scale = 18; // Reduzido pela metade para caber na tela
        const letterWidth = 5 * scale; // Largura de cada letra
        const spacing = letterWidth + 15; // Espaçamento reduzido proporcionalmente
        const totalWidth = word.length * spacing - 15;
        const startX = -totalWidth / 2;

        this.skynetTextCoords = [];

        for (let i = 0; i < word.length; i++) {
            const letter = letters[word[i]];
            const offsetX = startX + i * spacing;

            for (const [x, y] of letter) {
                // Muito mais partículas por ponto para densidade alta e legibilidade perfeita
                for (let j = 0; j < 80; j++) {
                    this.skynetTextCoords.push({
                        x: offsetX + x * scale + (Math.random() - 0.5) * 6, // Jitter reduzido
                        y: (2 - y) * scale + (Math.random() - 0.5) * 6,
                        z: (Math.random() - 0.5) * 4
                    });
                }
            }
        }
    }

    createParticles() {
        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(this.particleCount * 3);
        const targetPositions = new Float32Array(this.particleCount * 3); // Buffer para destino
        const colors = new Float32Array(this.particleCount * 3);
        const sizes = new Float32Array(this.particleCount);

        // Initialize particles in dense sphere formation
        for (let i = 0; i < this.particleCount; i++) {
            const i3 = i * 3;

            // Esfera inicial
            const radius = 100 + Math.random() * 30;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos((Math.random() * 2) - 1);

            const x = radius * Math.sin(phi) * Math.cos(theta);
            const y = radius * Math.sin(phi) * Math.sin(theta);
            const z = radius * Math.cos(phi);

            // Set both current and target to sphere initially
            positions[i3] = x;
            positions[i3 + 1] = y;
            positions[i3 + 2] = z;

            targetPositions[i3] = x;
            targetPositions[i3 + 1] = y;
            targetPositions[i3 + 2] = z;

            // Colors
            const color = this.baseColor.clone();
            color.lerp(this.accentColor, Math.random() * 0.5);
            colors[i3] = color.r;
            colors[i3 + 1] = color.g;
            colors[i3 + 2] = color.b;

            sizes[i] = Math.random() * 2 + 0.5;
        }

        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('targetPosition', new THREE.BufferAttribute(targetPositions, 3)); // Add target attribute
        geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        // Custom shader material with Morphing logic
        const material = new THREE.ShaderMaterial({
            uniforms: {
                time: { value: 0 },
                mixFactor: { value: 0 }, // 0 = position, 1 = targetPosition
                pixelRatio: { value: this.renderer.getPixelRatio() }
            },
            vertexShader: `
                attribute float size;
                attribute vec3 targetPosition;
                attribute vec3 color;
                
                varying vec3 vColor;
                uniform float time;
                uniform float mixFactor;
                
                void main() {
                    vColor = color;
                    
                    // Cubic easing for mixFactor directly in shader or pre-calculated in JS
                    // Here we assume mixFactor is linear 0->1 and we can ease it here or in JS.
                    // Let's do a simple mix for maximum smoothness.
                    
                    vec3 finalPos = mix(position, targetPosition, mixFactor);
                    
                    // Add some noise/movement based on time
                    float noiseFreq = 0.02;
                    float noiseAmp = 2.0;
                    vec3 noise = vec3(
                        sin(time * 2.0 + finalPos.y * noiseFreq) * noiseAmp,
                        cos(time * 1.5 + finalPos.z * noiseFreq) * noiseAmp,
                        sin(time * 2.2 + finalPos.x * noiseFreq) * noiseAmp
                    );
                    
                    vec4 mvPosition = modelViewMatrix * vec4(finalPos + noise, 1.0);
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
            vertexColors: false, // We use custom 'color' attribute, not built-in vertexColors logic implies
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        this.particles = new THREE.Points(geometry, material);
        this.scene.add(this.particles);
    }

    startIntroSequence() {
        // Iniciar imediatamente no modo texto
        this.introPhase = 'text';
        this.setMode('skynet_text'); // Use setMode for transitions
        this.camera.position.z = 350;

        // Fase 2: Mostrar texto por 4 segundos, depois voltar à esfera
        setTimeout(() => {
            this.introPhase = 'back_to_sphere';
            this.setMode('sphere');
            this.camera.position.z = 400;
            this.introAnimationDone = true;
        }, 4000);
    }

    setMode(mode) {
        if (this.currentMode === mode && this.transitionProgress >= 1) return;

        // Get access to attributes
        const positionAttr = this.particles.geometry.attributes.position;
        const targetAttr = this.particles.geometry.attributes.targetPosition;

        // If we finished a previous transition, our "visual" position is targetPosition.
        // Copy target -> position to be the new start.
        if (this.transitionProgress >= 1) {
            positionAttr.array.set(targetAttr.array);
            positionAttr.needsUpdate = true;
        } else {
            // If interrupted, we have a problem. The visual state is a mix.
            // We can bake the current mix into 'position'
            // position = mix(position, target, mixFactor)
            // simplified: assume we always finish or just snap.
            // Force finish:
            positionAttr.array.set(targetAttr.array);
            positionAttr.needsUpdate = true;
        }

        this.currentMode = mode;
        this.transitionProgress = 0;
        this.particles.material.uniforms.mixFactor.value = 0;

        // Calculate NEW targets
        this.calculateTargetPositions(targetAttr.array);
        targetAttr.needsUpdate = true;
    }

    calculateTargetPositions(outputArray) {
        // Fill outputArray with new coordinates based on this.currentMode
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
                        // Halo em volta do texto
                        const angle = Math.random() * Math.PI * 2;
                        const dist = 300 + Math.random() * 150;
                        x = Math.cos(angle) * dist;
                        y = (Math.random() - 0.5) * 200;
                        z = Math.sin(angle) * dist * 0.5;
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
                    x = 0; y = 0; z = 0;
            }

            outputArray[i3] = x;
            outputArray[i3 + 1] = y;
            outputArray[i3 + 2] = z;
        }
    }

    setState(state) {
        this.currentState = state;

        switch (state) {
            case 'idle':
                this.rotationSpeed = 0.001;
                this.pulseSpeed = 0.02;
                this.expansionFactor = 1;
                this.setColors(0x00ff88, 0x00cc66); // Verde
                break;

            case 'listening':
                this.rotationSpeed = 0.002;
                this.pulseSpeed = 0.05;
                this.expansionFactor = 1.1;
                this.setColors(0x44ffaa, 0x22dd88); // Verde mais claro
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

        this.time += 0.01;

        // Smooth volume changes
        this.volumeSmooth += (this.audioVolume - this.volumeSmooth) * 0.1;

        // Update Shader Transition
        if (this.transitionProgress < 1) {
            this.transitionProgress += this.transitionSpeed;
            if (this.transitionProgress > 1) this.transitionProgress = 1;

            // Simple cubic ease out for mixFactor
            const t = this.transitionProgress;
            const ease = 1 - Math.pow(1 - t, 3);

            if (this.particles && this.particles.material.uniforms) {
                this.particles.material.uniforms.mixFactor.value = ease;
            }
        }

        // Apply volume-based effects when user is speaking
        const volumeEffect = this.isUserSpeaking ? this.volumeSmooth * 40 : 0;

        // No CPU-based position updates for transition anymore!
        // We rely on the vertex shader 'mix(position, targetPosition, mixFactor)'

        // Other CPU animations (pulse, wave) still act on the 'position' buffer?
        // Wait, if we use shader for position, modifying the buffer on CPU conflicts with it?
        // The shader mixes 'position' and 'targetPosition'.
        // If we modify 'position' (the source), it affects the mix.
        // But our shader only does: finalPos = mix(position, targetPosition, mixFactor) + noise
        // The shader does NOT have "pulse" or "expansion" logic inside (except noise).
        // So we LOSE the pulse/expansion effects if we don't apply them to the shader or keep CPU update.

        // BEST PRACTICE: Move Pulse/Expansion to Shader too.
        // Logic:
        // Vertex Shader:
        // vec3 base = mix(position, targetPosition, mixFactor);
        // Apply expansion: base *= expansionFactor
        // Apply pulse: base += normal * sin(time)

        // BUT, rewriting all effects to shader now is risky for regressions on specific modes like 'galaxy'.
        // Hybrid approach:
        // We stop modifying positions array for *transition*, but we can still modify it for *effects*?
        // No, updating buffer every frame kills the performance gain.
        // CORRECT PATH:
        // Use shader for EVERYTHING if possible, or just accept that "effects" like pulse are subtle/removed or implemented simply in shader.
        // Let's implement simple pulse/expansion in shader using Uniforms.

        if (this.particles && this.particles.material.uniforms) {
            this.particles.material.uniforms.time.value = this.time;
            // Send volume/expansion to shader?
            // For now, let's keep it simple: Smooth transition is the priority.
            // We can re-add pulse later if needed, but the 'noise' in shader gives some life.
        }

        // Rotate particles - faster when volume high
        const volumeRotation = this.isUserSpeaking ? this.volumeSmooth * 0.005 : 0;
        if (this.particles) {
            this.particles.rotation.y += this.rotationSpeed + volumeRotation;
            this.particles.rotation.x = this.mouse.y * 0.15;
        }

        // Camera follows mouse slightly
        if (this.camera) {
            this.camera.position.x += (this.mouse.x * 80 - this.camera.position.x) * 0.015;
            this.camera.position.y += (this.mouse.y * 40 - this.camera.position.y) * 0.015;
            this.camera.lookAt(0, 0, 0);
        }

        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
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

    // Set transparent mode
    setTransparent(enabled) {
        if (enabled) {
            this.scene.background = null;
            this.renderer.setClearColor(0x000000, 0);
        } else {
            this.scene.background = new THREE.Color(0x000000);
            this.renderer.setClearColor(0x000000, 1);
        }
    }
}

// Export for use in other files
window.ParticleSystem = ParticleSystem;
