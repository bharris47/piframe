import json
import os
from dataclasses import dataclass
from typing import Type

import boto3
import streamlit as st

from piframe import prompts
from piframe.config import Config
from piframe.hardware import power
from piframe.reflection import ModuleDefinition

CONFIG_PATH = "config.json"


if "models" not in st.session_state:
    bedrock = boto3.client("bedrock")
    st.session_state["models"] = bedrock.list_foundation_models()["modelSummaries"]

models = st.session_state["models"]

@dataclass
class Component:
    class_path: str
    schema: dict[str, Type | list]

def get_model_id(model_summary: dict):
    if "ON_DEMAND" in model_summary["inferenceTypesSupported"]:
        return model_summary["modelId"]
    else:
        return f"us.{model_summary['modelId']}"


DESCRIPTION_MODEL_SCHEMAS = {
    "Meta": Component(
        class_path="piframe.models.Meta",
        schema={
            "model_id": [get_model_id(model) for model in models if model["providerName"] == "Meta"],
            "max_gen_len": int,
            "temperature": float,
        },
    ),
    "Anthropic": Component(
        class_path="piframe.models.Anthropic",
        schema={
            "model_id": [get_model_id(model) for model in models if model["providerName"] == "Anthropic"],
            "anthropic_version": ["bedrock-2023-05-31"],
            "max_tokens": int,
            "temperature": float,
        },
    ),
}

IMAGE_MODEL_SCHEMAS = {
    "Amazon Titan": Component(
        class_path="piframe.models.TitanImage",
        schema={
            "model_id": [
                get_model_id(model) for model in models
                if model["providerName"] == "Amazon"
                and "IMAGE" in model["outputModalities"]
            ],
            "imageGenerationConfig": {
                "quality": ["standard", "premium"],
                "width": int,
                "height": int,
            },
        },
    ),
    "Stable Diffusion": Component(
        class_path="piframe.models.StableDiffusion3x",
        schema={
            "model_id": [
                "sd3-large",
                "sd3-large-turbo",
                "sd3-medium",
                "sd3.5-large",
                "sd3.5-large-turbo",
                "sd3.5-medium",
            ],
            "aspect_ratio": ["16:9"],
            "cfg_scale": int,
        },
    ),
    "Stable Image Ultra": Component(
        class_path="piframe.models.StableDiffusion3x",
        schema={
            "model_id": [
                "stable-image-ultra-api",
            ],
            "aspect_ratio": ["16:9"],
            "negative_prompt": str,
        },
    ),
}

TOPIC_STRATEGY_SCHEMAS = {
    "Random Ad Lib": Component(
        class_path="piframe.prompts.RandomAdlib",
        schema={
            "adjectives": list,
            "nouns": list,
        },
    ),
}

DEFAULTS = {
    "max_tokens": 100,
    "adjectives": prompts.ADJECTIVES,
    "nouns": prompts.NOUNS,
}

def get_component_config(
        section_name: str,
        label: str,
        current_component_config: ModuleDefinition,
        component_schemas: dict[str, Component]
):
    st.markdown(f"#### {section_name}")
    current_description_model_type = [
        name for name, component in component_schemas.items()
        if component.class_path == current_component_config.class_path
    ][0]
    model_names = list(component_schemas)

    col1, col2 = st.columns([1, 2])
    with col1:
        selected_model_type = st.selectbox(
            label=label,
            options=model_names,
            index=model_names.index(current_description_model_type)
        )

    model_schema = component_schemas[selected_model_type].schema
    with col2:
        selected_options = get_selected_options(current_component_config.args, model_schema)

    return ModuleDefinition(
        class_path=component_schemas[selected_model_type].class_path,
        args=selected_options,
    )


def get_selected_options(current_args: dict, model_schema):
    selected_options = {}
    for field, field_type in model_schema.items():
        current_config_value = current_args.get(field)
        if current_config_value is None:
            current_config_value = DEFAULTS.get(field)
        choice = None
        if isinstance(field_type, list):
            idx = 0
            if current_config_value:
                try:
                    idx = field_type.index(current_config_value)
                except ValueError:
                    idx = None
            choice = st.selectbox(field, field_type, index=idx)
        elif isinstance(field_type, dict):
            st.text(field)
            choice = get_selected_options(current_args[field], field_type)
        elif field_type == str:
            choice = st.text_input(
                label=field,
                value=current_config_value,
            )
        elif field_type == int or field_type == float:
            choice = st.number_input(
                label=field,
                value=current_config_value,
            )
        elif field_type == list:
            values = st.text_area(
                label=field,
                value="\n".join(current_config_value),
            )
            choice = [line.strip() for line in values.splitlines()]
        if choice is not None:
            selected_options[field] = choice
    return selected_options

if "current_config" not in st.session_state:
    with open(CONFIG_PATH) as f:
        st.session_state["current_config"] = Config(**json.load(f))
current_config: Config = st.session_state["current_config"]
pending_config = {}

st.markdown(f"### Configuration")

pending_config["topic_strategy"] = get_component_config(
    section_name="Topic Strategy",
    label="Strategy",
    current_component_config=current_config.topic_strategy,
    component_schemas=TOPIC_STRATEGY_SCHEMAS,
)
st.divider()

pending_config["description_model"] = get_component_config(
    section_name="Description Model",
    label="Model",
    current_component_config=current_config.description_model,
    component_schemas=DESCRIPTION_MODEL_SCHEMAS,
)
st.divider()

pending_config["image_model"] = get_component_config(
    section_name="Image Model",
    label="Model",
    current_component_config=current_config.image_model,
    component_schemas=IMAGE_MODEL_SCHEMAS,
)
st.divider()

pending_config["artifact_directory"] = st.text_input(
    label="Artifacts Directory",
    value=current_config.artifact_directory,
)

with st.sidebar:
    st.markdown("# 🖼️ ️Piframe")
    col1, col2 = st.columns([1, 1])
    with col1:
        save = st.button(label="Save", icon=":material/save:", use_container_width=True)

    with col2:
        refresh_image = st.button(label="New Image", icon=":material/rotate_right:", use_container_width=True)

    if save:
        with open(CONFIG_PATH, "w") as f:
            save_config = Config(**pending_config)
            json.dump(save_config.model_dump(), f, indent=2)
            del st.session_state["current_config"]
            st.toast("Configuration saved!", icon="🎉")
            st.balloons()
    if refresh_image:
        # os.system("sudo systemctl start update-frame")
        st.toast("Screen will refresh soon!", icon="🖼️")

    st.subheader("⚡ Power Status")
    status = power.get_power_status()
    battery_level = power.get_battery_level()
    if power.is_battery_powered():
        power_status_string = f"Battery"
    else:
        power_status_string = f"Plugged in"
    st.write(power_status_string)
    if battery_level is not None:
        battery_icon = "🔋" if battery_level > 0.1 else "🪫"
        st.progress(value=battery_level, text=f"{battery_icon} {battery_level:.0%}")
