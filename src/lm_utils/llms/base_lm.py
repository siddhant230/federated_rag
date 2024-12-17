import json

from transformers import T5Tokenizer, T5ForConditionalGeneration
import google.generativeai as genai
from llama_index.llms.ollama import Ollama

from src.lm_utils.prompts import InfoRetriever


class BaseLLModel:
    """
    Base class for interfacing any large language model / answering mechanism
    To implement any new llm, follow the exmaple of any llm class below.
    You need to implement the generate and post-process method.
    """

    def __init__(self, model_name, tokenizer_name=None):
        self.model_name = model_name
        self.tokenizer_name = tokenizer_name
        if tokenizer_name is None:
            self.tokenizer_name = model_name

    def postprocess(self, *args):
        return args

    def generate_response(self, *args):
        return ""

    def make_prompt(self, context, query):
        return f"""
              Answer from given context, Be very specific and accurate.
              {context}
              Question: {query}
              Answer:
            """


class T5LLM(BaseLLModel):
    """
    Assuming flan-T5-small as base LLM and tokenizer.
    Overrinding BaseLLModel.
    """

    def __init__(self, model_name="google/flan-t5-small", tokenizer_name=None,
                 max_new_tokens=256):
        super().__init__(model_name, tokenizer_name)
        self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
        self.llm = T5ForConditionalGeneration.from_pretrained(self.model_name)
        self.max_new_tokens = max_new_tokens

    def postprocess(self, response, removable_content):
        out = self.tokenizer.decode(response[0])
        out = out.replace(removable_content, "")
        return out

    def make_prompt(self, context, query):
        return InfoRetriever.FLAN_T5_PROMPT.format(context, query)

    def generate_response(self, context, query):
        prompt = self.make_prompt(context, query)
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids

        outputs = self.llm.generate(
            input_ids, max_new_tokens=self.max_new_tokens)
        out = self.postprocess(outputs, prompt)
        return out


class GeminiLLM(BaseLLModel):
    def __init__(self, api_key_path="api_key.json",
                 model_name='gemini-1.5-flash'):
        super().__init__(model_name, None)
        if api_key_path.endswith(".json"):
            self.api_key = json.load(open(api_key_path))["gemini"]
        elif api_key_path.endswith(".txt"):
            self.api_key = open(api_key_path).read()
        else:
            self.api_key = api_key_path

        genai.configure(api_key=self.api_key)
        self.llm = genai.GenerativeModel(model_name)

    def make_prompt(self, context, query):
        return InfoRetriever.GEMINI_PROMPT.format(context, query)

    def generate_response(self, context, query):
        prompt = self.make_prompt(context, query)
        response = self.llm.generate_content(prompt)
        return response


class OllamaLLM(BaseLLModel):
    def __init__(self,
                 model_name='qwen2:1.5b', max_tokens=100):
        super().__init__(model_name, None)
        self.max_tokens = max_tokens
        self.llm = Ollama(model=model_name,
                          request_timeout=120.0,
                          additional_kwargs={"num_predict": max_tokens})

    def make_prompt(self, context, query):
        return InfoRetriever.OLLAMA_QWEN_PROMPT.format(context, query)

    def generate_response(self, context, query):
        prompt = self.make_prompt(context, query)
        response = self.llm.complete(prompt)
        return response.text
