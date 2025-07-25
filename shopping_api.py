from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import json
import random
import re
import requests
import time
from typing import Dict, List, Any
from serpapi import SerpResults
from serpapi import Client, SerpResults


app = Flask(__name__)
CORS(app)

# Configure Gemini API and YouTube Data API
API_KEY = "AIzaSyAQ-V9IvNDDegtQ2yhGUDQy7uF0zq1ajsM"


API_KEYS_LIST = [
    "AIzaSyAQ-V9IvNDDegtQ2yhGUDQy7uF0zq1ajsM",
    "AIzaSyA-JnfuCQglWtTAvLudidQOGAP70Ksqms4",
    "AIzaSyBATxvLLb48oXpd45qol9PxjZjoVZZA390",
    "AIzaSyAkKp5VDmxAeiNBpyjAsqYl8ec2g5FeKos"
]

genai.configure(api_key=API_KEY)

class ShoppingAssistantAPI:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.youtube_api_key = API_KEY
        self.youtube_base_url = "https://www.googleapis.com/youtube/v3"
        self.sessions = {}  # Store session data
    
    def create_session(self, session_id: str):
        """Create a new session"""
        self.sessions[session_id] = {
            'user_query': '',
            'follow_up_questions': [],
            'answers': {},
            'summary': '',
            'step': 'initial'
        }
    
    def get_follow_up_questions(self, user_query: str) -> List[str]:
        """Generate follow-up questions based on the user's initial query"""
        
        prompt = f"""
        You are an intelligent shopping assistant. The user has searched for: "{user_query}"

        **Task:** Analyze the product type from the user's query. Identify any constraints already provided (e.g., budget, color, specific features). Based on this analysis, generate EXACTLY 3 highly relevant follow-up questions to help refine the search.

        **Key Requirements:**
        1.  **Product Relevance:** Questions must be specific to the product category identified in the user's query.
        2.  **Avoid Redundancy:** Critically, do NOT ask questions that merely rephrase or slightly adjust constraints already present in the original query ("{user_query}"). Instead, focus on exploring *different, important aspects* of the product search that are likely *not* covered by the initial query. The goal is to gather new information, not confirm existing details.
        3.  **Prioritize Aspects:** Aim to cover a range of important clarifying factors relevant to the product category. Consider these core areas, adapting them based on the specific product and the initial query:
            *   **Budget:** Ask for a range in INR if not specified, or focus on other aspects if budget is clear. Do not ask for a narrower budget than initially provided.
            *   **Key Features/Preferences:** Ask about specific attributes, style elements, materials, technology, etc., that define the product category and go beyond the original query.
            *   **Size/Fit/Dimensions:** Inquire about necessary measurements, sizing standards, or physical characteristics relevant to the product.
            *   **Brand:** Explore user's brand preferences, requirements, or brands to avoid.
            *   **Usage/Occasion:** Understand the intended use, environment, setting, or purpose for the product.
        4.  **Example Guidance:**
            *   If query is "budget android mobile under 15000":
                *   Good: "What camera quality is most important to you?", "Do you have a preferred screen size?", "Are there specific brands you trust or want to avoid?", "What will be the primary use of the phone (gaming, work, photography)?", "What battery life are you expecting?"
                *   Bad: "How about mobiles under 12000?", "Do you need a budget mobile?", "Are you looking for Android?"
            *   If query is "red running shoes":
                *   Good: "What type of surface will you primarily run on (road, trail, track)?", "What level of cushioning do you prefer?", "Do you have any preferred brands for athletic footwear?", "What size standard do you typically wear (US, UK, EU)?", "Is there a specific type of running (e.g., marathon, casual jogging)?"
                *   Bad: "Do you want dark red or light red?", "Are you sure you want red shoes?"

        **Output Format:**
        *   Respond with ONLY a valid JSON array containing EXACTLY 3 question strings.
        *   Ensure the questions are distinct from each other and from the original query "{user_query}".
        *   Do not include any introductory text, explanations, apologies, reasoning, or any other content outside the JSON array. Ensure the JSON is correctly formatted.

        **Example JSON Response Structure:**
        ["What's your budget range for this item (in INR)?", "What specific style or features are you looking for?", "Do you have any brand preferences?", "What size or dimensions do you require?", "What is the intended use or occasion?"]
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
        
    
    def safe_generate_content(self, prompt, max_retries=10):
        for attempt in range(max_retries):
            gemini_key = random.choice(API_KEYS_LIST)
            genai.configure(api_key=gemini_key)
            try:
                response = self.model.generate_content(prompt)
                response_text = getattr(response, "text", "").strip() if response else ""
                if response_text:
                    return response_text
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
            
            time.sleep(0.2)  # wait before retrying
        return ""  # Return empty string if all attempts fail
    


    def serpapi_api_google_search(self,videos_info):
        def has_url(text):
            url_pattern = r'http?://\S+|www\.\S+'
            return bool(re.search(url_pattern, text))
        videos_info = videos_info[:5]
        product_name_list = []
        product_list = []
        description_list = []
        for info in videos_info:
            if info.get('description', None) is not None:
                if has_url(info.get('description')):
                    description_list.append(info['description'])
                    product_name_list.append(info.get('title', 'Title not found'))
            
        prompt = f"""
            You are a specialized AI model designed for a single purpose: to extract or suggest electronic device names from multiple YouTube video descriptions. Your analysis and response must follow a strict set of rules.

            Core Logic:

            Your task is to analyze the provided text and determine if it refers to a specific, named electronic device (such as a smartphone, laptop, smartwatch, earbuds, tablet, camera, etc.) or a general category/price range of devices. First, try to extract the exact name of the product from the descriptions. If no specific product name is found, then suggest some relevant options.

            First of all collate all the descriptions and then analyze them, as if it were a single description.

            Case 1: Specific Product Name Found
            If the description explicitly mentions a single specific electronic product (e.g., "Samsung Galaxy S24 Ultra", "MacBook Air M3", "Sony WH-1000XM5"), your ONLY output should be that exact model name.

            Case 2: General Category or Price Range Found
            If the description refers to a general category, price bracket, or a use case (e.g., "best tablets under ₹30000", "top laptops for coding", "best smartwatches in India"), you MUST suggest a list of 3-5 relevant, popular, and currently available products in that category, specifically for the Indian market.

            Case 3: Specific Product Names Found
            If the description explicitly mentions multiple specific electronic products (e.g., "Samsung Galaxy S24 Ultra", "MacBook Air M3", and "Sony WH-1000XM5"), your ONLY output should be all the product names in multiple lines.

            Strict Output Rules:

            Your response MUST ONLY contain the product name(s).

            Do NOT include any introductory text, explanations, headers, or conversational phrases (e.g., "Here are some suggestions:", "The product is:", "Based on the description...").

            If suggesting multiple products (Case 2), list each product on a new line.

            Do NOT use bullet points (-), numbering (1.), or any other formatting symbols.

            The entire response from start to finish must consist solely of the product name or a line-by-line list of product names. This is a strict requirement.

            Examples (Follow this format precisely)

            Scenario 1: Specific Product Mentioned
            Input Description: Full review of the brand new MacBook Air M3. We cover battery life, performance, and display in depth.
            Correct Output:
            MacBook Air M3

            Scenario 2: General Category (Under a Price)
            Input Description: Looking for the best earbuds under ₹3000? We test 5 popular models to find the one with best bass, mic, and comfort.
            Correct Output:
            OnePlus Nord Buds 2
            Realme Buds T300
            boAt Airdopes 141
            Noise Air Buds Pro 3
            Boult Z40

            Scenario 3: General Category (Use Case)
            Input Description: Best tablets for students in India right now. Perfect for online classes, note-taking, and media consumption.
            Correct Output:
            Xiaomi Pad 6
            Samsung Galaxy Tab A9+
            Realme Pad 2
            Lenovo Tab M10 3rd Gen

            Scenario 4: Specific Product Mentioned
            Input Description: Unboxing and hands-on of the new Sony WH-1000XM5 headphones. Are they worth the upgrade?
            Correct Output:
            Sony WH-1000XM5

            Scenario 5: General Product Need (Vague but Clear Intent)
            Input Description: Buying a new laptop for college? We list our favorite picks that balance performance and price for students.
            Correct Output:
            HP Pavilion Plus 14
            Lenovo IdeaPad Slim 5
            Asus Vivobook 16X
            Dell Inspiron 14

            Input field:
            Here is the input -> {description_list}
                    """
        response = self.safe_generate_content(prompt)
        
        temp_list = [line.strip() for line in response.strip().split('\n') if line.strip()]
        product_list.extend(temp_list)
        client = Client(api_key="6a7330c862cb8e9863311fdf80ecc13c31cc8f1a674bf8581f0a6c084a4282c2")
        product_details = {}
        print(product_list)
        product_list = product_list[:5]


        def fetch_top_result(query, mobile, site):
            """Query Google using SerpAPI and return the top organic result with extracted price."""
            
            # Step 1: Perform the search
            response = client.search({
                "engine": "google",
                "q": query,
                "location": "India",
                "hl": "en",
                "gl": "in"
            })

            results = response.get("organic_results", [])
            if not results:
                return {}

            top_result = results[0]
            snippet = top_result.get("snippet", "").strip()
            print(snippet)
            # Step 2: If no snippet found, skip price extraction
            if not snippet:
                price = ""
            else:
                # Step 3: Generate appropriate prompt based on site
                if site.lower() != "meesho":

                    snippet_prompt =  f"""
        you are given the 1 snippet text extract the price from the snippet return only the price donnot return anything. Return only 1 row 
        Input  - > {snippet}
                    """
                else:
                    snippet_prompt = f""" You are an AI assistant tasked with extracting the price of a specific product from a Google search snippet.
                    **Target Product Name:** {mobile}

                    **Input:** A single Google search snippet text provided below.

                    **Instructions:**
                    1.  Carefully examine the input snippet.
                    2.  Identify if a price is mentioned.
                    3.  **Crucial Rule:** Only return the price if it is unambiguously associated with the **exact target product** ({mobile}).
                    4.  **Condition:** If the snippet mentions an accessory (e.g., "cover", "case", "strap","charger","plug") or a variation *instead of* the main product, and provides a price for that accessory/variation, you must **NOT** return that price.
                    5.  If the snippet clearly states the price for the "iphone 16 pro max" product itself, extract and return *only* that price string (including the currency symbol).
                    6.  If the snippet does not contain the target product name, or if the mentioned price belongs to an accessory/variation as described in point 4, return an empty string.

                    **Output Format:**
                    *   Return *only* the extracted price on a single line.
                    *   Do not include any descriptive text, labels, or explanations.
                    *   If no valid price is found based on the rules, return an empty line.

                    **Example:**
                    **Product Name:** Iphone 16 Promax
                    **Input Snippet:**
                    Iphone 16 Promax green silicone cover · ₹172 · Shop Non-Stop on Meesho.


                    **Reasoning:** The snippet mentions "Iphone 16 Promax" but specifies it is a "green silicone cover". The price ₹172 is for the cover, not the phone itself.

                    **Expected Output:**
                    (An empty line)

                    ---

                    **Process the following input snippet:**

                    **Input Snippet:**
                    {snippet}

                                """
            try:
                # gen_output = self.model.generate_content(snippet_prompt)
                price = self.safe_generate_content(snippet_prompt)
            except Exception as e:
                price = ""

            if results:
                return {
                    "title": results[0].get("title"),
                    "link": results[0].get("link"),
                    "snippet": results[0].get("snippet"),
                    "thumbnail": results[0].get("thumbnail"),
                    "price": price,
                }
            
            return {}
        
        for mobile in product_list:
            product_details[mobile] = {}
            
            for site in ["amazon", "flipkart","meesho"]:
                print(mobile,site)
                query = f"{mobile} price on {site} india"
                product_details[mobile][site] = fetch_top_result(query,mobile,site)
        return product_details
        
        



            
    
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
    
    def search_product_recommendations(self, user_query: str, summary: str, max_videos: int = 10) -> str:
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
        except Exception as e:
            print(f"Error generating search query: {e}")
            search_query = f"{user_query} review unboxing"
        
        # Search for videos
        videos = self.search_youtube_videos(search_query, max_results=max_videos)
        
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
    
    def generate_youtuber_comments(self, videos: List[Dict], product_query: str) -> List[Dict]:
        """Generate realistic personal comments from YouTubers about the products"""
        
        comments = []
        
        for video in videos:
            # Create a prompt for generating realistic YouTuber comments
            comment_prompt = f"""
            You are a YouTube content creator named "{video['channel_title']}" who has reviewed a product.
            
            Video Title: {video['title']}
            Video Description: {video['description']}
            Product Query: {product_query}
            
            Based on the video title and description, write a realistic, personal comment that this YouTuber would make about the product. 
            
            The comment should:
            - Sound like a real person speaking naturally
            - Include the YouTuber's channel name
            - Mention the product name
            - Be 1-2 lines maximum
            - Show genuine opinion (positive or negative, but realistic)
            - Use casual, conversational language like real YouTubers do
            
            Examples of good comments:
            - "Hey guys! {video['channel_title']} here. This laptop is absolutely amazing for gaming, definitely worth the investment!"
            - "As {video['channel_title']}, I have to say this product exceeded my expectations. Great value for money!"
            
            Return ONLY the comment, nothing else.
            """
            
            try:
                response = self.model.generate_content(comment_prompt)
                comment = response.text.strip()
                
                comments.append({
                    'channel_name': video['channel_title'],
                    'video_title': video['title'],
                    'video_url': video['url'],
                    'comment': comment,
                    'thumbnail': video['thumbnail']
                })
                
            except Exception as e:
                print(f"Error generating comment for {video['channel_title']}: {e}")
                # Fallback comment
                comments.append({
                    'channel_name': video['channel_title'],
                    'video_title': video['title'],
                    'video_url': video['url'],
                    'comment': f"Hey everyone! {video['channel_title']} here. This product looks really promising based on my review!",
                    'thumbnail': video['thumbnail']
                })
        
        return comments

# Initialize the assistant
assistant = ShoppingAssistantAPI()

@app.route('/api/start', methods=['POST'])
def start_session():
    """Start a new shopping session with initial query"""
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        session_id = data.get('session_id', 'default')
        max_videos = data.get('max_videos', 10)  # Default to 10 videos
        
        if not user_query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Create session
        assistant.create_session(session_id)
        assistant.sessions[session_id]['user_query'] = user_query
        assistant.sessions[session_id]['max_videos'] = max_videos  # Store for later use
        
        # Generate follow-up questions
        questions = assistant.get_follow_up_questions(user_query)
        assistant.sessions[session_id]['follow_up_questions'] = questions
        assistant.sessions[session_id]['step'] = 'questions'
        
        return jsonify({
            'session_id': session_id,
            'user_query': user_query,
            'follow_up_questions': questions,
            'max_videos': max_videos,
            'message': 'Session started successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/answer', methods=['POST'])
def submit_answer():
    """Submit answer to a follow-up question"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        question_index = data.get('question_index')  # 0-based index
        answer = data.get('answer', '').strip()
        
        if session_id not in assistant.sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        if question_index is None:
            return jsonify({'error': 'Question index is required'}), 400
        
        session = assistant.sessions[session_id]
        
        if question_index >= len(session['follow_up_questions']):
            return jsonify({'error': 'Invalid question index'}), 400
        
        # Store the answer
        question = session['follow_up_questions'][question_index]
        session['answers'][question] = answer
        
        # Check if all questions are answered
        if len(session['answers']) == len(session['follow_up_questions']):
            # Generate summary and recommendations
            summary = assistant.generate_summary(session['user_query'], session['answers'])
            max_videos = session.get('max_videos', 10)  # Get stored max_videos
            recommendations = assistant.search_product_recommendations(session['user_query'], summary, max_videos)
            
            session['summary'] = summary
            session['step'] = 'complete'
            
            return jsonify({
                'session_id': session_id,
                'step': 'complete',
                'summary': summary,
                'recommendations': recommendations,
                'message': 'All questions answered. Here are your results!'
            })
        else:
            # Return next question info
            next_question_index = len(session['answers'])
            next_question = session['follow_up_questions'][next_question_index]
            
            return jsonify({
                'session_id': session_id,
                'step': 'questions',
                'next_question_index': next_question_index,
                'next_question': next_question,
                'questions_answered': len(session['answers']),
                'total_questions': len(session['follow_up_questions']),
                'message': f'Question {next_question_index + 1} of {len(session["follow_up_questions"])}'
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/answer-all', methods=['POST'])
def submit_all_answers():
    """Submit all answers to follow-up questions at once"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        answers = data.get('answers', [])  # Array of answers in order
        
        if session_id not in assistant.sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = assistant.sessions[session_id]
        total_questions = len(session['follow_up_questions'])
        
        if len(answers) != total_questions:
            return jsonify({
                'error': f'Expected {total_questions} answers, got {len(answers)}',
                'expected_count': total_questions,
                'received_count': len(answers)
            }), 400
        
        # Store all answers
        for i, answer in enumerate(answers):
            question = session['follow_up_questions'][i]
            session['answers'][question] = answer.strip()
        
        # Generate summary and recommendations
        summary = assistant.generate_summary(session['user_query'], session['answers'])
        max_videos = session.get('max_videos', 10)  # Get stored max_videos
        recommendations = assistant.search_product_recommendations(session['user_query'], summary, max_videos)
        
        session['summary'] = summary
        session['step'] = 'complete'
        
        return jsonify({
            'session_id': session_id,
            'step': 'complete',
            'summary': summary,
            'recommendations': recommendations,
            'questions_answered': len(session['answers']),
            'total_questions': total_questions,
            'message': 'All questions answered. Here are your results!'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<session_id>', methods=['GET'])
def get_session_status(session_id):
    """Get current session status"""
    try:
        if session_id not in assistant.sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session = assistant.sessions[session_id]
        
        return jsonify({
            'session_id': session_id,
            'step': session['step'],
            'user_query': session['user_query'],
            'questions_answered': len(session['answers']),
            'total_questions': len(session['follow_up_questions']),
            'summary': session.get('summary', ''),
            'follow_up_questions': session.get('follow_up_questions', [])
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/youtuber-comments', methods=['POST'])
def get_youtuber_comments():
    """Generate realistic YouTuber comments based on video data"""
    try:
        data = request.get_json()
        product_query = data.get('product_query', '').strip()
        max_videos = data.get('max_videos', 15)  # Default to 15 videos
        
        if not product_query:
            return jsonify({'error': 'Product query is required'}), 400
        
        # Generate search query using Gemini
        search_prompt = f"""
        Based on this product query, create a natural YouTube search query that a human would type.
        
        Product Query: {product_query}
        
        Create a simple, natural search query like how people actually search on YouTube.
        Include the product and any specific requirements, but keep it conversational and natural.
        
        Examples of good queries:
        - "laptop under 1 lakh"
        - "best gaming laptop"
        - "iPhone 15 review"
        - "shoes for running"
        
        Return ONLY the search query in one line, nothing else.
        """
        
        try:
            response = assistant.model.generate_content(search_prompt)
            search_query = response.text.strip()
        except Exception as e:
            print(f"Error generating search query: {e}")
            search_query = f"{product_query} review unboxing"
        
        # Search for videos
        videos = assistant.search_youtube_videos(search_query, max_results=max_videos)
        comparision_detail = assistant.serpapi_api_google_search(videos)
        
        if not videos:
            return jsonify({'error': 'No videos found for the query'}), 404
        
        # Generate YouTuber comments
        comments = assistant.generate_youtuber_comments(videos, product_query)
        
        return jsonify({
            'product_query': product_query,
            'search_query_used': search_query,
            'total_videos': len(videos),
            'youtuber_comments': comments,
            'comparison_details': comparision_detail,
            'message': f'Generated {len(comments)} YouTuber comments successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Shopping Assistant API is running'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000) 