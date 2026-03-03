FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY chatbot/ ./chatbot/

# Install dependencies using uv
RUN uv sync --frozen

# Expose port
EXPOSE 8080

# Run the FastAPI app
CMD ["uv", "run", "uvicorn", "chatbot.chatbot:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
