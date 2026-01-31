
import requests, base64


invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"

def call_llm(query, stream=False):
    headers = {
        "Authorization": "Bearer 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",
        "Accept": "text/event-stream" if stream else "application/json"
    }

    payload = {
        "model": "meta/llama-4-maverick-17b-128e-instruct",
        "messages": [{"role": "user", "content": query}],
        "max_tokens": 10512,
        "temperature": 1.00,
        "top_p": 1.00,
        "frequency_penalty": 0.00,
        "presence_penalty": 0.00,
        "stream": stream
    }

    response = requests.post(invoke_url, headers=headers, json=payload)

    if stream:
        for line in response.iter_lines():
            if line:
                print(line.decode("utf-8"))
    else:
        response_json = response.json()
        try:
            return response_json['choices'][0]['message']['content']
        except (KeyError, IndexError):
            return "Error: Unexpected response format: " + str(response_json)

if __name__ == "__main__":
    # Test execution when run directly
    result = call_llm("Hello, who are you? explane me what is this? a string theory with formular way to explain it")
    print(result)
