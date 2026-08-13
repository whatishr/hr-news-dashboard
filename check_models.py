from google import genai

client = genai.Client(api_key="AQ.Ab8RN6IXF5juNPJBdjnOde3GRu_jkyEgv43_PZjZs29WoBpHdQ")

for m in client.models.list():
    print(m.name)