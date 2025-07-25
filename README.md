# Smart Shopping Assistant

A Python-based shopping assistant that uses Google's Gemini AI to ask intelligent follow-up questions and generate shopping summaries.

## Features

- 🤖 AI-powered follow-up questions using Gemini API
- 🛍️ Product-specific question generation (especially for shoes)
- 📋 Comprehensive shopping summaries
- 💬 Interactive terminal interface
- 🔄 Multiple search sessions

## Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the shopping assistant:**
   ```bash
   python shopping_assistant.py
   ```

## How to Use

1. **Start the assistant** - Run the Python script
2. **Enter your search query** - e.g., "I want shoes", "I need a laptop"
3. **Answer follow-up questions** - The AI will ask relevant questions like:
   - Price range
   - Color preferences
   - Gender (male/female/unisex)
   - Size requirements
   - Brand preferences
   - And more...
4. **Get your summary** - Receive a comprehensive shopping summary
5. **Search again** - Option to start a new search

## Example Usage

```
🛍️  Welcome to the Smart Shopping Assistant!
==================================================
What are you looking for today? (e.g., 'I want shoes', 'I need a laptop'): I want shoes

🔍 Analyzing your search for: I want shoes
Generating personalized follow-up questions...

📝 Please answer the following questions (press Enter to skip any question):

1. What's your budget range?
   Your answer: $50-100

2. What type of shoes are you looking for?
   Your answer: Sneakers

3. What color do you prefer?
   Your answer: Black

4. Are you looking for male, female, or unisex items?
   Your answer: Male

5. What size do you need?
   Your answer: 10

📋 Generating your shopping summary...

==================================================
SHOPPING SUMMARY
==================================================
[AI-generated summary will appear here]
==================================================
```

## Supported Product Types

The assistant is optimized for various product categories, with special focus on:
- 👟 Shoes (sneakers, formal, casual, sports)
- 👕 Clothing
- 💻 Electronics
- 🏠 Home & Garden
- 🎮 Gaming
- And more!

## Requirements

- Python 3.7+
- Internet connection (for Gemini API)
- Google Generative AI package

## API Key

The script includes a pre-configured Gemini API key. For production use, consider using environment variables for security.

## Error Handling

The assistant includes robust error handling for:
- Network connectivity issues
- API rate limits
- Invalid user inputs
- Graceful exit with Ctrl+C 