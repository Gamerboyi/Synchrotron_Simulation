// dashboard.js — Real-time Canvas graphs with Steins;Gate aesthetic
export class Dashboard {
    constructor(container) {
        this.container = container;
        this.graphs = {};
        this.historyLen = 200;

        const graphDefs = [
            { id: 'energy', label: 'MEAN ENERGY (log₁₀ eV)', color: '#00ff41' },
            { id: 'radius', label: 'MEAN RADIUS (m)', color: '#00ccff' },
            { id: 'bz',     label: 'Bz FIELD (T)', color: '#ffcc00' },
            { id: 'momentum', label: 'MEAN |p| (kg·m/s)', color: '#ff6600' },
        ];

        graphDefs.forEach(def => {
            const wrapper = document.createElement('div');
            wrapper.className = 'graph-wrapper';

            const label = document.createElement('div');
            label.className = 'graph-label';
            label.textContent = def.label;

            const valueDisplay = document.createElement('span');
            valueDisplay.className = 'graph-value';
            valueDisplay.textContent = '0.000';
            label.appendChild(valueDisplay);

            const canvas = document.createElement('canvas');
            canvas.width = 280;
            canvas.height = 70;
            canvas.className = 'graph-canvas';

            wrapper.appendChild(label);
            wrapper.appendChild(canvas);
            container.appendChild(wrapper);

            this.graphs[def.id] = {
                canvas,
                ctx: canvas.getContext('2d'),
                values: [],
                color: def.color,
                valueDisplay,
            };
        });
    }

    push(id, value) {
        const g = this.graphs[id];
        if (!g) return;
        g.values.push(value);
        if (g.values.length > this.historyLen) g.values.shift();
    }

    render() {
        Object.values(this.graphs).forEach(g => {
            this._drawGraph(g);
        });
    }

    _drawGraph(g) {
        const { ctx, canvas, values, color, valueDisplay } = g;
        const w = canvas.width;
        const h = canvas.height;

        // Clear
        ctx.clearRect(0, 0, w, h);

        // Background
        ctx.fillStyle = 'rgba(5, 12, 8, 0.85)';
        ctx.fillRect(0, 0, w, h);

        // Grid lines
        ctx.strokeStyle = 'rgba(0, 255, 65, 0.08)';
        ctx.lineWidth = 0.5;
        for (let i = 1; i < 4; i++) {
            const y = (h / 4) * i;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(w, y);
            ctx.stroke();
        }
        for (let i = 1; i < 6; i++) {
            const x = (w / 6) * i;
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, h);
            ctx.stroke();
        }

        if (values.length < 2) return;

        const vMin = Math.min(...values);
        const vMax = Math.max(...values);
        let span = vMax - vMin;
        if (span < 1e-12) span = Math.max(Math.abs(vMin) * 0.001, 1e-6);

        // Value display
        valueDisplay.textContent = values[values.length - 1].toFixed(4);

        // Fill gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, h);
        gradient.addColorStop(0, color + '33');
        gradient.addColorStop(1, 'rgba(0,0,0,0)');

        ctx.beginPath();
        ctx.moveTo(0, h);

        for (let i = 0; i < values.length; i++) {
            const x = (i / (values.length - 1)) * w;
            const norm = (values[i] - vMin) / span;
            const y = h - 4 - norm * (h - 8);
            if (i === 0) ctx.lineTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.lineTo(w, h);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();

        // Line
        ctx.beginPath();
        for (let i = 0; i < values.length; i++) {
            const x = (i / (values.length - 1)) * w;
            const norm = (values[i] - vMin) / span;
            const y = h - 4 - norm * (h - 8);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.shadowColor = color;
        ctx.shadowBlur = 6;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Border
        ctx.strokeStyle = color + '44';
        ctx.lineWidth = 1;
        ctx.strokeRect(0, 0, w, h);
    }
}
