import { useState, useEffect } from 'react'
import './App.css'
import { API_URL } from './constants'

// Base field configuration that all types share
interface BaseFieldConfig {
  required: boolean;
  label: string;
  key: string;
}

// Specific field type configurations
interface StringFieldConfig extends BaseFieldConfig {
  type: 'string';
  default_value: string;
  min_length?: number;
  max_length?: number;
}

interface EnumFieldConfig extends BaseFieldConfig {
  type: 'enum';
  default_value: string;
  options: string[];
}

interface IntFieldConfig extends BaseFieldConfig {
  type: 'int';
  default_value: number;
  min_value?: number;
  max_value?: number;
}

interface FloatFieldConfig extends BaseFieldConfig {
  type: 'float';
  default_value: number;
  min_value?: number;
  max_value?: number;
}

interface ListFieldConfig extends BaseFieldConfig {
  type: 'list';
  default_value: string[];
  min_length?: number;
  max_length?: number;
}

interface DictFieldConfig extends BaseFieldConfig {
  type: 'dict';
  default_value: Record<string, any>;
  fields: ConfigSchema[];
}

// Union type of all possible field configurations
type ConfigSchema = 
  | StringFieldConfig 
  | EnumFieldConfig 
  | IntFieldConfig 
  | FloatFieldConfig 
  | ListFieldConfig 
  | DictFieldConfig;

interface ComponentConfig {
  name: string;
  class_path: string;
  schema: ConfigSchema[];
}

