from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from dotenv import load_dotenv
from os import getenv
from app.models import AiResponse, LightActionArgs, Perc, TrackingModeArgs
from openwakeword.model import Model as WakeModel
from app.eventbus import EventBus

load_dotenv()

class Ai():
    def __init__(self, bus=None):
        self.bus = bus
        self.model = OpenAIChatModel(
            "@preset/the-lamp-ai",
            provider=OpenRouterProvider(api_key=getenv('OPENROUTER_API_KEY', "DUMMYKEY")),
        )
        self.agent = Agent(self.model, output_type=AiResponse)
        self.wake_model = WakeModel(wakeword_models=["hey_jarvis"])

        if bus:
            bus.subscribe("ai_request")(self.on_request)
            bus.subscribe("audio_input")(self.wake_predict)

    async def on_request(self, request: str) -> AiResponse:
        ''' Execute any request to AI '''
        print(f"Requested: {request}")
        result = await self.agent.run(request)
        response = result.output

        # Execute all actions
        if self.bus:
            if response.action:
                for _name, args in response.action.items():
                    if isinstance(args, LightActionArgs):
                        perc = Perc(val=args.perc)
                        self.bus.emit("light_action", perc)
                    elif isinstance(args, TrackingModeArgs):
                        self.bus.emit("tracking_mode", args.type, args.subjects)
            
            self.bus.emit("talk", response.text)

        return response

    async def wake_predict(self, audio: bytes) -> bool:
        ''' Detect if wake word is spoken '''
        import numpy as np
        # Assuming audio is PCM 16-bit mono, convert bytes to numpy array
        audio_np = np.frombuffer(audio, dtype=np.int16)
        prediction_dict, _ = self.wake_model.predict(audio_np)
        for _, score in prediction_dict.items():
            if score > 0.8:
                print("Wake word detected")
                if self.bus:
                    self.bus.emit("ai_wakeup")
                return True

        return False
