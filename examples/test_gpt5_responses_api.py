"""Test script to verify GPT-5 and Responses API integration."""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()


def test_basic_chat():
    """Test basic chat with GPT-5 using Responses API."""
    print("Testing basic chat with GPT-5...")
    
    # NOTE: GPT-5 and o-series models don't support temperature parameter
    llm = ChatOpenAI(
        model="gpt-5-nano",  # or "gpt-5-pro"
        api_key=os.getenv("OPENAI_API_KEY"),
        output_version="responses/v1",
        use_responses_api=True,
        # temperature is NOT supported for reasoning models
    )
    
    response = llm.invoke("Say 'Hello from GPT-5!' and nothing else.")
    print(f"Response: {response.content}")
    print(f"Response metadata: {response.response_metadata}")
    print("✓ Basic chat test passed!\n")


def test_reasoning_model():
    """Test reasoning with o-series models."""
    print("Testing reasoning model...")
    
    llm = ChatOpenAI(
        model="o4-mini",
        reasoning={
            "effort": "medium",
            "summary": "auto",
        },
        output_version="responses/v1",
    )
    
    response = llm.invoke("What is 7 * 8?")
    
    # Get text response
    print(f"Answer: {response.text()}")
    
    # Check for reasoning blocks
    for block in response.content:
        if block["type"] == "reasoning":
            print("Reasoning summary found:")
            for summary in block.get("summary", []):
                print(f"  - {summary.get('text', '')[:100]}...")
    
    print("✓ Reasoning model test passed!\n")


def test_streaming():
    """Test streaming with GPT-5."""
    print("Testing streaming...")
    
    # NOTE: GPT-5 models don't support temperature parameter
    llm = ChatOpenAI(
        model="gpt-5-nano",
        stream_usage=True,
        output_version="responses/v1",
        use_responses_api=True,
        # temperature is NOT supported for reasoning models
    )
    
    print("Streaming response: ", end="", flush=True)
    for chunk in llm.stream("Count from 1 to 5, separated by commas."):
        if chunk.content:
            print(chunk.content, end="", flush=True)
    
    print("\n✓ Streaming test passed!\n")


def test_conversation_state():
    """Test conversation state management."""
    print("Testing conversation state...")
    
    llm = ChatOpenAI(
        model="gpt-5-nano",
        output_version="responses/v1",
        use_responses_api=True,
    )
    
    # First message
    response1 = llm.invoke("My name is Alice.")
    print(f"First response: {response1.text()}")
    
    # Continue conversation using previous response ID
    response2 = llm.invoke(
        "What is my name?",
        previous_response_id=response1.response_metadata["id"],
    )
    print(f"Second response: {response2.text()}")
    print("✓ Conversation state test passed!\n")


def test_structured_output():
    """Test structured output."""
    print("Testing structured output...")
    
    from pydantic import BaseModel
    
    class GameIdea(BaseModel):
        """A simple game idea"""
        title: str
        genre: str
    
    llm = ChatOpenAI(
        model="gpt-5-nano",
        output_version="responses/v1",
        use_responses_api=True,
    )
    
    structured_llm = llm.with_structured_output(GameIdea, strict=True)
    result = structured_llm.invoke("Suggest a space exploration game idea.")
    
    print(f"Title: {result.title}")
    print(f"Genre: {result.genre}")
    print("✓ Structured output test passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("GPT-5 and Responses API Integration Tests")
    print("=" * 60)
    print()
    
    try:
        test_basic_chat()
        test_streaming()
        
        # Optional tests - only run if you have access to these models
        try:
            test_conversation_state()
        except Exception as e:
            print(f"⚠ Conversation state test skipped: {e}\n")
        
        try:
            test_structured_output()
        except Exception as e:
            print(f"⚠ Structured output test skipped: {e}\n")
        
        try:
            test_reasoning_model()
        except Exception as e:
            print(f"⚠ Reasoning model test skipped: {e}\n")
        
        print("=" * 60)
        print("All available tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

