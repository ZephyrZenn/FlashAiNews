import React, { useCallback, useEffect, useState } from "react";
import MainCard from "../components/MainCard";
import { useToast } from "../components/toast/useToast";
import { getSetting, updateSetting } from "../services/SettingService";
import { LLMProvider, ModelConfig, Settings } from "../types";

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({
    prompt: "",
    model: {
      name: "",
      model: "",
      provider: LLMProvider.OPENAI,
      apiKey: "",
      baseUrl: "",
      isDefault: false,
    },
  });
//   const [isEditing, setIsEditing] = useState<boolean>(false);
  const { success, error } = useToast();

  useEffect(() => {
    const fetchSettings = async () => {
      const settings = await getSetting();
      setSettings(settings);
    };
    fetchSettings();
  }, []);

  const handlePromptChange = (newPrompt: string) => {
    setSettings((prev) => ({ ...prev, prompt: newPrompt }));
  };

  const handleSave = async () => {
    try {
      await updateSetting(settings);
      success("Prompt saved successfully");
    } catch (err) {
      console.error(err);
      error(`Failed to save prompt ${err}`);
    }
  };

  const handleModelChange = useCallback(
    (field: keyof ModelConfig, value: string | boolean) => {
      setSettings((prev) => ({
        ...prev,
        model: { ...prev.model, [field]: value },
      }));
    },
    []
  );

  return (
    <div className="w-2/3">
      <MainCard>
        <div className="space-y-8">
          {/* Prompt Section */}
          <div>
            <h2 className="text-xl font-semibold mb-4">Prompt Configuration</h2>
            <div className="space-y-4">
              <textarea
                value={settings.prompt}
                onChange={(e) => handlePromptChange(e.target.value)}
                className="w-full h-32 p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your prompt template..."
              />
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Save Prompt
              </button>
            </div>
          </div>

          {/* Models Section */}
          <div className="flex-col">
            <h2 className="text-xl font-semibold">Model Configuration</h2>
            <div className="flex justify-between items-center mt-4">
              {/* <Select.Root
                value={selectedProvider}
                onValueChange={(value) =>
                  setSelectedProvider(value as LLMProvider)
                }
              >
                <Select.Trigger className="inline-flex items-center justify-between px-4 py-2 text-sm font-medium border rounded-md shadow-sm bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
                  <Select.Value placeholder="Select a provider" />
                  <Select.Icon>
                    <ChevronDownIcon />
                  </Select.Icon>
                </Select.Trigger>
                <Select.Portal>
                  <Select.Content className="overflow-hidden bg-white rounded-md shadow-lg border">
                    <Select.Viewport className="p-1">
                      <Select.Group>
                        <Select.Item
                          value={LLMProvider.OPENAI}
                          className="relative flex items-center px-8 py-2 text-sm text-gray-700 rounded hover:bg-gray-100 cursor-pointer"
                        >
                          <Select.ItemText>OpenAI</Select.ItemText>
                          <Select.ItemIndicator className="absolute left-2 inline-flex items-center">
                            <span className="h-2 w-2 rounded-full bg-blue-500" />
                          </Select.ItemIndicator>
                        </Select.Item>
                        <Select.Item
                          value={LLMProvider.GEMINI}
                          className="relative flex items-center px-8 py-2 text-sm text-gray-700 rounded hover:bg-gray-100 cursor-pointer"
                        >
                          <Select.ItemText>Gemini</Select.ItemText>
                          <Select.ItemIndicator className="absolute left-2 inline-flex items-center">
                            <span className="h-2 w-2 rounded-full bg-blue-500" />
                          </Select.ItemIndicator>
                        </Select.Item>
                        <Select.Item
                          value={LLMProvider.DEEPSEEK}
                          className="relative flex items-center px-8 py-2 text-sm text-gray-700 rounded hover:bg-gray-100 cursor-pointer"
                        >
                          <Select.ItemText>DeepSeek</Select.ItemText>
                          <Select.ItemIndicator className="absolute left-2 inline-flex items-center">
                            <span className="h-2 w-2 rounded-full bg-blue-500" />
                          </Select.ItemIndicator>
                        </Select.Item>
                      </Select.Group>
                    </Select.Viewport>
                  </Select.Content>
                </Select.Portal>
              </Select.Root> */}
              {/* <button
                onClick={handleAddModel}
                className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
              >
                Add Model
              </button> */}
            </div>
            <div className="flex justify-between items-center mb-4"></div>
            <div className="space-y-4">
              <div key={0} className="p-4 border rounded-lg space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <ModelItem
                    label="Name"
                    itemType="text"
                    value={settings.model.name}
                    onChange={(e) => handleModelChange("name", e.target.value)}
                    disabled={true}
                  />
                  <ModelItem
                    label="Provider"
                    itemType="text"
                    value={settings.model.provider}
                    onChange={(e) =>
                      handleModelChange("provider", e.target.value)
                    }
                    disabled={true}
                  />
                  <ModelItem
                    label="Base URL"
                    itemType="text"
                    value={settings.model.baseUrl}
                    onChange={(e) =>
                      handleModelChange("baseUrl", e.target.value)
                    }
                    disabled={true}
                  />
                </div>
                <div className="flex justify-between items-center">
                  {/* <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={model.isDefault}
                        onChange={() => handleSetDefault(model.id)}
                        className="rounded focus:ring-blue-500"
                        disabled={isEditing !== model.id}
                      />
                      <span className="text-sm text-gray-700">
                        Set as default
                      </span>
                    </label> */}
                  {/* {isEditing ? (
                    <button
                      onClick={handleSave}
                      className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                      Save
                    </button>
                  ) : (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                    >
                      Edit
                    </button>
                  )} */}
                </div>
              </div>
            </div>
          </div>
        </div>
      </MainCard>
    </div>
  );
}

interface ModelItemProps {
  label: string;
  itemType: "text" | "url";
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  disabled: boolean;
}

const ModelItem = React.memo(
  ({ label, itemType, value, onChange, disabled }: ModelItemProps) => {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
        <input
          type={itemType}
          value={value}
          onChange={onChange}
          className="w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={disabled}
        />
      </div>
    );
  }
);
