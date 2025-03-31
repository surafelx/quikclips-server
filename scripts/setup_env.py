with open(".env", "w") as env_file:
    env_file.write("GOOGLE_CREDENTIALS_PATH=your-google-credentials.json\n")
    env_file.write("OPENAI_API_KEY=your-openai-api-key\n")

print("✅ .env file created successfully!")