function App() {
  const [configs, setConfigs] = useState<{
    description_model?: { args: Record<string, any> },
    image_model?: { args: Record<string, any> },
    topic_strategy?: { args: Record<string, any> },
    artifact_directory?: string
  }>({})
  const [selectedDescriptionModel, setSelectedDescriptionModel] = useState("Meta")
  const [selectedImageModel, setSelectedImageModel] = useState("Amazon Titan")
  const [selectedTopicStrategy, setSelectedTopicStrategy] = useState("Random Ad Lib")
  const [batteryLevel, setBatteryLevel] = useState<number | null>(null)
  const [isPowered, setIsPowered] = useState(true)
  const [loading, setLoading] = useState(true)
  const [modelOptions, setModelOptions] = useState<Record<string, string[]>>({
    Meta: [],
    Anthropic: [],
    "Amazon Titan": [],
    "Stable Diffusion": [],
    "Stable Image Ultra": []
  })
  const [toast, setToast] = useState<{message: string, visible: boolean}>({
    message: '',
    visible: false
  });

  // Move DESCRIPTION_MODEL_SCHEMAS inside the component
  const DESCRIPTION_MODEL_SCHEMAS: ComponentConfig[] = [
    {
      name: "Meta",
      class_path: "piframe.models.Meta",
      schema: [
        {
          type: "enum",
          label: "Model ID",
          key: "model_id",
          required: true,
          default_value: modelOptions.Meta[0] || "meta.llama2-13b-chat-v1",
          options: modelOptions.Meta.length ? modelOptions.Meta : ["meta.llama2-13b-chat-v1"]
        },
        {
          type: "int",
          label: "Max Generation Length",
          key: "max_gen_len",
          required: true,
          default_value: 100,
          min_value: 1,
          max_value: 2048
        },
        {
          type: "float",
          label: "Temperature",
          key: "temperature",
          required: true,
          default_value: 0.7,
          min_value: 0.0,
          max_value: 1.0
        }
      ]
    },
    {
      name: "Anthropic",
      class_path: "piframe.models.Anthropic",
      schema: [
        {
          type: "enum",
          label: "Model ID",
          key: "model_id",
          required: true,
          default_value: modelOptions.Anthropic[0] || "anthropic.claude-3-sonnet-20240229-v1:0",
          options: modelOptions.Anthropic.length ? modelOptions.Anthropic : ["anthropic.claude-3-sonnet-20240229-v1:0"]
        },
        {
          type: "enum",
          label: "Anthropic Version",
          key: "anthropic_version",
          required: true,
          default_value: "bedrock-2023-05-31",
          options: ["bedrock-2023-05-31"]
        },
        {
          type: "int",
          label: "Max Tokens",
          key: "max_tokens",
          required: true,
          default_value: 1000,
          min_value: 1,
          max_value: 4096
        },
        {
          type: "float",
          label: "Temperature",
          key: "temperature",
          required: true,
          default_value: 0.7,
          min_value: 0.0,
          max_value: 1.0
        }
      ]
    }
  ];

  // Add this effect to fetch models when component mounts
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch(`${API_URL}/api/models`)
        const data = await response.json()
        
        // Group models by provider
        const modelsByProvider: Record<string, string[]> = {
          Meta: [],
          Anthropic: [],
          "Amazon Titan": [],
          "Stable Diffusion": [],
          "Stable Image Ultra": []
        }
        
        data.models.forEach((model: any) => {
          const modelId = model.modelId
          switch(model.providerName) {
            case "Meta":
              modelsByProvider.Meta.push(modelId)
              break
            case "Anthropic":
              modelsByProvider.Anthropic.push(modelId)
              break
            case "Amazon":
              if (modelId.includes("titan-image")) {
                modelsByProvider["Amazon Titan"].push(modelId)
              }
              break
          }
        })
        
        // Preserve current model_id selections when updating options
        setConfigs(prevConfigs => ({
          ...prevConfigs,
          description_model: {
            ...prevConfigs.description_model,
            args: {
              ...prevConfigs.description_model?.args,
              model_id: prevConfigs.description_model?.args?.model_id || modelsByProvider[selectedDescriptionModel]?.[0]
            }
          },
          image_model: {
            ...prevConfigs.image_model,
            args: {
              ...prevConfigs.image_model?.args,
              model_id: prevConfigs.image_model?.args?.model_id || modelsByProvider[selectedImageModel]?.[0]
            }
          }
        }))
        
        setModelOptions(modelsByProvider)
      } catch (error) {
        console.error('Failed to fetch models:', error)
      }
    }
    
    fetchModels()
  }, [selectedDescriptionModel, selectedImageModel])

  // Update the schemas to use dynamic options
  const IMAGE_MODEL_SCHEMAS: ComponentConfig[] = [
    {
      name: "Amazon Titan",
      class_path: "piframe.models.TitanImage",
      schema: [
        {
          type: "enum",
          label: "Model ID",
          key: "model_id",
          required: true,
          default_value: modelOptions["Amazon Titan"][0] || "amazon.titan-image-generator-v1",
          options: modelOptions["Amazon Titan"].length ? modelOptions["Amazon Titan"] : ["amazon.titan-image-generator-v1"]
        },
        {
          type: "dict",
          label: "Image Generation Config",
          key: "imageGenerationConfig",
          required: true,
          default_value: {
            quality: "standard",
            width: 1024,
            height: 1024
          },
          fields: [
            {
              type: "enum",
              label: "Quality",
              key: "quality",
              required: true,
              default_value: "standard",
              options: ["standard", "premium"]
            },
            {
              type: "int",
              label: "Width",
              key: "width",
              required: true,
              default_value: 1024,
              min_value: 512,
              max_value: 2048
            },
            {
              type: "int",
              label: "Height",
              key: "height",
              required: true,
              default_value: 1024,
              min_value: 512,
              max_value: 2048
            }
          ]
        }
      ]
    },
    {
      name: "Stable Diffusion",
      class_path: "piframe.models.StableDiffusion3x",
      schema: [
        {
          type: "enum",
          label: "Model ID",
          key: "model_id",
          required: true,
          default_value: "sd3-large",
          options: [
            "sd3-large",
            "sd3-large-turbo",
            "sd3-medium",
            "sd3.5-large",
            "sd3.5-large-turbo",
            "sd3.5-medium"
          ]
        },
        {
          type: "enum",
          label: "Aspect Ratio",
          key: "aspect_ratio",
          required: true,
          default_value: "16:9",
          options: ["16:9"]
        },
        {
          type: "int",
          label: "CFG Scale",
          key: "cfg_scale",
          required: true,
          default_value: 7,
          min_value: 1,
          max_value: 20
        }
      ]
    },
    {
      name: "Stable Image Ultra",
      class_path: "piframe.models.StableImageUltra",
      schema: [
        {
          type: "enum",
          label: "Model ID",
          key: "model_id",
          required: true,
          default_value: "stable-image-ultra-api",
          options: ["stable-image-ultra-api"]
        },
        {
          type: "enum",
          label: "Aspect Ratio",
          key: "aspect_ratio",
          required: true,
          default_value: "16:9",
          options: ["16:9"]
        },
        {
          type: "string",
          label: "Negative Prompt",
          key: "negative_prompt",
          required: true,
          default_value: "",
          min_length: 0,
          max_length: 1000
        }
      ]
    }
  ];

  const TOPIC_STRATEGY_SCHEMAS: ComponentConfig[] = [
    {
      name: "Random Ad Lib",
      class_path: "piframe.prompts.RandomAdlib",
      schema: [
        {
          type: "list",
          label: "Adjectives",
          key: "adjectives",
          required: true,
          default_value: [
            "Cozy",
            "Mischevious",
            "Space",
            "Office-worker",
            "Glamorous",
            "Deceptive",
            "Stylish",
            "Leisurely",
            "Lounging",
            "Smoking",
            "Binge-drinking",
            "Dancing",
            "Partying",
            "Cute",
            "Evil",
            "Psychedelic",
            "Gangster"
          ],
          min_length: 1,
          max_length: 20
        },
        {
          type: "list",
          label: "Nouns",
          key: "nouns",
          required: true,
          default_value: [
            "Animals",
            "Hot Dogs",
            "Robots",
            "Astronauts", 
            "Pickles",
            "Condiments",
            "Wizards",
            "Zombies",
            "Dogs",
            "Cats",
            "Garden Gnomes",
            "French Fries",
            "Musical Instruments",
            "Lobsters",
            "Monsteras",
            "House Plants",
            "Aliens",
            "Fruits"
          ],
          min_length: 1,
          max_length: 20
        }
      ]
    }
  ];

  // Load initial configuration
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch(`${API_URL}/api/config`)
        const data = await response.json()
        
        // Set initial model selections based on class_path
        const descModel = DESCRIPTION_MODEL_SCHEMAS.find(m => 
          m.class_path === data.description_model?.class_path
        )
        if (descModel) {
          setSelectedDescriptionModel(descModel.name)
        }
        
        const imgModel = IMAGE_MODEL_SCHEMAS.find(m => 
          m.class_path === data.image_model?.class_path
        )
        if (imgModel) {
          setSelectedImageModel(imgModel.name)
        }

        // Set all configs at once
        setConfigs({
          description_model: {
            args: data.description_model?.args || {}
          },
          image_model: {
            args: data.image_model?.args || {}
          },
          topic_strategy: {
            args: data.topic_strategy?.args || {
              adjectives: TOPIC_STRATEGY_SCHEMAS[0].schema[0].default_value,
              nouns: TOPIC_STRATEGY_SCHEMAS[0].schema[1].default_value
            }
          },
          artifact_directory: data.artifact_directory || "artifacts"
        })
        
        setLoading(false)
      } catch (error) {
        console.error('Failed to load config:', error)
        setLoading(false)
      }
    }
    fetchConfig()
  }, [])

  // Poll power status
  useEffect(() => {
    const pollPowerStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/api/power`)
        const data = await response.json()
        setBatteryLevel(data.battery_level)
        setIsPowered(!data.is_battery_powered)
      } catch (error) {
        console.error('Failed to fetch power status:', error)
      }
    }

    pollPowerStatus() // Initial fetch
    const interval = setInterval(pollPowerStatus, 30000) // Poll every 30 seconds
    return () => clearInterval(interval)
  }, [])

  // Get list of available models
  const descriptionModelNames = DESCRIPTION_MODEL_SCHEMAS.map(m => m.name)
  const imageModelNames = IMAGE_MODEL_SCHEMAS.map(m => m.name)

  // Get selected model schemas
  const selectedDescriptionSchema = DESCRIPTION_MODEL_SCHEMAS.find(m => m.name === selectedDescriptionModel)
  const selectedImageSchema = IMAGE_MODEL_SCHEMAS.find(m => m.name === selectedImageModel)

  const renderFormField = (props: ConfigSchema & { value: any, onChange: (value: any) => void }) => {
    switch(props.type) {
      case 'string':
        return (
          <input
            type="text"
            value={props.value ?? props.default_value}
            onChange={(e) => props.onChange(e.target.value)}
            required={props.required}
            minLength={props.min_length}
            maxLength={props.max_length}
          />
        )

      case 'int':
        return (
          <input
            type="number"
            value={props.value ?? props.default_value}
            onChange={(e) => props.onChange(parseInt(e.target.value))}
            required={props.required}
            min={props.min_value}
            max={props.max_value}
            step={1}
          />
        )

      case 'float':
        return (
          <input
            type="number"
            value={props.value ?? props.default_value}
            onChange={(e) => props.onChange(parseFloat(e.target.value))}
            required={props.required}
            min={props.min_value}
            max={props.max_value}
            step="any"
          />
        )

      case 'enum':
        return (
          <select 
            value={props.value ?? props.default_value}
            onChange={(e) => props.onChange(e.target.value)}
            required={props.required}
          >
            {props.options.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        )

      case 'list':
        const currentList = (props.value ?? props.default_value) || [];
        return (
          <div className="list-field">
            <div className="list-items-container">
              {currentList.map((item: string, index: number) => (
                <div key={index} className="list-item">
                  <input
                    type="text"
                    value={item}
                    onChange={(e) => {
                      const newList = [...currentList];
                      newList[index] = e.target.value;
                      props.onChange(newList);
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      const newList = currentList.filter((_: any, i: number) => i !== index);
                      props.onChange(newList);
                    }}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={() => {
                if (!props.max_length || currentList.length < props.max_length) {
                  props.onChange([...currentList, '']);
                }
              }}
              disabled={props.max_length ? currentList.length >= props.max_length : false}
            >
              Add Item
            </button>
          </div>
        )

      case 'dict':
        const currentDict = (props.value ?? props.default_value) || {};
        return (
          <div className="dict-field">
            {props.fields.map((field) => (
              <div key={field.key} className="form-field">
                <label>{field.label}</label>
                {renderFormField({
                  ...field,
                  key: `${props.key}.${field.key}`,
                  value: currentDict[field.key] || field.default_value,
                  onChange: (value) => props.onChange({
                    ...currentDict,
                    [field.key]: value
                  })
                })}
              </div>
            ))}
          </div>
        )

      default:
        return <div>Unsupported field type: {(props as any).type}</div>
    }
  }

  const showToast = (message: string) => {
    setToast({ message, visible: true });
    setTimeout(() => {
      setToast(prev => ({ ...prev, visible: false }));
    }, 3000); // Hide after 3 seconds
  };

  const handleSave = async () => {
    try {
      // Get the schema for the current models
      const descSchema = DESCRIPTION_MODEL_SCHEMAS.find(m => m.name === selectedDescriptionModel)
      const imgSchema = IMAGE_MODEL_SCHEMAS.find(m => m.name === selectedImageModel)
      const topicSchema = TOPIC_STRATEGY_SCHEMAS.find(m => m.name === selectedTopicStrategy)

      // Extract relevant configs for each model, including default values
      const descriptionConfigs = descSchema?.schema.reduce((acc, field) => {
        acc[field.key] = configs.description_model?.args?.[field.key] ?? field.default_value
        return acc
      }, {} as Record<string, any>)

      const imageConfigs = imgSchema?.schema.reduce((acc, field) => {
        acc[field.key] = configs.image_model?.args?.[field.key] ?? field.default_value
        return acc
      }, {} as Record<string, any>)

      const topicConfigs = topicSchema?.schema.reduce((acc, field) => {
        acc[field.key] = configs.topic_strategy?.args?.[field.key] ?? field.default_value
        return acc
      }, {} as Record<string, any>)

      const configData = {
        description_model: {
          class_path: descSchema?.class_path,
          args: descriptionConfigs
        },
        image_model: {
          class_path: imgSchema?.class_path,
          args: imageConfigs
        },
        topic_strategy: {
          class_path: topicSchema?.class_path,
          args: topicConfigs
        },
        artifact_directory: configs.artifact_directory || "artifacts"
      }

      const response = await fetch(`${API_URL}/api/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ config: configData })
      })
      
      if (!response.ok) throw new Error('Failed to save config')
      showToast('Configuration saved successfully! 🎉')
    } catch (error) {
      console.error('Failed to save config:', error)
      showToast('Failed to save configuration ❌')
    }
  }

  const handleRefresh = async () => {
    try {
      const response = await fetch(`${API_URL}/api/refresh`, { method: 'POST' })
      if (!response.ok) throw new Error('Failed to refresh image')
      showToast('Screen will refresh soon! 🖼️')
    } catch (error) {
      console.error('Failed to refresh image:', error)
      showToast('Failed to refresh image ❌')
    }
  }

  if (loading) {
    return <div className="loading">Loading configuration...</div>
  }

  return (
    <div className="config-app">
      {toast.visible && (
        <div className="toast">
          {toast.message}
        </div>
      )}
      <div className="sidebar">
        <h2>🖼️ Piframe</h2>
        <div className="action-buttons">
          <button onClick={handleSave}>
            <span className="material-symbols-rounded">save</span>
            Save
          </button>
          <button onClick={handleRefresh}>
            <span className="material-symbols-rounded">autorenew</span>
            New Image
          </button>
        </div>

        <div className="power-status">
          <h3>⚡ Power Status</h3>
          <div className="status-text">
            {isPowered ? "Plugged in" : "Battery"}
          </div>
          {batteryLevel !== null && (
            <div>
              <div className="progress-container">
                <progress 
                  value={batteryLevel} 
                  max={1}
                  className={batteryLevel < 0.2 ? 'low-battery' : 'normal-battery'} 
                />
                <span className="progress-text">
                  {batteryLevel > 0.1 ? "🔋" : "🪫"} {Math.round(batteryLevel * 100)}%
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="main-content">
        {/* Topic Strategy Section */}
        <div className="config-section">
          <div className="config-row">
            <div className="selector-column">
              <h2>Topic Strategy</h2>
              <select 
                value={selectedTopicStrategy}
                onChange={(e) => setSelectedTopicStrategy(e.target.value)}
              >
                {TOPIC_STRATEGY_SCHEMAS.map(schema => (
                  <option key={schema.name} value={schema.name}>{schema.name}</option>
                ))}
              </select>
            </div>
            <div className="params-column">
              {TOPIC_STRATEGY_SCHEMAS.map(component => (
                <div key={component.name}>
                  <h2>{component.name} Parameters</h2>
                  {component.schema.map(field => (
                    <div key={field.key} className="form-field">
                      <label>{field.label}</label>
                      {renderFormField({
                        ...field,
                        value: configs.topic_strategy?.args?.[field.key],
                        onChange: (value) => setConfigs(prev => ({
                          ...prev,
                          topic_strategy: {
                            ...prev.topic_strategy,
                            args: {
                              ...prev.topic_strategy?.args,
                              [field.key]: value
                            }
                          }
                        }))
                      })}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Description Model Section */}
        <div className="config-section">
          <div className="config-row">
            <div className="selector-column">
              <h2>Description Model</h2>
              <select 
                value={selectedDescriptionModel}
                onChange={(e) => {
                  const newModel = e.target.value;
                  setSelectedDescriptionModel(newModel);
                  // Find the schema for the new model
                  const newSchema = DESCRIPTION_MODEL_SCHEMAS.find(m => m.name === newModel);
                  // Update configs with the new model's default model_id
                  if (newSchema) {
                    const modelIdField = newSchema.schema.find(f => f.key === 'model_id');
                    setConfigs(prev => ({
                      ...prev,
                      description_model: {
                        ...prev.description_model,
                        args: {
                          ...prev.description_model?.args,
                          model_id: modelIdField?.default_value
                        }
                      }
                    }));
                  }
                }}
              >
                {descriptionModelNames.map(name => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
            </div>
            <div className="params-column">
              {selectedDescriptionSchema && (
                <>
                  <h2>{selectedDescriptionSchema.name} Parameters</h2>
                  {selectedDescriptionSchema.schema.map(field => (
                    <div key={field.key} className="form-field">
                      <label>{field.label}</label>
                      {renderFormField({
                        ...field,
                        value: configs.description_model?.args?.[field.key],
                        onChange: (value) => setConfigs(prev => ({
                          ...prev,
                          description_model: {
                            ...prev.description_model,
                            args: {
                              ...prev.description_model?.args,
                              [field.key]: value
                            }
                          }
                        }))
                      })}
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>
        </div>

        {/* Image Model Section */}
        <div className="config-section">
          <div className="config-row">
            <div className="selector-column">
              <h2>Image Model</h2>
              <select 
                value={selectedImageModel}
                onChange={(e) => {
                  const newModel = e.target.value;
                  setSelectedImageModel(newModel);
                  // Find the schema for the new model
                  const newSchema = IMAGE_MODEL_SCHEMAS.find(m => m.name === newModel);
                  // Update configs with the new model's default model_id
                  if (newSchema) {
                    const modelIdField = newSchema.schema.find(f => f.key === 'model_id');
                    setConfigs(prev => ({
                      ...prev,
                      image_model: {
                        ...prev.image_model,
                        args: {
                          ...prev.image_model?.args,
                          model_id: modelIdField?.default_value
                        }
                      }
                    }));
                  }
                }}
              >
                {imageModelNames.map(name => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
            </div>
            <div className="params-column">
              {selectedImageSchema && (
                <>
                  <h2>{selectedImageSchema.name} Parameters</h2>
                  {selectedImageSchema.schema.map(field => (
                    <div key={field.key} className="form-field">
                      <label>{field.label}</label>
                      {renderFormField({
                        ...field,
                        value: configs.image_model?.args?.[field.key],
                        onChange: (value) => setConfigs(prev => ({
                          ...prev,
                          image_model: {
                            ...prev.image_model,
                            args: {
                              ...prev.image_model?.args,
                              [field.key]: value
                            }
                          }
                        }))
                      })}
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App

