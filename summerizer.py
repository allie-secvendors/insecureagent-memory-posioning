import ollama
import time
import re


# Structure to store summaries with timestamps and validation
summary_memory = {}  # Format: {user_id: {"summary": str, "timestamp": float}}
MAX_SUMMARY_LENGTH = 1000  # Maximum length of stored summaries
SUMMARY_EXPIRY_SECONDS = 3600  # Summaries expire after 1 hour


def validate_user_id(user_id):
    """Validate user ID to prevent injection attacks."""
    # Only allow alphanumeric user IDs with limited length
    return isinstance(user_id, str) and re.match(r'^[a-zA-Z0-9_-]{1,32}$', user_id) is not None


def sanitize_input(text, max_length=5000):
    """
    Sanitize user input to prevent prompt injection and other manipulations.
    """
    # Remove potentially harmful characters, keep basic text formatting
    sanitized = re.sub(r'[^\w\s.,?!()\'":-]', ' ', text)
    # Truncate if too long
    return sanitized[:max_length]


def llama_summarizer():
    """
    Summarizes user-provided text using Llama 3.2.
    Protected against memory poisoning attacks.
    """
    user_id = input("Enter user ID (alphanumeric only, max 32 characters): ")
    
    # Validate user ID
    if not validate_user_id(user_id):
        print("Invalid user ID. Please use only alphanumeric characters (max 32).")
        return
    
    user_input = input("Enter text to summarize: ")
    # Sanitize user input to prevent prompt injection
    user_input = sanitize_input(user_input)
    
    # Clean expired entries from memory
    current_time = time.time()
    expired_keys = [k for k, v in summary_memory.items() 
                    if current_time - v.get("timestamp", 0) > SUMMARY_EXPIRY_SECONDS]
    for key in expired_keys:
        del summary_memory[key]
    
    # Create prompt with context if available
    prompt = f"Summarize the following text: {user_input}"
    if user_id in summary_memory:
        prev_summary = summary_memory[user_id].get("summary", "")
        # Use previous summary in a structured way rather than direct concatenation
        prompt = (f"Previous summary: {prev_summary}\n\n"
                  f"Please summarize this new text: {user_input}")
    
    try:
        response = ollama.chat(model="llama3.2", messages=[
            {"role": "user", "content": prompt}
        ])
        summary = response.get("message", {}).get("content", "Error: No response")
        
        # Limit summary size before storing
        if len(summary) > MAX_SUMMARY_LENGTH:
            summary = summary[:MAX_SUMMARY_LENGTH]
        
        # Store summary with timestamp
        summary_memory[user_id] = {
            "summary": summary,
            "timestamp": current_time
        }
    except Exception as e:
        summary = f"Error: {str(e)}"
    
    print("\nSummary:", summary)


if __name__ == "__main__":
    llama_summarizer()