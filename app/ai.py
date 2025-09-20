from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from dotenv import load_dotenv
from os import getenv
from app.models import AiResponse, LightActionArgs, Perc, TrackingModeArgs
from openwakeword.model import Model as WakeModel

load_dotenv()

class Ai():
    def __init__(self, bus=None):
        self.bus = bus
        self.model = OpenAIChatModel(
            "@preset/the-lamp-ai",
            provider=OpenRouterProvider(api_key=getenv('OPENROUTER_API_KEY')),
        )
        self.agent = Agent(self.model, output_type=AiResponse)
        self.wake_model = WakeModel(wakeword_models=["hey_jarvis"])

        if self.bus:
            self.bus.subscribe("ai_request")(self.on_request)
            self.bus.subscribe("audio_input")(self.wake_predict)

    async def on_request(self, request: str) -> str:
        ''' Execute any request to AI '''
        print(f"Requested: {request}")
        request = await self.agent.run(request)
        response: AiResponse = request.output

        # Execute all actions
        if self.bus:
            if response.action:
                for _name, args in response.action.items():
                    if isinstance(args, LightActionArgs):
                        perc = Perc(val=args.perc)
                        self.bus.emit("light_action", perc)
                    elif isinstance(args, TrackingModeArgs):
                        self.bus.emit("tracking_mode", args.mode, args.subjects)
            
            self.bus.emit("talk", response.text)

        return response

    async def wake_predict(self, audio: bytes) -> bool:
        ''' Detect if wake word is spoken '''
        predictions = self.wake_model.predict(audio)
        for _, score in predictions.prediction_buffer.items():
            if score > 0.8:
                print("Wake word detected")
                self.bus.emit("ai_wakeup")
                return True

        return False
