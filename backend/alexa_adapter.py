from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.bedrock_agent import run_reasoning_agent
from backend.event_log import add_event

logger = logging.getLogger(__name__)

router = APIRouter()


class AlexaRequestEnvelope(BaseModel):
    version: str = "1.0"
    session: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    request: Dict[str, Any]


class AlexaSpeechOutput(BaseModel):
    type: str = Field("PlainText", const=True)
    text: str


class AlexaCard(BaseModel):
    type: str = Field("Simple", const=True)
    title: str
    content: str


class AlexaResponseBody(BaseModel):
    output_speech: AlexaSpeechOutput = Field(..., alias="outputSpeech")
    card: Optional[AlexaCard] = None
    should_end_session: bool = Field(False, alias="shouldEndSession")

    class Config:
        allow_population_by_field_name = True


class AlexaResponseEnvelope(BaseModel):
    version: str = "1.0"
    session_attributes: Dict[str, Any] = Field(default_factory=dict, alias="sessionAttributes")
    response: AlexaResponseBody

    class Config:
        allow_population_by_field_name = True


class DeviceCommand(BaseModel):
    device: str = Field(..., min_length=1, description="Logical device name, e.g. light or firetv.")
    action: str = Field(..., min_length=1, description="Action to perform on the device.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Optional action parameters.")
    utterance: Optional[str] = Field(
        default=None,
        description="User utterance that triggered the command. Used to enrich Bedrock reasoning context.",
    )


try:  # Optional import: prefer Philips Hue via phue.
    from phue import Bridge as _HueBridge  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    _HueBridge = None  # type: ignore

try:  # Optional import: python-lifx api for LIFX bulbs.
    import lifxlan  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    lifxlan = None  # type: ignore

try:  # Optional import: Fire TV controller.
    from firetv import FireTV  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    FireTV = None  # type: ignore


