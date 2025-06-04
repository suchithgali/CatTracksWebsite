from google import genai
from google.genai import types

model_config = types.GenerateContentConfig(temperature=0.5, top_p=1.0)

client = genai.Client(api_key="AIzaSyCu6vMDNjRmWD37QkLxFUJyqe7Fu31ciMw")
#chat = client.chats.create(model='gemini-2.0-flash', history=[])
response = client.models.generate_content(model="gemini-2.0-flash", config = model_config, contents="Say not nice things about my not real chinese friend Jacori, in teen slang english in second person perspective, mix in unique roasts about how he never showers, always blows his nose super loud, doesn't clean up his trash")
print(response.text)