"""
Gemini Service

Handles all interactions with Google Gemini LLM.
"""

import json
import logging
import tempfile
from typing import Any

import google.genai as genai
from google.genai import types
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_community.callbacks import get_openai_callback
from langchain.chat_models import init_chat_model, BaseChatModel

from src.config.settings import settings


class AIService:
    """Service for interacting with Langchain."""
    
    def __init__(self) -> None:
        # `genai.Client` is lightweight; initialize once per service instance.
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.logger = logging.getLogger(__name__)

    def call_llm(self, model_name: str | None = None) -> BaseChatModel:
        llm = ChatGoogleGenerativeAI(model = model_name or settings.BASE_MODEL, api_key=settings.GEMINI_API_KEY)
        return llm

    def generate(self, prompt: str, model_name: str | None = None) -> str:
        """Return a plain-text completion from the Gemini API.

        Parameters
        ----------
        prompt : str
            Text prompt to send to the model.
        model_name : Optional[str]
            If omitted or falsy, ``settings.BASE_MODEL`` is used.
        model_provider : Optional[str]
            If omitted or falsy, ``settings.BASE_MODEL`` is used.

        Returns
        -------
        str
            The raw text produced by the model.
        """

        llm = self.call_llm(model_name = model_name)
        output = llm.invoke(prompt)
        
        return output.content
    
    def generate_json(self, model_name: str,prompt: str, schema: Any, tools: Any | None = None):
        """Request a structured JSON completion from Gemini.

        Parameters
        ----------
        prompt : str
            The prompt text to send.
        schema : Any
            JSON schema (dict) or Pydantic model class guiding the model's output.
        model_name : Optional[str]
            Specific Gemini model to use; falls back to ``settings.BASE_MODEL``.
        tools : Any
            LangChain-compatible tools specification; if provided, the model can call these tools as part of its response generation.
        """

        llm = self.call_llm(model_name=model_name)
        if tools:
            llm = llm.bind_tools([schema], tools=tools,
                                        ls_structured_output_format={"kwargs": {"method": "function_calling"},
                                                                     "schema": schema,})
        else:
            llm = llm.bind_tools([schema], ls_structured_output_format={"kwargs": {"method": "function_calling"},
                                                                        "schema": schema,})
        output = llm.invoke(prompt)
        return output.model_dump() if hasattr(output, 'model_dump') else output
    
    def call_llm_with_tools(self, model_name: str, temperature: int,prompt: str, schema: Any, tools: Any | None = None):
        """Get a LangChain-wrapped LLM instance that can call tools and produce structured output.

        Parameters
        ----------
        prompt : str
            The prompt text to send.
        schema : Any
            JSON schema (dict) or Pydantic model class guiding the model's output.
        model_name : Optional[str]
            Specific Gemini model to use; falls back to ``settings.BASE_MODEL``.
        tools : Any
            LangChain-compatible tools specification; if provided, the model can call these tools as part of its response generation.
        """

        llm = self.call_llm(model_name=model_name, temperature= temperature)
        llm_with_tools = llm.bind_tools([schema], tools=tools,
                                        ls_structured_output_format={"kwargs": {"method": "function_calling"},
                                                                     "schema": schema,}) if tools else llm
        return llm_with_tools
    
    def generate_json_from_agent(
        self,
        prompt: str,
        input_data: dict,
        tools: Any,
        schema: dict,
        model_name: str | None = None,
    ) -> dict:
        """Use a LangChain agent backed by Gemini to produce structured output.

        Parameters
        ----------
        prompt : str
            System prompt for the agent.
        input_data : dict
            Data passed as the "user" message.
        tools : Any
            LangChain-compatible tools specification.
        schema : dict
            Expected response format for the agent.
        model_name : Optional[str]
            Gemini model override.

        Returns
        -------
        dict
            The parsed agent response.
        """
        agent = create_agent(
            model=model_name,
            tools=tools,
            system_prompt=prompt,
            response_format=schema,
        )

        formatted_input = {"messages": [{"role": "user", "content": json.dumps(input_data, indent=2)}]}

        try:
            with get_openai_callback() as cb:
                response = agent.invoke(formatted_input)

            # logging callbacks for insight; consumers can swap for real logger if needed
            print(f"Total Tokens: {cb.total_tokens}")
            print(f"Prompt Tokens: {cb.prompt_tokens}")
            print(f"Completion Tokens: {cb.completion_tokens}")
            print(f"Total Cost (USD): ${cb.total_cost}")

            return response["structured_response"].model_dump(exclude_none=True)
        except Exception as e:
            self.logger.error(f"Agent invocation failed: {e}", exc_info=True)
            return self._error_dict(str(e))
    
    import tempfile

    def generate_image(self, image_id ,prompt: str) -> str:
        response = self.client.models.generate_content(
            model=settings.IMAGE_GENERATION_MODEL,
            contents=[prompt],
        )

        temp_path = None

        for part in response.parts:
            if part.text:
                print(part.text)
            elif part.inline_data:
                image = part.as_image()

                with tempfile.NamedTemporaryFile(
                    suffix=".png",
                    delete=False,
                    dir=tempfile.gettempdir(),
                ) as tmp:
                    temp_path = tmp.name

                image.save(temp_path)

        return temp_path