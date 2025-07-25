import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:3000/api"

def test_shopping_assistant_api():
    """Test the complete shopping assistant API flow"""
    
    print("🛍️ Testing Shopping Assistant API")
    print("=" * 50)
    
    # Step 1: Start a session with initial query
    print("\n1️⃣ Starting session with query: 'I want a laptop'")
    start_data = {
        "session_id": "test_session_001",
        "query": "I want a laptop",
        "max_videos": 15  # Configurable video count
    }
    
    response = requests.post(f"{BASE_URL}/start", json=start_data)
    if response.status_code == 200:
        result = response.json()
        session_id = result['session_id']
        questions = result['follow_up_questions']
        
        print(f"✅ Session created: {session_id}")
        print(f"📝 Follow-up questions generated: {len(questions)}")
        
        # Step 2: Answer questions one by one
        answers = [
            "1 lakh",  # Budget
            "Gaming and work",  # Primary use
            "16GB RAM, SSD",  # Specifications
            "15.6 inch",  # Screen size
            "HP or Dell"  # Brand preference
        ]
        
        for i, (question, answer) in enumerate(zip(questions, answers)):
            print(f"\n{i+2}️⃣ Answering question {i+1}: {question}")
            print(f"   Answer: {answer}")
            
            answer_data = {
                "session_id": session_id,
                "question_index": i,
                "answer": answer
            }
            
            response = requests.post(f"{BASE_URL}/answer", json=answer_data)
            
            if response.status_code == 200:
                result = response.json()
                
                if result['step'] == 'complete':
                    print(f"✅ All questions answered!")
                    print(f"📋 Summary: {result['summary'][:100]}...")
                    print(f"🎥 Recommendations: {result['recommendations'][:100]}...")
                    break
                else:
                    print(f"   Next question: {result['next_question']}")
                    print(f"   Progress: {result['questions_answered']}/{result['total_questions']}")
            else:
                print(f"❌ Error: {response.text}")
                break
                
    else:
        print(f"❌ Error starting session: {response.text}")

def test_health_check():
    """Test the health check endpoint"""
    print("\n🏥 Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("✅ API is healthy!")
    else:
        print(f"❌ API health check failed: {response.text}")

def test_session_status():
    """Test getting session status"""
    print("\n📊 Testing session status...")
    session_id = "test_session_001"
    response = requests.get(f"{BASE_URL}/status/{session_id}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Session status: {result['step']}")
        print(f"   Questions answered: {result['questions_answered']}/{result['total_questions']}")
    else:
        print(f"❌ Error getting session status: {response.text}")

def test_answer_all():
    """Test answering all questions at once"""
    print("\n🚀 Testing answer-all API...")
    
    # Start a new session
    start_data = {
        "session_id": "test_session_all",
        "query": "I want shoes",
        "max_videos": 20  # Configurable video count
    }
    
    response = requests.post(f"{BASE_URL}/start", json=start_data)
    if response.status_code == 200:
        result = response.json()
        session_id = result['session_id']
        questions = result['follow_up_questions']
        
        print(f"✅ Session created: {session_id}")
        print(f"📝 Questions to answer: {len(questions)}")
        
        # Answer all questions at once
        all_answers = [
            "Under 5000 rupees",  # Budget
            "Running shoes",      # Type
            "Size 9",            # Size
            "Nike or Adidas",    # Brand
            "For daily running"  # Purpose
        ]
        
        print(f"\n📝 Submitting all answers at once:")
        for i, (question, answer) in enumerate(zip(questions, all_answers), 1):
            print(f"   {i}. {question}")
            print(f"      Answer: {answer}")
        
        answer_all_data = {
            "session_id": session_id,
            "answers": all_answers
        }
        
        response = requests.post(f"{BASE_URL}/answer-all", json=answer_all_data)
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ All questions answered successfully!")
            print(f"📋 Summary: {result['summary'][:100]}...")
            print(f"🎥 Recommendations: {result['recommendations'][:100]}...")
        else:
            print(f"❌ Error answering all questions: {response.text}")
    else:
        print(f"❌ Error starting session: {response.text}")

def test_youtuber_comments():
    """Test the YouTuber comments API"""
    print("\n🎥 Testing YouTuber comments API...")
    
    comment_data = {
        "product_query": "laptop under 1 lakh",
        "max_videos": 5  # Test with 5 videos first
    }
    
    response = requests.post(f"{BASE_URL}/youtuber-comments", json=comment_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Generated {result['total_videos']} YouTuber comments")
        print(f"🔍 Search query used: {result['search_query_used']}")
        
        print("\n📝 Sample YouTuber Comments:")
        for i, comment in enumerate(result['youtuber_comments'][:3], 1):  # Show first 3
            print(f"\n{i}. Channel: {comment['channel_name']}")
            print(f"   Video: {comment['video_title'][:50]}...")
            print(f"   Comment: {comment['comment']}")
            print(f"   URL: {comment['video_url']}")
    else:
        print(f"❌ Error generating YouTuber comments: {response.text}")

if __name__ == "__main__":
    # Test health check first
    test_health_check()
    
    # Test the complete flow (one by one)
    test_shopping_assistant_api()
    
    # Test answering all questions at once
    test_answer_all()
    
    # Test session status
    test_session_status()
    
    # Test YouTuber comments
    test_youtuber_comments() 