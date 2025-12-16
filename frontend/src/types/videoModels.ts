// =============================================================================
// VIDEO MODEL TYPES - Gen Scene Studio
// =============================================================================
// Sincronizado con el backend enterprise_manager.py
// Última actualización: 2025-12-16

export type VideoModelTier = 'premium' | 'high' | 'economic';

export interface VideoModelInfo {
    id: string;
    name: string;
    tier: VideoModelTier;
    credits_5s: number;
    max_duration: number;
    features: string[];
    description: string;
    recommended_for?: string[];
}

export interface StyleModelMapping {
    [styleKey: string]: string;
}

// Modelos disponibles (sincronizados con backend)
export const VIDEO_MODELS: Record<string, VideoModelInfo> = {
    'runway-gen3': {
        id: 'runway-gen3',
        name: 'Runway Gen-3',
        tier: 'high',
        credits_5s: 200,
        max_duration: 10,
        features: ['text-to-video', 'image-to-video', 'video-extension'],
        description: 'Balance óptimo calidad/precio'
    },
    'veo3': {
        id: 'veo3',
        name: 'Google Veo 3.1',
        tier: 'premium',
        credits_5s: 350,
        max_duration: 8,
        features: ['text-to-video', 'image-to-video'],
        description: 'Máxima calidad visual'
    },
    'sora-2-pro-text-to-video': {
        id: 'sora-2-pro-text-to-video',
        name: 'OpenAI Sora 2 Pro',
        tier: 'premium',
        credits_5s: 400,
        max_duration: 20,
        features: ['text-to-video', 'narrative-complex'],
        description: 'Ideal para narrativa compleja'
    },
    'kling/v2-1-pro': {
        id: 'kling/v2-1-pro',
        name: 'Kling v2.1 Pro',
        tier: 'high',
        credits_5s: 250,
        max_duration: 10,
        features: ['text-to-video', 'image-to-video', 'negative-prompt'],
        description: 'Control creativo avanzado'
    },
    'hailuo/2-3-image-to-video-pro': {
        id: 'hailuo/2-3-image-to-video-pro',
        name: 'Hailuo I2V',
        tier: 'economic',
        credits_5s: 180,
        max_duration: 6,
        features: ['image-to-video'],
        description: 'Estilos artísticos únicos'
    },
    'bytedance/v1-pro-text-to-video': {
        id: 'bytedance/v1-pro-text-to-video',
        name: 'Bytedance v1',
        tier: 'economic',
        credits_5s: 150,
        max_duration: 5,
        features: ['text-to-video', 'camera-control'],
        description: 'Optimizado para social media'
    },
    'wan/2-2-a14b-text-to-video-turbo': {
        id: 'wan/2-2-a14b-text-to-video-turbo',
        name: 'Wan Turbo',
        tier: 'economic',
        credits_5s: 120,
        max_duration: 5,
        features: ['text-to-video', 'turbo-speed'],
        description: 'El más económico y rápido'
    }
};

// Mapeo de estilos a modelos por defecto
// ESTRATEGIA: Modelos económicos por defecto, premium solo cuando es necesario
export const STYLE_TO_MODEL: StyleModelMapping = {
    // ===== ESTILOS QUE REQUIEREN PREMIUM (solo estos) =====
    'photorealistic': 'veo3',                 // Requiere máxima calidad
    'realistic': 'runway-gen3',               // Alta fidelidad visual
    'fantasy_epic': 'sora-2-pro-text-to-video',
    'epic': 'sora-2-pro-text-to-video',

    // ===== ESTILOS CON MODELOS ESPECIALIZADOS =====
    'anime_style': 'kling/v2-1-pro',
    'anime': 'kling/v2-1-pro',
    'stylized': 'kling/v2-1-pro',

    // ===== TODOS LOS DEMÁS → ECONÓMICOS =====
    'cinematic_realism': 'bytedance/v1-pro-text-to-video',
    'cinematic': 'bytedance/v1-pro-text-to-video',
    'documentary': 'bytedance/v1-pro-text-to-video',
    'artistic': 'hailuo/2-3-image-to-video-pro',
    'fantasy': 'bytedance/v1-pro-text-to-video',
    'dramatic': 'bytedance/v1-pro-text-to-video',

    // Minimalista/Rápido → Wan Turbo (el más barato)
    'minimalist': 'wan/2-2-a14b-text-to-video-turbo',
    'simple': 'wan/2-2-a14b-text-to-video-turbo',
    'fast': 'wan/2-2-a14b-text-to-video-turbo',

    // Social media → Bytedance
    'social_media': 'bytedance/v1-pro-text-to-video',
    'tiktok': 'bytedance/v1-pro-text-to-video',
    'reels': 'bytedance/v1-pro-text-to-video',
    'shorts': 'bytedance/v1-pro-text-to-video',

    // Vintage/Retro
    'vintage': 'bytedance/v1-pro-text-to-video',
    'retro': 'bytedance/v1-pro-text-to-video',

    // Default → Bytedance (económico pero bueno)
    'default': 'bytedance/v1-pro-text-to-video'
};

/**
 * Obtiene el modelo recomendado para un estilo
 */
export function getRecommendedModel(styleKey: string): string {
    return STYLE_TO_MODEL[styleKey] || STYLE_TO_MODEL['default'];
}

/**
 * Obtiene información completa del modelo para un estilo
 */
export function getModelInfoForStyle(styleKey: string): VideoModelInfo {
    const modelId = getRecommendedModel(styleKey);
    return VIDEO_MODELS[modelId] || VIDEO_MODELS['runway-gen3'];
}

/**
 * Obtiene todos los modelos de un tier específico
 */
export function getModelsByTier(tier: VideoModelTier): VideoModelInfo[] {
    return Object.values(VIDEO_MODELS).filter(model => model.tier === tier);
}

/**
 * Calcula el costo estimado en créditos para una duración dada
 */
export function estimateCredits(modelId: string, durationSeconds: number): number {
    const model = VIDEO_MODELS[modelId];
    if (!model) return 0;

    // Costo por cada 5 segundos
    const segments = Math.ceil(durationSeconds / 5);
    return model.credits_5s * segments;
}

// Aspect ratios disponibles
export const ASPECT_RATIOS = [
    { id: '16:9', label: 'Horizontal (16:9)', description: 'YouTube, TV' },
    { id: '9:16', label: 'Vertical (9:16)', description: 'TikTok, Reels, Shorts' },
    { id: '1:1', label: 'Cuadrado (1:1)', description: 'Instagram Feed' }
];

// Calidades de video
export const VIDEO_QUALITIES = [
    { id: '720p', label: '720p HD', description: 'Standard HD' },
    { id: '1080p', label: '1080p Full HD', description: 'Alta calidad (más créditos)' }
];

// Duraciones de video
export const VIDEO_DURATIONS = [
    { id: 5, label: '5 segundos', description: 'Clip corto' },
    { id: 10, label: '10 segundos', description: 'Clip estándar' }
];
