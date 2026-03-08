// renderer.js — Three.js 3D scene with cinematic Steins;Gate aesthetic
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';

const COLORS = {
    bg: 0x020508,
    ringInner: 0x00ff88,
    ringOuter: 0x003322,
    ringEmissive: 0x00ff66,
    beamPipe: 0x001a0d,
    particleAlive: 0x00ff41,
    particleHead: 0xff4444,
    particleDead: 0x441111,
    rfGap: 0xffaa00,
    trail: 0x44ffaa,
    gridColor: 0x0a1f12,
    starField: 0xffffff,
    energyRing: 0x00ffcc,
    accent: 0xff6600,
};

export class Renderer {
    constructor(container) {
        this.container = container;
        this.R = 10; // Major radius of torus in world units
        this.tubeR = 0.6; // Tube radius — thick enough to see 3D depth

        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(COLORS.bg);
        this.scene.fog = new THREE.FogExp2(COLORS.bg, 0.008);

        // Camera — cinematic low angle for dramatic 3D perspective
        this.camera = new THREE.PerspectiveCamera(50, 1, 0.1, 500);
        this.camera.position.set(18, 9, 14);
        this.camera.lookAt(0, 0, 0);

        // Renderer
        this.webglRenderer = new THREE.WebGLRenderer({
            antialias: true,
            powerPreference: 'high-performance',
        });
        this.webglRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.webglRenderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.webglRenderer.toneMappingExposure = 1.4;
        this.webglRenderer.shadowMap.enabled = true;
        this.webglRenderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(this.webglRenderer.domElement);

        // Controls
        this.controls = new OrbitControls(this.camera, this.webglRenderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.06;
        this.controls.maxDistance = 60;
        this.controls.minDistance = 6;
        this.controls.target.set(0, 0, 0);
        this.controls.maxPolarAngle = Math.PI * 0.85;

        // Post-processing — heavy bloom for sci-fi glow
        this.composer = new EffectComposer(this.webglRenderer);
        this.composer.addPass(new RenderPass(this.scene, this.camera));
        this.bloomPass = new UnrealBloomPass(
            new THREE.Vector2(window.innerWidth, window.innerHeight),
            1.2,   // strength — cranked up
            0.5,   // radius
            0.7    // threshold — lower = more things glow
        );
        this.composer.addPass(this.bloomPass);

        // Build scene
        this._buildStarField();
        this._buildLights();
        this._buildBeamPipe();
        this._buildInnerRings();
        this._buildGrid();
        this._buildRFGapStructure();
        this._buildEnergyRings();
        this._buildSupportStructures();
        this._buildParticles(50);
        this._buildTrails(50);

        this.handleResize();
        window.addEventListener('resize', () => this.handleResize());
    }

    handleResize() {
        const w = this.container.clientWidth;
        const h = this.container.clientHeight;
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.webglRenderer.setSize(w, h);
        this.composer.setSize(w, h);
    }

    // ═══════════════════════════════════════════════════════
    // STARFIELD — deep space background
    // ═══════════════════════════════════════════════════════
    _buildStarField() {
        const starCount = 2000;
        const geo = new THREE.BufferGeometry();
        const positions = new Float32Array(starCount * 3);
        const sizes = new Float32Array(starCount);

        for (let i = 0; i < starCount; i++) {
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            const r = 80 + Math.random() * 120;
            positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
            positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
            positions[i * 3 + 2] = r * Math.cos(phi);
            sizes[i] = 0.3 + Math.random() * 1.2;
        }

        geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geo.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        const mat = new THREE.PointsMaterial({
            color: 0x88aacc,
            size: 0.4,
            transparent: true,
            opacity: 0.7,
            sizeAttenuation: true,
            blending: THREE.AdditiveBlending,
        });

        this.starField = new THREE.Points(geo, mat);
        this.scene.add(this.starField);
    }

    // ═══════════════════════════════════════════════════════
    // LIGHTS — dramatic multi-point lighting
    // ═══════════════════════════════════════════════════════
    _buildLights() {
        // Subtle ambient
        this.scene.add(new THREE.AmbientLight(0x001a0d, 0.8));

        // Main overhead green
        const mainLight = new THREE.PointLight(COLORS.ringInner, 3, 50);
        mainLight.position.set(0, 15, 0);
        this.scene.add(mainLight);

        // Rim light — amber accent
        const rimLight = new THREE.PointLight(COLORS.accent, 1.5, 40);
        rimLight.position.set(-15, 8, -10);
        this.scene.add(rimLight);

        // Fill light — cool cyan
        const fillLight = new THREE.PointLight(0x0066ff, 1, 35);
        fillLight.position.set(12, 5, 15);
        this.scene.add(fillLight);

        // Under-glow
        const underLight = new THREE.PointLight(COLORS.ringInner, 0.8, 25);
        underLight.position.set(0, -5, 0);
        this.scene.add(underLight);
    }

    // ═══════════════════════════════════════════════════════
    // BEAM PIPE — the main torus structure (thick, glassy)
    // ═══════════════════════════════════════════════════════
    _buildBeamPipe() {
        // Outer glass-like shell
        const outerGeo = new THREE.TorusGeometry(this.R, this.tubeR, 64, 200);
        const outerMat = new THREE.MeshPhysicalMaterial({
            color: 0x003322,
            emissive: COLORS.ringEmissive,
            emissiveIntensity: 0.15,
            metalness: 0.3,
            roughness: 0.2,
            transparent: true,
            opacity: 0.3,
            transmission: 0.4,
            thickness: 0.5,
            side: THREE.DoubleSide,
            envMapIntensity: 0.5,
        });
        this.beamPipe = new THREE.Mesh(outerGeo, outerMat);
        this.beamPipe.rotation.x = Math.PI / 2;
        this.scene.add(this.beamPipe);

        // Wireframe cage around the pipe
        const wireGeo = new THREE.TorusGeometry(this.R, this.tubeR * 1.05, 24, 120);
        const wireMat = new THREE.MeshBasicMaterial({
            color: COLORS.ringInner,
            wireframe: true,
            transparent: true,
            opacity: 0.12,
        });
        this.beamWire = new THREE.Mesh(wireGeo, wireMat);
        this.beamWire.rotation.x = Math.PI / 2;
        this.scene.add(this.beamWire);
    }

    // ═══════════════════════════════════════════════════════
    // INNER RINGS — bright centerline guides
    // ═══════════════════════════════════════════════════════
    _buildInnerRings() {
        // Bright thin centerline
        const centerGeo = new THREE.TorusGeometry(this.R, 0.04, 8, 300);
        const centerMat = new THREE.MeshBasicMaterial({
            color: COLORS.ringInner,
            transparent: true,
            opacity: 0.9,
        });
        this.centerRing = new THREE.Mesh(centerGeo, centerMat);
        this.centerRing.rotation.x = Math.PI / 2;
        this.scene.add(this.centerRing);

        // Inner edge ring
        const inner2 = new THREE.TorusGeometry(this.R, this.tubeR * 0.3, 16, 150);
        const inner2Mat = new THREE.MeshBasicMaterial({
            color: COLORS.ringInner,
            transparent: true,
            opacity: 0.08,
        });
        const innerMesh = new THREE.Mesh(inner2, inner2Mat);
        innerMesh.rotation.x = Math.PI / 2;
        this.scene.add(innerMesh);
    }

    // ═══════════════════════════════════════════════════════
    // SUPPORT STRUCTURES — pylons around the ring
    // ═══════════════════════════════════════════════════════
    _buildSupportStructures() {
        const pylonCount = 12;
        const pylonGeo = new THREE.BoxGeometry(0.12, 3.5, 0.12);
        const pylonMat = new THREE.MeshPhongMaterial({
            color: 0x112222,
            emissive: COLORS.ringInner,
            emissiveIntensity: 0.05,
        });

        for (let i = 0; i < pylonCount; i++) {
            const angle = (i / pylonCount) * Math.PI * 2;
            const pylon = new THREE.Mesh(pylonGeo, pylonMat);
            pylon.position.set(
                this.R * Math.cos(angle),
                -1.5,
                this.R * Math.sin(angle)
            );
            this.scene.add(pylon);

            // Horizontal brace connecting to ring
            const braceGeo = new THREE.BoxGeometry(0.06, 0.06, this.tubeR * 2.5);
            const brace = new THREE.Mesh(braceGeo, pylonMat);
            brace.position.set(
                this.R * Math.cos(angle),
                0,
                this.R * Math.sin(angle)
            );
            brace.lookAt(0, 0, 0);
            this.scene.add(brace);

            // Small light on each pylon
            const lightGeo = new THREE.SphereGeometry(0.08, 8, 8);
            const lightMat = new THREE.MeshBasicMaterial({ color: COLORS.ringInner });
            const lightMesh = new THREE.Mesh(lightGeo, lightMat);
            lightMesh.position.set(
                this.R * Math.cos(angle),
                0.3,
                this.R * Math.sin(angle)
            );
            this.scene.add(lightMesh);
        }
    }

    // ═══════════════════════════════════════════════════════
    // ENERGY RINGS — animated rings flowing through the tube
    // ═══════════════════════════════════════════════════════
    _buildEnergyRings() {
        this.energyRings = [];
        const ringCount = 8;

        for (let i = 0; i < ringCount; i++) {
            const geo = new THREE.RingGeometry(this.tubeR * 0.3, this.tubeR * 0.7, 32);
            const mat = new THREE.MeshBasicMaterial({
                color: COLORS.energyRing,
                transparent: true,
                opacity: 0.2,
                side: THREE.DoubleSide,
                blending: THREE.AdditiveBlending,
            });
            const ring = new THREE.Mesh(geo, mat);
            ring.userData.phase = (i / ringCount) * Math.PI * 2;
            this.energyRings.push(ring);
            this.scene.add(ring);
        }
    }

    // ═══════════════════════════════════════════════════════
    // RF GAP STRUCTURE — visible accelerating cavity
    // ═══════════════════════════════════════════════════════
    _buildRFGapStructure() {
        const gapGroup = new THREE.Group();

        // Main cavity body
        const cavityGeo = new THREE.CylinderGeometry(1.0, 1.0, 0.4, 16);
        const cavityMat = new THREE.MeshPhongMaterial({
            color: 0x332200,
            emissive: COLORS.rfGap,
            emissiveIntensity: 0.3,
            transparent: true,
            opacity: 0.7,
        });
        const cavity = new THREE.Mesh(cavityGeo, cavityMat);
        cavity.rotation.z = Math.PI / 2;
        gapGroup.add(cavity);

        // Glowing energy sphere at center
        const sphereGeo = new THREE.SphereGeometry(0.35, 16, 16);
        const sphereMat = new THREE.MeshBasicMaterial({
            color: COLORS.rfGap,
            transparent: true,
            opacity: 0.9,
        });
        this.rfSphere = new THREE.Mesh(sphereGeo, sphereMat);
        gapGroup.add(this.rfSphere);

        // Vertical antenna
        const antennaGeo = new THREE.CylinderGeometry(0.04, 0.04, 5, 8);
        const antennaMat = new THREE.MeshBasicMaterial({
            color: COLORS.rfGap,
            transparent: true,
            opacity: 0.4,
        });
        const antenna = new THREE.Mesh(antennaGeo, antennaMat);
        antenna.position.y = 2.5;
        gapGroup.add(antenna);

        // Accent rings around cavity
        for (let i = 0; i < 3; i++) {
            const rGeo = new THREE.TorusGeometry(1.0 + i * 0.25, 0.02, 8, 32);
            const rMat = new THREE.MeshBasicMaterial({
                color: COLORS.rfGap,
                transparent: true,
                opacity: 0.3 - i * 0.08,
            });
            const rMesh = new THREE.Mesh(rGeo, rMat);
            rMesh.rotation.x = Math.PI / 2;
            gapGroup.add(rMesh);
        }

        gapGroup.position.set(this.R, 0, 0);
        this.rfGapGroup = gapGroup;
        this.scene.add(gapGroup);
    }

    // ═══════════════════════════════════════════════════════
    // GRID — ground reference plane
    // ═══════════════════════════════════════════════════════
    _buildGrid() {
        const gridHelper = new THREE.GridHelper(50, 50, 0x003318, 0x0a1510);
        gridHelper.position.y = -3.2;
        gridHelper.material.opacity = 0.25;
        gridHelper.material.transparent = true;
        this.scene.add(gridHelper);

        // Reflective ground disc
        const groundGeo = new THREE.CircleGeometry(25, 64);
        const groundMat = new THREE.MeshPhongMaterial({
            color: 0x020805,
            emissive: COLORS.ringInner,
            emissiveIntensity: 0.01,
            transparent: true,
            opacity: 0.6,
        });
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -3.2;
        this.scene.add(ground);
    }

    // ═══════════════════════════════════════════════════════
    // PARTICLES — glowing shader-based points
    // ═══════════════════════════════════════════════════════
    _buildParticles(maxCount) {
        this.maxParticles = maxCount;
        const geo = new THREE.BufferGeometry();
        const positions = new Float32Array(maxCount * 3);
        const colors = new Float32Array(maxCount * 3);
        const sizes = new Float32Array(maxCount);

        geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
        geo.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        const vertexShader = `
            attribute float size;
            attribute vec3 color;
            varying vec3 vColor;
            varying float vDist;
            void main() {
                vColor = color;
                vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                vDist = -mvPosition.z;
                gl_PointSize = size * (250.0 / -mvPosition.z);
                gl_PointSize = clamp(gl_PointSize, 2.0, 80.0);
                gl_Position = projectionMatrix * mvPosition;
            }
        `;
        const fragmentShader = `
            varying vec3 vColor;
            varying float vDist;
            void main() {
                float d = length(gl_PointCoord - vec2(0.5));
                if (d > 0.5) discard;
                float core = 1.0 - smoothstep(0.0, 0.15, d);
                float glow = 1.0 - smoothstep(0.0, 0.5, d);
                float intensity = core * 1.5 + glow * 0.6;
                gl_FragColor = vec4(vColor * intensity, intensity * 0.95);
            }
        `;

        const mat = new THREE.ShaderMaterial({
            vertexShader,
            fragmentShader,
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false,
        });

        this.particlePoints = new THREE.Points(geo, mat);
        this.scene.add(this.particlePoints);

        // Lead particle — actual 3D sphere for prominence
        const leadGeo = new THREE.SphereGeometry(0.25, 16, 16);
        const leadMat = new THREE.MeshBasicMaterial({
            color: COLORS.particleHead,
            transparent: true,
            opacity: 0.95,
        });
        this.leadSphere = new THREE.Mesh(leadGeo, leadMat);
        this.scene.add(this.leadSphere);

        // Lead glow halo
        const haloGeo = new THREE.SphereGeometry(0.6, 16, 16);
        const haloMat = new THREE.MeshBasicMaterial({
            color: COLORS.particleHead,
            transparent: true,
            opacity: 0.15,
            blending: THREE.AdditiveBlending,
        });
        this.leadHalo = new THREE.Mesh(haloGeo, haloMat);
        this.scene.add(this.leadHalo);
    }

    // ═══════════════════════════════════════════════════════
    // TRAILS — 3D line segments following particles
    // ═══════════════════════════════════════════════════════
    _buildTrails(maxCount) {
        this.trailLines = [];
        const maxTrailPoints = 200;

        for (let i = 0; i < maxCount; i++) {
            const geo = new THREE.BufferGeometry();
            const positions = new Float32Array(maxTrailPoints * 3);
            geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            geo.setDrawRange(0, 0);

            const mat = new THREE.LineBasicMaterial({
                color: i === 0 ? 0xff6644 : COLORS.trail,
                transparent: true,
                opacity: i === 0 ? 0.6 : 0.3,
                blending: THREE.AdditiveBlending,
                linewidth: 1,
            });

            const line = new THREE.Line(geo, mat);
            this.trailLines.push(line);
            this.scene.add(line);
        }
    }

    // ═══════════════════════════════════════════════════════
    // COORDINATE TRANSFORM — sim 2D → world 3D on torus
    // ═══════════════════════════════════════════════════════
    simToWorld(x, y, ringRadiusSim) {
        const angle = Math.atan2(y, x);
        const r = Math.sqrt(x * x + y * y);
        const rOffset = (r - ringRadiusSim) / ringRadiusSim * this.tubeR * 3;
        const worldR = this.R + rOffset;

        return new THREE.Vector3(
            worldR * Math.cos(angle),
            rOffset * 0.3, // slight vertical offset based on radial deviation
            worldR * Math.sin(angle)
        );
    }

    // ═══════════════════════════════════════════════════════
    // UPDATE PARTICLES EACH FRAME
    // ═══════════════════════════════════════════════════════
    updateParticles(beam, ringRadiusSim) {
        const posAttr = this.particlePoints.geometry.getAttribute('position');
        const colAttr = this.particlePoints.geometry.getAttribute('color');
        const sizeAttr = this.particlePoints.geometry.getAttribute('size');

        const headColor = new THREE.Color(COLORS.particleHead);
        const aliveColor = new THREE.Color(COLORS.particleAlive);
        const deadColor = new THREE.Color(COLORS.particleDead);

        let leadPos = null;

        for (let i = 0; i < this.maxParticles; i++) {
            if (i < beam.length) {
                const p = beam[i];
                const pos = this.simToWorld(p.x, p.y, ringRadiusSim);

                posAttr.setXYZ(i, pos.x, pos.y, pos.z);

                if (i === 0 && p.alive) {
                    leadPos = pos;
                    colAttr.setXYZ(i, headColor.r, headColor.g, headColor.b);
                    sizeAttr.setX(i, 0); // hide point — using 3D sphere instead
                } else {
                    const color = !p.alive ? deadColor : aliveColor;
                    colAttr.setXYZ(i, color.r, color.g, color.b);
                    sizeAttr.setX(i, p.alive ? 5 : 1.5);
                }
            } else {
                posAttr.setXYZ(i, 0, -100, 0);
                sizeAttr.setX(i, 0);
            }
        }

        posAttr.needsUpdate = true;
        colAttr.needsUpdate = true;
        sizeAttr.needsUpdate = true;

        // Update lead particle 3D sphere
        if (leadPos) {
            this.leadSphere.position.copy(leadPos);
            this.leadSphere.visible = true;
            this.leadHalo.position.copy(leadPos);
            this.leadHalo.visible = true;
        } else {
            this.leadSphere.visible = false;
            this.leadHalo.visible = false;
        }
    }

    updateTrails(beam, ringRadiusSim) {
        for (let i = 0; i < Math.min(beam.length, this.trailLines.length); i++) {
            const p = beam[i];
            const line = this.trailLines[i];
            const posAttr = line.geometry.getAttribute('position');

            if (!p.trail || p.trail.length < 2) {
                line.geometry.setDrawRange(0, 0);
                continue;
            }

            const count = Math.min(p.trail.length, 200);
            for (let j = 0; j < count; j++) {
                const [tx, ty] = p.trail[p.trail.length - count + j];
                const pos = this.simToWorld(tx, ty, ringRadiusSim);
                posAttr.setXYZ(j, pos.x, pos.y, pos.z);
            }

            posAttr.needsUpdate = true;
            line.geometry.setDrawRange(0, count);
            line.material.opacity = p.alive ? (i === 0 ? 0.6 : 0.3) : 0.05;
        }
    }

    // ═══════════════════════════════════════════════════════
    // EFFECTS — animated per frame
    // ═══════════════════════════════════════════════════════
    updateEffects(time) {
        // RF gap pulse
        const pulse = 0.5 + 0.5 * Math.sin(time * 5);
        if (this.rfSphere) {
            this.rfSphere.material.opacity = 0.4 + pulse * 0.6;
            this.rfSphere.scale.setScalar(0.8 + 0.4 * pulse);
        }

        // Energy rings flowing through the torus
        for (let i = 0; i < this.energyRings.length; i++) {
            const ring = this.energyRings[i];
            const phase = ring.userData.phase + time * 1.5;
            const angle = phase % (Math.PI * 2);

            const x = this.R * Math.cos(angle);
            const z = this.R * Math.sin(angle);
            ring.position.set(x, 0, z);

            // Orient ring perpendicular to the torus path
            const tangentX = -Math.sin(angle);
            const tangentZ = Math.cos(angle);
            ring.lookAt(x + tangentX, 0, z + tangentZ);

            ring.material.opacity = 0.08 + 0.12 * Math.sin(time * 3 + i);
        }

        // Beam pipe emissive pulse
        if (this.beamPipe) {
            this.beamPipe.material.emissiveIntensity = 0.1 + 0.08 * Math.sin(time * 0.7);
        }

        // Wireframe slow rotation
        if (this.beamWire) {
            this.beamWire.rotation.z += 0.0005;
        }

        // Lead particle halo pulse
        if (this.leadHalo && this.leadHalo.visible) {
            this.leadHalo.scale.setScalar(1.0 + 0.3 * Math.sin(time * 6));
        }

        // Star field slow rotation
        if (this.starField) {
            this.starField.rotation.y += 0.00008;
        }
    }

    render(time) {
        this.controls.update();
        this.updateEffects(time);
        this.composer.render();
    }
}
