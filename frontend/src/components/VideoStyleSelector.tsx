import React, { useState, useEffect } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

interface StyleOption {
  id: string;
  label: string;
  category: string;
  motion: string;
  grain: string;
  aspectRatio: string;
  prompt: string;
  negative: string;
}

interface VideoStyleSelectorProps {
  value?: string;
  onChange: (styleId: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export function VideoStyleSelector({
  value,
  onChange,
  placeholder = "Seleccionar estilo de video...",
  disabled = false
}: VideoStyleSelectorProps) {
  const [styles, setStyles] = useState<StyleOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStyles();
  }, []);

  const loadStyles = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${import.meta.env.VITE_API_URL}/styles`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': import.meta.env.VITE_API_KEY,
        },
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setStyles(data);
    } catch (err) {
      console.error('Error al cargar estilos:', err);
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  // Agrupar estilos por categoría
  const stylesByCategory = styles.reduce((acc, style) => {
    if (!acc[style.category]) {
      acc[style.category] = [];
    }
    acc[style.category].push(style);
    return acc;
  }, {} as Record<string, StyleOption[]>);

  const categoryLabels: Record<string, string> = {
    realistic: 'Realista',
    animated: 'Animación',
    vintage: 'Vintage',
    artistic: 'Artístico',
  };

  if (loading) {
    return (
      <Select disabled>
        <SelectTrigger>
          <SelectValue placeholder="Cargando estilos de video..." />
        </SelectTrigger>
      </Select>
    );
  }

  if (error) {
    return (
      <Select disabled>
        <SelectTrigger className="border-red-500">
          <SelectValue placeholder={`⚠️ Error: ${error}`} />
        </SelectTrigger>
      </Select>
    );
  }

  return (
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {Object.entries(stylesByCategory).map(([category, categoryStyles]) => (
          <div key={category}>
            <div className="px-2 py-1.5 text-sm font-semibold text-gray-500 bg-gray-50">
              {categoryLabels[category] || category}
            </div>
            {categoryStyles.map((style) => (
              <SelectItem key={style.id} value={style.id}>
                <div className="flex flex-col items-start">
                  <span className="font-medium">{style.label}</span>
                  <span className="text-xs text-gray-500">
                    {style.motion} • {style.grain} • {style.aspectRatio}
                  </span>
                </div>
              </SelectItem>
            ))}
          </div>
        ))}
      </SelectContent>
    </Select>
  );
}

export default VideoStyleSelector;