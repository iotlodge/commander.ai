/**
 * Agent Model Settings Modal
 * Allows users to view and change an agent's LLM model configuration
 */

"use client";

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAgentModels } from '@/lib/hooks/use-agent-models';
import { ProviderIcon } from '@/components/ui/provider-icon';
import type { AgentModelConfig, ApprovedModel, AgentModelUpdate } from '@/lib/types';

interface AgentModelModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentId: string;
  agentNickname: string;
}

export function AgentModelModal({
  open,
  onOpenChange,
  agentId,
  agentNickname,
}: AgentModelModalProps) {
  const { loading, error, fetchModelConfig, updateModelConfig, fetchApprovedModels } = useAgentModels();

  const [currentConfig, setCurrentConfig] = useState<AgentModelConfig | null>(null);
  const [approvedModels, setApprovedModels] = useState<ApprovedModel[]>([]);

  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [temperature, setTemperature] = useState<number>(0.7);
  const [maxTokens, setMaxTokens] = useState<number>(2000);

  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Load current config and approved models when modal opens
  useEffect(() => {
    if (open) {
      loadData();
    }
  }, [open, agentId]);

  const loadData = async () => {
    setSaveSuccess(false);
    setSaveError(null);

    // Load approved models first
    const models = await fetchApprovedModels();
    setApprovedModels(models);

    // Load current config
    const config = await fetchModelConfig(agentId);
    if (config) {
      setCurrentConfig(config);
      // Set these AFTER we have the data to ensure Select components update
      setSelectedProvider(config.provider);
      setSelectedModel(config.model_name);
      setTemperature(config.temperature);
      setMaxTokens(config.max_tokens);
    }
  };

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);
    // Reset model selection when provider changes
    setSelectedModel('');
  };

  const handleSave = async () => {
    if (!selectedProvider || !selectedModel) {
      setSaveError('Please select a provider and model');
      return;
    }

    setSaveSuccess(false);
    setSaveError(null);

    const update: AgentModelUpdate = {
      provider: selectedProvider,
      model_name: selectedModel,
      temperature,
      max_tokens: maxTokens,
    };

    const result = await updateModelConfig(agentId, update);

    if (result) {
      setSaveSuccess(true);
      setCurrentConfig(result);

      // Close modal after 1.5 seconds
      setTimeout(() => {
        onOpenChange(false);
      }, 1500);
    } else {
      setSaveError(error || 'Failed to update model configuration');
    }
  };

  // Get available providers
  const providers = Array.from(new Set(approvedModels.map(m => m.provider)));

  // Get models for selected provider
  const availableModels = approvedModels.filter(m => m.provider === selectedProvider);

  // Get current model details
  const selectedModelDetails = approvedModels.find(
    m => m.provider === selectedProvider && m.model_name === selectedModel
  );

  const hasChanges = currentConfig && (
    selectedProvider !== currentConfig.provider ||
    selectedModel !== currentConfig.model_name ||
    temperature !== currentConfig.temperature ||
    maxTokens !== currentConfig.max_tokens
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span>Model Settings</span>
            <span className="text-muted-foreground">@{agentNickname}</span>
          </DialogTitle>
          <DialogDescription>
            Configure the LLM model and parameters for this agent
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Current Configuration Display */}
          {currentConfig && (
            <div className="rounded-lg border border-border bg-muted/20 p-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Current Model</p>
                  <div className="flex items-center gap-2 mt-1">
                    <ProviderIcon provider={currentConfig.provider} size={16} />
                    <span className="text-sm text-muted-foreground">
                      {currentConfig.model_display_name || currentConfig.model_name}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">Version</p>
                  <p className="text-sm font-mono">{currentConfig.version}</p>
                </div>
              </div>
            </div>
          )}

          {/* Provider Selection */}
          <div className="space-y-2">
            <Label htmlFor="provider">Provider</Label>
            <Select value={selectedProvider} onValueChange={handleProviderChange}>
              <SelectTrigger id="provider">
                <SelectValue placeholder="Select provider" />
              </SelectTrigger>
              <SelectContent>
                {providers.map(provider => (
                  <SelectItem key={provider} value={provider}>
                    <div className="flex items-center gap-2">
                      <ProviderIcon provider={provider} size={16} />
                      <span className="capitalize">{provider}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Model Selection */}
          <div className="space-y-2">
            <Label htmlFor="model">Model</Label>
            <Select
              value={selectedModel}
              onValueChange={setSelectedModel}
              disabled={!selectedProvider}
            >
              <SelectTrigger id="model">
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent>
                {availableModels.map(model => (
                  <SelectItem key={model.model_name} value={model.model_name}>
                    <div className="space-y-0.5">
                      <div>{model.model_display_name || model.model_name}</div>
                      {model.description && (
                        <div className="text-xs text-muted-foreground">
                          {model.description}
                        </div>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Model Details */}
            {selectedModelDetails && (
              <div className="text-xs text-muted-foreground space-y-1 mt-2">
                {selectedModelDetails.context_window && (
                  <div>Context: {selectedModelDetails.context_window.toLocaleString()} tokens</div>
                )}
                {selectedModelDetails.supports_function_calling && (
                  <div className="flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" />
                    Function calling supported
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Temperature */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="temperature">Temperature</Label>
              <span className="text-sm text-muted-foreground">{temperature.toFixed(2)}</span>
            </div>
            <Slider
              id="temperature"
              min={0}
              max={1}
              step={0.05}
              value={[temperature]}
              onValueChange={(values) => setTemperature(values[0])}
            />
            <p className="text-xs text-muted-foreground">
              Lower = more focused, Higher = more creative
            </p>
          </div>

          {/* Max Tokens */}
          <div className="space-y-2">
            <Label htmlFor="max-tokens">Max Tokens</Label>
            <Input
              id="max-tokens"
              type="number"
              min={100}
              max={32000}
              step={100}
              value={maxTokens}
              onChange={(e) => setMaxTokens(parseInt(e.target.value) || 2000)}
            />
            <p className="text-xs text-muted-foreground">
              Maximum response length
            </p>
          </div>

          {/* Success/Error Messages */}
          {saveSuccess && (
            <Alert className="bg-green-500/10 border-green-500/50">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <AlertDescription className="text-green-500">
                Model updated successfully! Agent reloaded.
              </AlertDescription>
            </Alert>
          )}

          {saveError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{saveError}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={loading || !hasChanges || saveSuccess}
          >
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {loading ? 'Updating...' : 'Save & Reload Agent'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
