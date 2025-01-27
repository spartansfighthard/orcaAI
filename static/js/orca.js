// Wrap in DOMContentLoaded to ensure safe execution
document.addEventListener('DOMContentLoaded', function() {
    try {
        // Check if canvas exists before initializing
        const waterCanvas = document.getElementById('water-bg');
        if (!waterCanvas) {
            console.error('Water canvas not found');
            return;
        }

        const waterEffect = new WaterEffect();
        const orcaModel = new OrcaModel();
        const chatInterface = new ChatInterface();
        
        orcaModel.animate();
    } catch (error) {
        console.error('Error initializing components:', error);
        // Show error in UI
        const container = document.querySelector('.interface-container');
        if (container) {
            container.innerHTML += `
                <div style="color: red; padding: 20px; text-align: center;">
                    Error initializing interface. Please refresh the page.
                </div>
            `;
        }
    }
});

class OrcaModel {
    constructor() {
        try {
            this.container = document.getElementById('orca-model');
            if (!this.container) {
                throw new Error('Model container not found');
            }

            // Set explicit dimensions
            this.container.style.width = '100%';
            this.container.style.height = '100%';

            this.scene = new THREE.Scene();
            this.camera = new THREE.PerspectiveCamera(75, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
            
            // Enhanced renderer settings
            this.renderer = new THREE.WebGLRenderer({ 
                antialias: true, 
                alpha: true,
                powerPreference: "high-performance"
            });
            
            this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
            this.renderer.setClearColor(0x000066, 0); // Transparent background
            this.renderer.shadowMap.enabled = true;
            this.container.appendChild(this.renderer.domElement);

            this.setupLights();
            
            // Set model path and load it
            this.modelPath = '/static/models/orca.glb';
            this.loadModel().catch(() => {
                console.log('Falling back to basic model');
                this.loadFallbackModel();
            });
            
            this.setupControls();
            
            // Add water effect animation
            this.time = 0;
            
            window.addEventListener('resize', () => this.onWindowResize(), false);
        } catch (error) {
            console.error('Error initializing OrcaModel:', error);
            this.showFallbackContent();
        }
    }

    setupLights() {
        // Enhanced lighting
        const mainLight = new THREE.PointLight(0x0066cc, 1.5, 100);
        mainLight.position.set(10, 10, 10);
        mainLight.castShadow = true;
        this.scene.add(mainLight);

        const backLight = new THREE.PointLight(0x0044aa, 1, 100);
        backLight.position.set(-10, 5, -10);
        this.scene.add(backLight);

        const ambientLight = new THREE.AmbientLight(0x404040, 0.8);
        this.scene.add(ambientLight);
    }

    async loadModel() {
        try {
            const loadingElement = document.getElementById('model-loading');
            if (loadingElement) loadingElement.style.display = 'block';
            
            // Create GLTFLoader
            const loader = new THREE.GLTFLoader();
            
            // Load the model
            console.log('Loading model from:', this.modelPath);
            const gltf = await loader.loadAsync(this.modelPath);
            console.log('Model loaded successfully:', gltf);
            
            // Set up the model
            this.model = gltf.scene;
            this.model.scale.set(2, 2, 2); // Scale the model
            this.model.position.set(0, 0, 0); // Center the model
            this.model.rotation.set(0, Math.PI, 0); // Rotate to face forward
            
            // Add model to scene
            this.scene.add(this.model);
            
            // Position camera
            this.camera.position.z = 5;
            this.camera.position.y = 2;
            this.camera.lookAt(0, 0, 0);
            
            // Hide loading indicator
            if (loadingElement) loadingElement.style.display = 'none';
            
            return this.model;
        } catch (error) {
            console.error('Error loading model:', error);
            throw error; // Propagate error to trigger fallback
        }
    }

    loadFallbackModel() {
        console.log('Loading fallback model...');
        const geometry = new THREE.CapsuleGeometry(0.5, 2, 8, 16); // Increased segments
        const material = new THREE.MeshPhongMaterial({
            color: 0x000000,
            emissive: 0x003366,
            transparent: true,
            opacity: 0.9,
            specular: 0x666666,
            shininess: 30
        });
        
        this.model = new THREE.Mesh(geometry, material);
        
        // Enhanced white patches
        const whitePatchGeometry = new THREE.SphereGeometry(0.3, 32, 32);
        const whiteMaterial = new THREE.MeshPhongMaterial({
            color: 0xFFFFFF,
            emissive: 0x666666,
            specular: 0x999999,
            shininess: 50
        });
        
        const bellyPatch = new THREE.Mesh(whitePatchGeometry, whiteMaterial);
        bellyPatch.scale.set(1, 0.5, 2);
        bellyPatch.position.set(0, -0.3, 0);
        this.model.add(bellyPatch);
        
        this.scene.add(this.model);
        this.camera.position.z = 5;
        this.camera.position.y = 1;
        
        const loadingElement = document.getElementById('model-loading');
        if (loadingElement) loadingElement.style.display = 'none';
    }

    setupControls() {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.rotateSpeed = 0.5;
        this.controls.enableZoom = false; // Disable zoom for better UX
        this.controls.enablePan = false; // Disable panning
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        
        this.time += 0.01;
        
        if (this.model) {
            // Smooth swimming motion
            this.model.rotation.y += 0.003;
            this.model.position.y = Math.sin(this.time) * 0.1;
            this.model.rotation.z = Math.sin(this.time * 0.5) * 0.05;
        }
        
        if (this.controls) {
            this.controls.update();
        }
        
        this.renderer.render(this.scene, this.camera);
    }

    onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    showFallbackContent() {
        if (this.container) {
            this.container.innerHTML = '<div style="color: #0066cc; text-align: center; padding: 20px;">*click* *click* Having trouble loading the 3D model. Please refresh!</div>';
        }
    }
}

class ChatInterface {
    constructor() {
        this.terminal = document.getElementById('terminal-output');
        this.input = document.getElementById('terminal-input');
        this.isProcessing = false;
        
        this.setupEventListeners();
        this.initialize();
    }