class LightController:
    """Attempt to control smart lights via Hue or LIFX APIs."""

    def __init__(self) -> None:
        self._mode: Optional[str] = None
        self._bridge = None
        self._lifx: Optional["lifxlan.LifxLAN"] = None  # type: ignore

        if _HueBridge is not None:
            bridge_ip = os.getenv("HUE_BRIDGE_IP")
            if bridge_ip:
                try:
                    self._bridge = _HueBridge(bridge_ip)
                    self._mode = "hue"
                    logger.info("Configured Philips Hue bridge at %s", bridge_ip)
                except Exception as exc:  # pragma: no cover - hardware specific
                    logger.warning("Failed to connect to Hue bridge at %s: %s", bridge_ip, exc)
        if self._mode is None and lifxlan is not None:
            try:
                self._lifx = lifxlan.LifxLAN()  # type: ignore
                self._mode = "lifx"
                logger.info("Configured LIFX LAN controller for smart lights.")
            except Exception as exc:  # pragma: no cover - hardware specific
                logger.warning("Failed to initialize LIFX LAN controller: %s", exc)

    @property
    def available(self) -> bool:
        return self._mode is not None

    def execute(self, action: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError(
                "No smart light controller is available. Configure HUE_BRIDGE_IP "
                "or install/configure python-lifx."
            )

        action_lower = action.lower()
        params = parameters or {}
        brightness = int(params.get("brightness", 150))
        brightness = max(1, min(brightness, 254))

        if self._mode == "hue":  # pragma: no cover - requires hardware
            if action_lower in {"on", "turn_on"}:
                self._bridge.set_group(0, "on", True)
            elif action_lower in {"off", "turn_off"}:
                self._bridge.set_group(0, "on", False)
            elif action_lower in {"dim", "brightness_down"}:
                self._bridge.set_group(0, "bri", max(1, brightness // 2))
            elif action_lower in {"brighten", "brightness_up"}:
                self._bridge.set_group(0, "bri", min(254, brightness))
            else:
                raise ValueError(f"Unsupported light action '{action}'.")
        elif self._mode == "lifx":  # pragma: no cover - requires hardware
            lights = self._lifx.get_lights() if self._lifx else []
            for light in lights:
                if action_lower in {"on", "turn_on"}:
                    light.set_power("on")
                elif action_lower in {"off", "turn_off"}:
                    light.set_power("off")
                elif action_lower in {"dim", "brightness_down"}:
                    light.set_brightness(max(0.1, brightness / 254.0))
                elif action_lower in {"brighten", "brightness_up"}:
                    light.set_brightness(min(1.0, brightness / 254.0))
                else:
                    raise ValueError(f"Unsupported light action '{action}'.")
        else:  # pragma: no cover - defensive
            raise RuntimeError("Light controller configured without a valid mode.")

        return {"device": "light", "action": action_lower, "parameters": params, "mode": self._mode}


class FireTVController:
    """Control Amazon Fire TV devices via the firetv library."""

    def __init__(self) -> None:
        self._firetv = None
        if FireTV is None:
            return

        host = os.getenv("FIRETV_HOST")
        adb_port = int(os.getenv("FIRETV_ADB_PORT", "5555"))
        adb_key = os.getenv("FIRETV_ADB_KEY")
        if not host:
            logger.info("FIRETV_HOST not configured; Fire TV control disabled.")
            return
        try:  # pragma: no cover - requires hardware
            self._firetv = FireTV(host, adb_port=adb_port, adbkey=adb_key)
            logger.info("Connected to Fire TV at %s:%s", host, adb_port)
        except Exception as exc:
            logger.warning("Failed to connect to Fire TV at %s:%s - %s", host, adb_port, exc)

    @property
    def available(self) -> bool:
        return self._firetv is not None

    def execute(self, action: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError(
                "Fire TV controller is not available. Ensure firetv is installed and FIRETV_HOST is set."
            )

        params = parameters or {}
        action_lower = action.lower()
        device = self._firetv  # type: ignore

        if action_lower in {"play", "resume"}:
            device.media_play()
        elif action_lower in {"pause", "stop"}:
            device.media_pause()
        elif action_lower in {"home"}:
            device.home()
        elif action_lower in {"launch"}:
            package = params.get("package")
            if not package:
                raise ValueError("Missing package name for Fire TV launch action.")
            device.launch_app(package)
        else:
            raise ValueError(f"Unsupported Fire TV action '{action}'.")

        return {"device": "firetv", "action": action_lower, "parameters": params}


_light_controller: Optional[LightController] = None
_firetv_controller: Optional[FireTVController] = None


def _get_light_controller() -> LightController:
    global _light_controller
    if _light_controller is None:
        _light_controller = LightController()
    return _light_controller


def _get_firetv_controller() -> FireTVController:
    global _firetv_controller
    if _firetv_controller is None:
        _firetv_controller = FireTVController()
    return _firetv_controller


@router.post("/alexa")
def alexa_endpoint(envelope: AlexaRequestEnvelope) -> Dict[str, Any]:
    user_input = _extract_alexa_input(envelope.request)
    context = {
        "alexa": {
            "request": envelope.request,
            "session": envelope.session or {},
        }
    }

    try:
        plan = run_reasoning_agent(user_input, context)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected failure handling Alexa request.")
        raise HTTPException(status_code=500, detail="Unexpected Bedrock reasoning failure.") from exc

    response_body = AlexaResponseBody(
        output_speech=AlexaSpeechOutput(text=plan),
        card=AlexaCard(title="Care Plan", content=plan),
        should_end_session=_should_end_session(envelope.request),
    )
    response_envelope = AlexaResponseEnvelope(response=response_body)
    return response_envelope.model_dump(by_alias=True)


@router.post("/smart_home")
def smart_home_endpoint(command: DeviceCommand) -> Dict[str, Any]:
    context = {
        "device": command.device,
        "action": command.action,
        "parameters": command.parameters or {},
    }
    user_input = command.utterance or f"Perform {command.action} on {command.device}"

    try:
        plan = run_reasoning_agent(user_input, context)
    except ValueError as exc:
        add_event(
            "smart_home.error",
            {"device": command.device, "action": command.action, "error": str(exc)},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        add_event(
            "smart_home.error",
            {"device": command.device, "action": command.action, "error": str(exc)},
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    execution_result: Dict[str, Any]
    try:
        if command.device.lower() in {"light", "lights"}:
            execution_result = _get_light_controller().execute(command.action, command.parameters)
        elif command.device.lower() in {"firetv", "tv", "aftv"}:
            execution_result = _get_firetv_controller().execute(command.action, command.parameters)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported device '{command.device}'.")
    except ValueError as exc:
        add_event(
            "smart_home.error",
            {"device": command.device, "action": command.action, "error": str(exc)},
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        add_event(
            "smart_home.error",
            {"device": command.device, "action": command.action, "error": str(exc)},
        )
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    add_event(
        "smart_home.success",
        {
            "device": command.device,
            "action": command.action,
            "plan_preview": plan[:200],
            "execution": execution_result,
        },
    )

    return {"status": "ok", "plan": plan, "execution": execution_result}


def _extract_alexa_input(request: Dict[str, Any]) -> str:
    request_type = (request.get("type") or "").lower()
    if request_type == "intentrequest":
        intent = request.get("intent") or {}
        name = intent.get("name", "GeneralIntent")
        slots = intent.get("slots") or {}
        slot_values = []
        for slot in slots.values():
            if isinstance(slot, dict) and slot.get("value"):
                slot_values.append(str(slot["value"]))
        if slot_values:
            return " ".join(slot_values)
        return name.replace("_", " ")
    if request_type == "launchrequest":
        return "Provide a welcoming caregiving response for the Alexa LaunchRequest."
    if request_type == "sessionendedrequest":
        return "Provide a graceful session end acknowledgment for Alexa."
    text = request.get("spokenText") or request.get("text") or request.get("payload")
    if isinstance(text, str) and text.strip():
        return text.strip()
    return "Provide supportive caregiving guidance for the user."


def _should_end_session(request: Dict[str, Any]) -> bool:
    request_type = (request.get("type") or "").lower()
    return request_type == "sessionendedrequest"


__all__ = ["router"]
