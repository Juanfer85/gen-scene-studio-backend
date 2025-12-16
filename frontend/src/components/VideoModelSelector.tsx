import { useState, useEffect } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Info, Zap, Crown, Coins } from 'lucide-react';
import {
    VIDEO_MODELS,
    VideoModelInfo,
    VideoModelTier,
    getRecommendedModel,
    getModelInfoForStyle,
    estimateCredits
} from '@/types/videoModels';

interface VideoModelSelectorProps {
    styleKey?: string;
    value?: string | null;
    onChange: (modelId: string | null) => void;
    videoDuration?: number;
    disabled?: boolean;
    showAutoOption?: boolean;
}

const TierIcon = ({ tier }: { tier: VideoModelTier }) => {
    switch (tier) {
        case 'premium':
            return <Crown className="w-4 h-4 text-yellow-500" />;
        case 'high':
            return <Zap className="w-4 h-4 text-blue-500" />;
        case 'economic':
            return <Coins className="w-4 h-4 text-green-500" />;
    }
};

const tierStyles: Record<VideoModelTier, string> = {
    premium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    high: 'bg-blue-100 text-blue-800 border-blue-300',
    economic: 'bg-green-100 text-green-800 border-green-300'
};

const tierLabelsMap: Record<VideoModelTier, string> = {
    premium: 'Premium',
    high: 'Alta Calidad',
    economic: 'Económico'
};

const TierBadge = ({ tier }: { tier: VideoModelTier }) => {
    return (
        <Badge variant="outline" className={`text-xs ${tierStyles[tier]}`}>
            {tierLabelsMap[tier]}
        </Badge>
    );
};

export function VideoModelSelector({
    styleKey = 'default',
    value,
    onChange,
    videoDuration = 5,
    disabled = false,
    showAutoOption = true
}: VideoModelSelectorProps) {
    const [recommendedModel, setRecommendedModel] = useState<string>('runway-gen3');
    const [recommendedModelInfo, setRecommendedModelInfo] = useState<VideoModelInfo | null>(null);

    useEffect(() => {
        const modelId = getRecommendedModel(styleKey);
        const modelInfo = getModelInfoForStyle(styleKey);
        setRecommendedModel(modelId);
        setRecommendedModelInfo(modelInfo);
    }, [styleKey]);

    const effectiveModel = value || recommendedModel;
    const effectiveModelInfo = VIDEO_MODELS[effectiveModel] || VIDEO_MODELS['runway-gen3'];

    // Agrupar modelos por tier con tipos correctos
    const modelsByTier = Object.values(VIDEO_MODELS).reduce<Record<VideoModelTier, VideoModelInfo[]>>((acc, model) => {
        if (!acc[model.tier]) acc[model.tier] = [];
        acc[model.tier].push(model);
        return acc;
    }, { premium: [], high: [], economic: [] });

    const tierOrder: VideoModelTier[] = ['premium', 'high', 'economic'];
    const tierLabels: Record<VideoModelTier, string> = {
        premium: '👑 Premium',
        high: '⚡ Alta Calidad',
        economic: '💰 Económico'
    };

    return (
        <div className="space-y-2">
            <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700">
                    Modelo de Video
                </label>
                <div className="group relative">
                    <Info className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" />
                    <div className="absolute right-0 top-6 z-10 hidden group-hover:block w-64 p-2 text-xs bg-gray-900 text-white rounded shadow-lg">
                        El modelo se selecciona automáticamente según el estilo,
                        pero puedes elegir uno específico si lo prefieres.
                    </div>
                </div>
            </div>

            <Select
                value={value || 'auto'}
                onValueChange={(val) => onChange(val === 'auto' ? null : val)}
                disabled={disabled}
            >
                <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar modelo...">
                        <div className="flex items-center gap-2">
                            {value === null || value === 'auto' || !value ? (
                                <>
                                    <span className="text-blue-600">🪄 Automático</span>
                                    <span className="text-gray-400 text-xs">
                                        ({recommendedModelInfo?.name || 'Runway Gen-3'})
                                    </span>
                                </>
                            ) : (
                                <>
                                    <TierIcon tier={effectiveModelInfo.tier} />
                                    <span>{effectiveModelInfo.name}</span>
                                </>
                            )}
                        </div>
                    </SelectValue>
                </SelectTrigger>
                <SelectContent>
                    {showAutoOption && (
                        <div>
                            <div className="px-2 py-1.5 text-sm font-semibold text-blue-600 bg-blue-50">
                                🪄 Recomendado
                            </div>
                            <SelectItem value="auto">
                                <div className="flex flex-col">
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium">Automático</span>
                                        <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700">
                                            Estilo: {styleKey}
                                        </Badge>
                                    </div>
                                    <span className="text-xs text-gray-500">
                                        Usa {recommendedModelInfo?.name} ({estimateCredits(recommendedModel, videoDuration)} créditos)
                                    </span>
                                </div>
                            </SelectItem>
                        </div>
                    )}

                    {tierOrder.map((tier) => (
                        modelsByTier[tier] && modelsByTier[tier].length > 0 && (
                            <div key={tier}>
                                <div className="px-2 py-1.5 text-sm font-semibold text-gray-600 bg-gray-50">
                                    {tierLabels[tier]}
                                </div>
                                {modelsByTier[tier].map((model: VideoModelInfo) => (
                                    <SelectItem key={model.id} value={model.id}>
                                        <div className="flex flex-col">
                                            <div className="flex items-center gap-2">
                                                <TierIcon tier={model.tier} />
                                                <span className="font-medium">{model.name}</span>
                                                {model.id === recommendedModel && (
                                                    <Badge variant="outline" className="text-xs bg-green-50 text-green-700">
                                                        Recomendado
                                                    </Badge>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2 text-xs text-gray-500">
                                                <span>{model.description}</span>
                                                <span>•</span>
                                                <span className="font-medium">
                                                    ~{estimateCredits(model.id, videoDuration)} créditos
                                                </span>
                                            </div>
                                        </div>
                                    </SelectItem>
                                ))}
                            </div>
                        )
                    ))}
                </SelectContent>
            </Select>

            <div className="flex items-center justify-between text-xs text-gray-500 bg-gray-50 rounded px-2 py-1">
                <div className="flex items-center gap-2">
                    <TierIcon tier={effectiveModelInfo.tier} />
                    <span>{effectiveModelInfo.name}</span>
                    <TierBadge tier={effectiveModelInfo.tier} />
                </div>
                <div className="flex items-center gap-1">
                    <span>~{estimateCredits(effectiveModel, videoDuration)} créditos</span>
                    <span>•</span>
                    <span>Máx {effectiveModelInfo.max_duration}s</span>
                </div>
            </div>
        </div>
    );
}

export default VideoModelSelector;
