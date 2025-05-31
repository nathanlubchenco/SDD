import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Textarea } from './ui/textarea';
import { Input } from './ui/input';
import { Lightbulb, CheckCircle, AlertTriangle, Plus, Edit3, Eye } from 'lucide-react';
import { useSpecificationStore } from '../store/specificationStore';

interface ScenarioComponent {
  type: string;
  content: string;
  confidence: number;
  entities: string[];
  relationships: string[];
}

interface ScenarioSuggestion {
  component_type: string;
  suggestion: string;
  reasoning: string;
  confidence: number;
  context_entities: string[];
}

interface ExtractedScenario {
  id: string;
  title: string;
  given: ScenarioComponent[];
  when: ScenarioComponent[];
  then: ScenarioComponent[];
  confidence: number;
  completion_suggestions: ScenarioSuggestion[];
  validation_issues: string[];
}

interface ScenarioBuilderProps {
  isVisible: boolean;
  className?: string;
}

export const ScenarioBuilder: React.FC<ScenarioBuilderProps> = ({ 
  isVisible, 
  className = "" 
}) => {
  const { entities, scenarios, addScenario } = useSpecificationStore();
  const [currentScenario, setCurrentScenario] = useState({
    title: '',
    given: '',
    when: '',
    then: ''
  });
  const [extractedScenarios, setExtractedScenarios] = useState<ExtractedScenario[]>([]);
  const [suggestions, setSuggestions] = useState<ScenarioSuggestion[]>([]);
  const [validationIssues, setValidationIssues] = useState<string[]>([]);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionMode, setExtractionMode] = useState<'manual' | 'auto'>('auto');

  // Auto-extract scenarios as user types
  const extractScenariosFromText = useCallback(async (text: string) => {
    if (!text.trim() || extractionMode !== 'auto') return;

    setIsExtracting(true);
    try {
      const response = await fetch('/api/scenarios/extract', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          entities: entities.map(e => e.name)
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setExtractedScenarios(data.scenarios || []);
      }
    } catch (error) {
      console.error('Error extracting scenarios:', error);
    } finally {
      setIsExtracting(false);
    }
  }, [entities, extractionMode]);

  // Generate completion suggestions
  const generateSuggestions = useCallback(async () => {
    if (!currentScenario.given && !currentScenario.when && !currentScenario.then) {
      setSuggestions([]);
      setValidationIssues([]);
      return;
    }

    try {
      const response = await fetch('/api/scenarios/suggest-completion', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          given: currentScenario.given,
          when: currentScenario.when,
          then: currentScenario.then,
          entities: entities.map(e => e.name)
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.completion_suggestions || []);
        setValidationIssues(data.validation_issues || []);
      }
    } catch (error) {
      console.error('Error generating suggestions:', error);
    }
  }, [currentScenario, entities]);

  // Debounced text extraction
  useEffect(() => {
    const timer = setTimeout(() => {
      const fullText = `${currentScenario.title} ${currentScenario.given} ${currentScenario.when} ${currentScenario.then}`.trim();
      if (fullText) {
        extractScenariosFromText(fullText);
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [currentScenario, extractScenariosFromText]);

  // Generate suggestions when scenario changes
  useEffect(() => {
    const timer = setTimeout(() => {
      generateSuggestions();
    }, 500);

    return () => clearTimeout(timer);
  }, [generateSuggestions]);

  const handleInputChange = (field: keyof typeof currentScenario, value: string) => {
    setCurrentScenario(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const applySuggestion = (suggestion: ScenarioSuggestion) => {
    setCurrentScenario(prev => ({
      ...prev,
      [suggestion.component_type]: suggestion.suggestion
    }));
  };

  const saveCurrentScenario = () => {
    if (!currentScenario.title || !currentScenario.when || !currentScenario.then) {
      return;
    }

    addScenario({
      title: currentScenario.title,
      given: currentScenario.given,
      when: currentScenario.when,
      then: currentScenario.then,
      status: 'draft',
      entities: entities.map(e => e.name).filter(name => 
        currentScenario.given.toLowerCase().includes(name.toLowerCase()) ||
        currentScenario.when.toLowerCase().includes(name.toLowerCase()) ||
        currentScenario.then.toLowerCase().includes(name.toLowerCase())
      )
    });

    // Reset form
    setCurrentScenario({
      title: '',
      given: '',
      when: '',
      then: ''
    });
  };

  const importExtractedScenario = (scenario: ExtractedScenario) => {
    setCurrentScenario({
      title: scenario.title,
      given: scenario.given.map(g => g.content).join(' | '),
      when: scenario.when.map(w => w.content).join(' | '),
      then: scenario.then.map(t => t.content).join(' | ')
    });
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800';
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getSuggestionTypeIcon = (type: string) => {
    switch (type) {
      case 'given': return '🎯';
      case 'when': return '⚡';
      case 'then': return '✅';
      default: return '💡';
    }
  };

  if (!isVisible) return null;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Mode Toggle */}
      <div className="flex items-center gap-2 mb-4">
        <Button
          variant={extractionMode === 'auto' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setExtractionMode('auto')}
        >
          <Eye className="w-4 h-4 mr-1" />
          Auto Extract
        </Button>
        <Button
          variant={extractionMode === 'manual' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setExtractionMode('manual')}
        >
          <Edit3 className="w-4 h-4 mr-1" />
          Manual
        </Button>
      </div>

      {/* Scenario Builder */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="w-5 h-5" />
            Build New Scenario
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Scenario Title
            </label>
            <Input
              value={currentScenario.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              placeholder="e.g., User logs in successfully"
              className="w-full"
            />
          </div>

          {/* Given */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Given (Preconditions)
            </label>
            <Textarea
              value={currentScenario.given}
              onChange={(e) => handleInputChange('given', e.target.value)}
              placeholder="e.g., user has valid credentials and is on the login page"
              className="min-h-[60px]"
            />
          </div>

          {/* When */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              When (Action) *
            </label>
            <Textarea
              value={currentScenario.when}
              onChange={(e) => handleInputChange('when', e.target.value)}
              placeholder="e.g., user enters username and password and clicks login"
              className="min-h-[60px]"
            />
          </div>

          {/* Then */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Then (Expected Result) *
            </label>
            <Textarea
              value={currentScenario.then}
              onChange={(e) => handleInputChange('then', e.target.value)}
              placeholder="e.g., user is authenticated and redirected to dashboard"
              className="min-h-[60px]"
            />
          </div>

          {/* Validation Issues */}
          {validationIssues.length > 0 && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-yellow-600" />
                <span className="text-sm font-medium text-yellow-800">Validation Issues</span>
              </div>
              <ul className="text-sm text-yellow-700 space-y-1">
                {validationIssues.map((issue, index) => (
                  <li key={index}>• {issue}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Save Button */}
          <Button 
            onClick={saveCurrentScenario}
            disabled={!currentScenario.title || !currentScenario.when || !currentScenario.then}
            className="w-full"
          >
            <CheckCircle className="w-4 h-4 mr-2" />
            Save Scenario
          </Button>
        </CardContent>
      </Card>

      {/* Completion Suggestions */}
      {suggestions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="w-5 h-5" />
              Smart Suggestions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {suggestions.slice(0, 4).map((suggestion, index) => (
                <div
                  key={index}
                  className="p-3 border border-gray-200 rounded-md hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => applySuggestion(suggestion)}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-lg">{getSuggestionTypeIcon(suggestion.component_type)}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-xs">
                          {suggestion.component_type.toUpperCase()}
                        </Badge>
                        <Badge 
                          className={`text-xs ${getConfidenceColor(suggestion.confidence)}`}
                        >
                          {Math.round(suggestion.confidence * 100)}%
                        </Badge>
                      </div>
                      <p className="text-sm font-medium text-gray-900 mb-1">
                        {suggestion.suggestion}
                      </p>
                      <p className="text-xs text-gray-600">
                        {suggestion.reasoning}
                      </p>
                      {suggestion.context_entities.length > 0 && (
                        <div className="flex gap-1 mt-2">
                          {suggestion.context_entities.slice(0, 3).map((entity, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {entity}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Auto-Extracted Scenarios */}
      {extractionMode === 'auto' && extractedScenarios.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye className="w-5 h-5" />
              Auto-Detected Scenarios
              {isExtracting && (
                <span className="text-sm text-gray-500">(Analyzing...)</span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {extractedScenarios.map((scenario, index) => (
                <div
                  key={index}
                  className="p-3 border border-blue-200 rounded-md bg-blue-50 hover:bg-blue-100 cursor-pointer transition-colors"
                  onClick={() => importExtractedScenario(scenario)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium text-gray-900">{scenario.title}</h4>
                    <Badge className={getConfidenceColor(scenario.confidence)}>
                      {Math.round(scenario.confidence * 100)}%
                    </Badge>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    {scenario.given.length > 0 && (
                      <div>
                        <span className="font-medium text-blue-700">Given:</span>
                        <span className="ml-2 text-gray-700">
                          {scenario.given.map(g => g.content).join(' | ')}
                        </span>
                      </div>
                    )}
                    {scenario.when.length > 0 && (
                      <div>
                        <span className="font-medium text-blue-700">When:</span>
                        <span className="ml-2 text-gray-700">
                          {scenario.when.map(w => w.content).join(' | ')}
                        </span>
                      </div>
                    )}
                    {scenario.then.length > 0 && (
                      <div>
                        <span className="font-medium text-blue-700">Then:</span>
                        <span className="ml-2 text-gray-700">
                          {scenario.then.map(t => t.content).join(' | ')}
                        </span>
                      </div>
                    )}
                  </div>

                  {scenario.completion_suggestions.length > 0 && (
                    <div className="mt-2">
                      <Badge variant="outline" className="text-xs">
                        {scenario.completion_suggestions.length} suggestions available
                      </Badge>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Current Scenarios Summary */}
      {scenarios.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Current Scenarios ({scenarios.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {scenarios.slice(-3).map((scenario, index) => (
                <div key={index} className="p-2 bg-gray-50 rounded text-sm">
                  <span className="font-medium">{scenario.title}</span>
                  <Badge variant="secondary" className="ml-2 text-xs">
                    {scenario.status}
                  </Badge>
                </div>
              ))}
              {scenarios.length > 3 && (
                <p className="text-xs text-gray-500">
                  ... and {scenarios.length - 3} more
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};