// Shared topic colours + line icons (same palette as the home page topic cards).
const svg = (inner: string) =>
	`<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${inner}</svg>`;

export const topicStyles = [
	{ key: 'batter', c1: '#08372f', c2: '#14a37f', icon: svg('<rect x="1" y="6" width="18" height="12" rx="2"/><path d="M23 13v-2"/><path d="M11 6l-4 6h6l-4 6"/>') },
	{ key: 'car care', c1: '#122b63', c2: '#2f9bd8', icon: svg('<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>') },
	{ key: 'electronic', c1: '#321a63', c2: '#8b6cf0', icon: svg('<path d="M12 14l4-4"/><path d="M3.3 19a10 10 0 1 1 17.4 0"/>') },
	{ key: 'engine', c1: '#5c1410', c2: '#ef6a2a', icon: svg('<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>') },
	{ key: 'key', c1: '#1e2733', c2: '#6c7f98', icon: svg('<circle cx="7.5" cy="15.5" r="4.5"/><path d="M10.7 12.3L21 2M16 7l3 3M18 5l3 3"/>') },
	{ key: 'maintenance', c1: '#5a3205', c2: '#e39a14', icon: svg('<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>') },
	{ key: 'tire', c1: '#14181f', c2: '#4f5b6b', icon: svg('<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><path d="M12 2v6M12 16v6M2 12h6M16 12h6"/>') },
	{ key: 'truck', c1: '#3b2a12', c2: '#a8672a', icon: svg('<path d="M1 3h15v13H1z"/><path d="M16 8h4l3 3v5h-7z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/>') },
	{ key: 'vehicle types', c1: '#5a1236', c2: '#d9487f', icon: svg('<path d="M3 13l2-6h14l2 6v5H3z"/><circle cx="7.5" cy="18" r="1.8"/><circle cx="16.5" cy="18" r="1.8"/>') },
];
export const fallbackStyle = { key: '', c1: '#1c2635', c2: '#4d6b8f', icon: svg('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>') };
export const styleFor = (topic: string) => topicStyles.find((s) => topic.toLowerCase().includes(s.key)) ?? fallbackStyle;
