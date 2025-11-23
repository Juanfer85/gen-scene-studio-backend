import React, { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Volume2, Video, Image, Package, Briefcase, Plus, Mic, Layers, Sparkles } from 'lucide-react';

const Index: React.FC = () => {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  const features = [
    {
      id: 'voz',
      title: 'Generador de Voz',
      description: 'Convierte texto a audio de alta calidad utilizando inteligencia artificial',
      icon: Mic,
      href: '/Voz',
      color: 'from-blue-500 to-blue-600',
      stats: ['Calidad profesional', 'Múltiples voces', 'Control de velocidad']
    },
    {
      id: 'timeline',
      title: 'Timeline de Video',
      description: 'Crea videos profesionales combinando imágenes, audio y efectos visuales',
      icon: Video,
      href: '/Timeline',
      color: 'from-purple-500 to-purple-600',
      stats: ['Editor visual', 'Efectos Ken Burns', 'Sincronización automática']
    },
    {
      id: 'storyboard',
      title: 'Storyboard con IA',
      description: 'Genera secuencias de imágenes para storyboards con prompts de texto',
      icon: Image,
      href: '/Storyboard',
      color: 'from-green-500 to-green-600',
      stats:['Alta calidad', 'Estilos variados', 'Generación en lote']
    },
    {
      id: 'lote',
      title: 'Procesamiento por Lotes',
      description: 'Procesa múltiples imágenes simultáneamente usando archivos CSV',
      icon: Package,
      href: '/Lote',
      color: 'from-orange-500 to-orange-600',
      stats: ['Importación CSV', 'Procesamiento masivo', 'Seguimiento en tiempo real']
    },
    {
      id: 'jobs',
      title: 'Monitor de Trabajos',
      description: 'Visualiza y gestiona el estado de todos tus trabajos en curso',
      icon: Briefcase,
      href: '/Jobs',
      color: 'from-red-500 to-red-600',
      stats: ['Panel completo', 'Auto-refresh', 'Filtros avanzados']
    },
    {
      id: 'newjob',
      title: 'Nuevo Trabajo Automatizado',
      description: 'Crea flujos de trabajo automatizados con múltiples pasos',
      icon: Layers,
      href: '/NewJob',
      color: 'from-indigo-500 to-indigo-600',
      stats: ['Plantillas', 'Flujos personalizados', 'Ejecución secuencial']
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900">GenScene Studio</h1>
            </div>
            <nav className="flex items-center gap-6">
              <Link href="/Voz">
                <Button variant="ghost" size="sm">Voz</Button>
              </Link>
              <Link href="/Timeline">
                <Button variant="ghost" size="sm">Timeline</Button>
              </Link>
              <Link href="/Storyboard">
                <Button variant="ghost" size="sm">Storyboard</Button>
              </Link>
              <Link href="/Lote">
                <Button variant="ghost" size="sm">Lote</Button>
              </Link>
              <Link href="/Jobs">
                <Button variant="ghost" size="sm">Jobs</Button>
              </Link>
              <Link href="/NewJob">
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Nuevo Job
                </Button>
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Plataforma de Creación de
            <span className="bg-gradient-to-r from-blue-500 to-purple-600 text-transparent bg-clip-text">
              {' '}Contenido con IA
            </span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            Genera voz, imágenes y videos de alta calidad utilizando inteligencia artificial.
            Crea storyboards, procesa en lote y automatiza tus flujos de trabajo.
          </p>
          <div className="flex justify-center gap-4">
            <Link href="/NewJob">
              <Button size="lg" className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700">
                <Plus className="h-5 w-5 mr-2" />
                Crear Nuevo Proyecto
              </Button>
            </Link>
            <Link href="/Jobs">
              <Button variant="outline" size="lg">
                <Briefcase className="h-5 w-5 mr-2" />
                Ver Trabajos
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Link key={feature.id} href={feature.href}>
                <Card
                  className={`h-full cursor-pointer transition-all duration-300 hover:shadow-lg hover:scale-105 border-0 ${
                    hoveredCard === feature.id ? 'ring-2 ring-offset-2 ring-blue-500' : ''
                  }`}
                  onMouseEnter={() => setHoveredCard(feature.id)}
                  onMouseLeave={() => setHoveredCard(null)}
                >
                  <CardHeader className="pb-4">
                    <div className={`w-12 h-12 rounded-lg bg-gradient-to-r ${feature.color} flex items-center justify-center mb-4`}>
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <CardTitle className="text-xl mb-2">{feature.title}</CardTitle>
                    <CardDescription className="text-base leading-relaxed">
                      {feature.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-gray-700">Características:</div>
                      <ul className="space-y-1">
                        {feature.stats.map((stat, index) => (
                          <li key={index} className="flex items-center gap-2 text-sm text-gray-600">
                            <div className="w-1 h-1 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full"></div>
                            {stat}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="mt-4 pt-4 border-t">
                      <Button variant="ghost" className="w-full justify-start text-blue-600 hover:text-blue-700 hover:bg-blue-50">
                        {feature.title} →
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>

        {/* Stats Section */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="text-center">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-blue-600 mb-2">10K+</div>
              <div className="text-sm text-gray-600">Videos Generados</div>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-purple-600 mb-2">50K+</div>
              <div className="text-sm text-gray-600">Imágenes Creadas</div>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-green-600 mb-2">100K+</div>
              <div className="text-sm text-gray-600">Minutos de Audio</div>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="pt-6">
              <div className="text-3xl font-bold text-orange-600 mb-2">99.9%</div>
              <div className="text-sm text-gray-600">Uptime</div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-500 text-sm">
            © 2024 GenScene Studio. Plataforma de creación de contenido con IA.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;