    setupEventListeners() {
        this.input.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter' && !this.isProcessing && this.input.value.trim()) {
                const message = this.input.value.trim();
                this.input.value = '';
                await this.processMessage(message);
            }
        });
    }

    async initialize() {
        try {
            const response = await fetch('/get-greeting');
            const data = await response.json();
            if (data && data.greeting) {
                await this.typeMessage(data.greeting, 'bot');
            }
        } catch (error) {
            console.error('Error getting greeting:', error);
            await this.typeMessage("*click* *click* Hello! Ready to make waves in the data ocean?", 'bot');
        }
    }

    async processMessage(message) {
        try {
            this.isProcessing = true;
            await this.typeMessage(message, 'user');
            
            const response = await fetch('/generate-response', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.status === 'error') {
                throw new Error(data.response);
            }
            
            await this.typeMessage(data.response, 'bot');
        } catch (error) {
            console.error('Error processing message:', error);
            await this.typeMessage("*splash* Oops, hit some rough waters! Let's try that again.", 'bot');
        } finally {
            this.isProcessing = false;
        }
    }

    async typeMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        this.terminal.appendChild(messageDiv);
        
        for (let i = 0; i < text.length; i++) {
            messageDiv.textContent += text[i];
            await new Promise(resolve => setTimeout(resolve, 20));
        }
        
        this.terminal.scrollTop = this.terminal.scrollHeight;
    }
}

// Water Effect Background
class WaterEffect {
    constructor() {
        const canvas = document.getElementById('water-bg');
        if (!canvas) {
            console.error('Water background canvas not found');
            return;
        }
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        if (!this.ctx) {
            console.error('Could not get 2D context');
            return;
        }
        this.initialize();
    }

    initialize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.waves = [];
        this.createWaves();
        
        window.addEventListener('resize', () => this.handleResize());
        this.animate();
    }

    createWaves() {
        for (let i = 0; i < 5; i++) {
            this.waves.push({
                y: Math.random() * this.canvas.height,
                length: 200 + Math.random() * 200,
                amplitude: 50 + Math.random() * 50,
                speed: 0.1 + Math.random() * 0.1
            });
        }
    }

    handleResize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.waves = [];
        this.createWaves();
    }

    animate() {
        this.ctx.fillStyle = 'rgba(0, 102, 204, 0.1)'; // Light blue
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.ctx.strokeStyle = 'rgba(0, 102, 204, 0.5)';
        this.ctx.lineWidth = 2;
        
        this.waves.forEach(wave => {
            this.ctx.beginPath();
            for (let x = 0; x < this.canvas.width; x++) {
                const y = wave.y + Math.sin((x + Date.now() * wave.speed) / wave.length) * wave.amplitude;
                if (x === 0) {
                    this.ctx.moveTo(x, y);
                } else {
                    this.ctx.lineTo(x, y);
                }
            }
            this.ctx.stroke();
        });
        
        requestAnimationFrame(() => this.animate());
    }
} 