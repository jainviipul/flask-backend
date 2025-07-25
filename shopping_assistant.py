import google.generativeai as genai
import json
import os
import requests
from typing import Dict, List, Any

# Configure Gemini API and YouTube Data API
API_KEY = "AIzaSyAQ-V9IvNDDegtQ2yhGUDQy7uF0zq1ajsM"
genai.configure(api_key=API_KEY)

class ShoppingAssistant:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.conversation_history = []
        self.youtube_api_key = API_KEY
        self.youtube_base_url = "https://www.googleapis.com/youtube/v3"
        
    def search_youtube_videos(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search YouTube videos using the YouTube Data API v3"""
        
        url = f"{self.youtube_base_url}/search"
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'key': self.youtube_api_key,
            'order': 'relevance'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = []
            
            if 'items' in data:
                for item in data['items']:
                    video_info = {
                        'video_id': item['id']['videoId'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'channel_title': item['snippet']['channelTitle'],
                        'published_at': item['snippet']['publishedAt'],
                        'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                        'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                    }
                    videos.append(video_info)
            
            return videos
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching YouTube: {e}")
            return []
    
    def get_video_captions(self, video_id: str) -> str:
        """Get captions for a specific video"""
        
        # First, list available caption tracks
        captions_url = f"{self.youtube_base_url}/captions"
        params = {
            'part': 'snippet',
            'videoId': video_id,
            'key': self.youtube_api_key
        }
        
        try:
            response = requests.get(captions_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            captions_text = ""
            
            if 'items' in data and data['items']:
                # Get the first available caption track (usually English)
                caption_id = data['items'][0]['id']
                
                # Download the caption content
                download_url = f"{self.youtube_base_url}/captions/{caption_id}"
                download_params = {
                    'key': self.youtube_api_key
                }
                
                download_response = requests.get(download_url, params=download_params)
                if download_response.status_code == 200:
                    captions_text = download_response.text
                else:
                    captions_text = "Captions available but could not be downloaded"
            else:
                captions_text = "No captions available for this video"
                
            return captions_text
            
        except requests.exceptions.RequestException as e:
            return f"Error retrieving captions: {e}"
    
    def search_product_recommendations(self, user_query: str, summary: str) -> str:
        """Search for product recommendations using YouTube Data API"""
        
        # Let Gemini create the search query based on the summary
        search_prompt = f"""
        Based on this shopping summary, create a natural YouTube search query that a human would type.
        
        Original Query: {user_query}
        Shopping Summary: {summary}
        
        Create a simple, natural search query like how people actually search on YouTube.
        Include the product and budget if mentioned, but keep it conversational and natural.
        
        Examples of good queries:
        - "laptop under 1 lakh"
        - "best gaming laptop"
        - "iPhone 15 review"
        - "shoes for running"
        
        Return ONLY the search query in one line, nothing else.
        """
        
        try:
            response = self.model.generate_content(search_prompt)
            search_query = response.text.strip()
            print(f"🔍 Searching YouTube for: {search_query}")
            print(f"📋 Based on summary: {summary[:100]}...")
        except Exception as e:
            print(f"Error generating search query: {e}")
            search_query = f"{user_query} review unboxing"
            print(f"🔍 Using fallback search: {search_query}")
        
        # Search for videos
        videos = self.search_youtube_videos(search_query, max_results=10)
        
        if not videos:
            return "No videos found for your search query."
        
        # Format the results
        result = "🎥 YouTube Video Recommendations:\n"
        result += "=" * 50 + "\n\n"
        
        for i, video in enumerate(videos, 1):
            result += f"{i}. 📺 {video['title']}\n"
            result += f"   👤 Channel: {video['channel_title']}\n"
            result += f"   📅 Published: {video['published_at'][:10]}\n"
            result += f"   🔗 URL: {video['url']}\n"
            result += f"   📝 Description: {video['description']}\n"
            result += "\n" + "-" * 40 + "\n\n"
        
        return result
    
    def get_follow_up_questions(self, user_query: str) -> List[str]:
        """Generate follow-up questions based on the user's initial query"""
        
        prompt = f"""
        You are an intelligent shopping assistant. The user has searched for: "{user_query}"
        
        Analyze the product type and generate EXACTLY 5 highly relevant, specific follow-up questions that would help narrow down their search.
        
        IMPORTANT: Make questions specific to the product type mentioned. For example:
        - For clothing: fabric type, occasion, season, fit preference, etc.
        - For electronics: specifications, brand preference, usage purpose, etc.
        - For shoes: type, size system, comfort level, activity, etc.
        - For jewelry: metal type, stone preference, occasion, etc.
        
        Focus on the 5 most important aspects:
        - Budget range, always remeber the price i will give is in indian rupees.
        - Specific preferences (color, style, material, etc.)
        - Size/dimensions
        - Brand preferences
        - Usage/occasion
        
        CRITICAL: You must respond with ONLY a valid JSON array of EXACTLY 5 question strings.
        Do not include any other text, explanations, or formatting.
        
        Example response:
        ["What's your budget range?", "What specific style are you looking for?", "Do you have any brand preferences?", "What size do you need?", "What's the primary use/occasion?"]
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Try to extract JSON from the response
            if response_text.startswith('[') and response_text.endswith(']'):
                questions = json.loads(response_text)
            else:
                # If the response isn't pure JSON, try to extract it
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    questions = json.loads(json_match.group())
                else:
                    # If no JSON found, split by lines and clean up
                    lines = response_text.split('\n')
                    questions = []
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('-'):
                            # Remove numbering if present
                            line = re.sub(r'^\d+\.\s*', '', line)
                            if line:
                                questions.append(line)
                    
                    if not questions:
                        raise Exception("Could not parse questions from response")
            
            return questions
        except Exception as e:
            print(f"Error generating questions: {e}")
            print("Using fallback questions...")
            # Fallback questions (exactly 5)
            return [
                "What's your budget range?",
                "What color do you prefer?",
                "Are you looking for male, female, or unisex items?",
                "What size do you need?",
                "Do you have any brand preferences?"
            ]
    
    def generate_summary(self, user_query: str, answers: Dict[str, str]) -> str:
        """Generate a summary of the user's requirements"""
        
        answers_text = "\n".join([f"- {question}: {answer}" for question, answer in answers.items()])
        
        prompt = f"""
        Based on the following information, create a concise shopping summary:
        
        Original Query: {user_query}
        
        User's Answers:
        {answers_text}
        
        Create a well-formatted summary that includes:
        1. Product category/type
        2. Key specifications
        3. Preferences
        4. Budget considerations
        
        Format it nicely for console output with clear sections.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating summary: {e}")
            return f"""
Shopping Summary:
===============
Original Query: {user_query}

Requirements:
{answers_text}

This summary can be used to search for products that match your criteria.
"""
    
    def run(self):
        """Main interaction loop"""
        print("🛍️  Welcome to the Smart Shopping Assistant!")
        print("=" * 50)
        
        # Get initial query
        user_query = input("What are you looking for today? (e.g., 'I want shoes', 'I need a laptop'): ").strip()
        
        if not user_query:
            print("Please provide a search query.")
            return
        
        print(f"\n🔍 Analyzing your search for: {user_query}")
        print("Generating personalized follow-up questions...\n")
        
        # Get follow-up questions
        questions = self.get_follow_up_questions(user_query)
        
        if not questions:
            print("Sorry, I couldn't generate questions. Please try again.")
            return
        
        # Ask follow-up questions
        answers = {}
        print("📝 Please answer the following questions (press Enter to skip any question):\n")
        
        for i, question in enumerate(questions, 1):
            print(f"{i}. {question}")
            answer = input("   Your answer: ").strip()
            
            if answer:  # Only store non-empty answers
                answers[question] = answer
            print()
        
        # Generate and display summary
        print("📋 Generating your shopping summary...\n")
        summary = self.generate_summary(user_query, answers)
        
        print("=" * 50)
        print("SHOPPING SUMMARY")
        print("=" * 50)
        print(summary)
        print("=" * 50)
        
        # Search for product recommendations
        print("\n🔍 Searching for product recommendations...\n")
        recommendations = self.search_product_recommendations(user_query, summary)
        
        print("=" * 50)
        print("PRODUCT RECOMMENDATIONS")
        print("=" * 50)
        print(recommendations)
        print("=" * 50)
        
        # Ask if user wants to search again
        while True:
            choice = input("\nWould you like to search for something else? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                print("\n" + "=" * 50)
                self.run()
                break
            elif choice in ['n', 'no']:
                print("Thank you for using the Smart Shopping Assistant! 👋")
                break
            else:
                print("Please enter 'y' or 'n'.")

def main():
    """Main function to run the shopping assistant"""
    try:
        assistant = ShoppingAssistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please check your internet connection and try again.")

if __name__ == "__main__":
    main() 