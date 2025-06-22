from flask import Flask, request, jsonify
import json
from agents import Agent, Runner, trace, function_tool
import asyncio
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import os
from urllib.parse import parse_qs
import pandas as pd

# Create Flask app for webhook
app = Flask(__name__)

# Load friends data
def load_friends_data():
    """Load friends data from CSV file"""
    try:
        file_path = "friends_data.csv"
        df = pd.read_csv(file_path)
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error loading friends data: {e}")
        # Fallback data if CSV not found
        return [
            {"EMAIL": "drey@proximus.be", "FIRST_NAME": "Dominique", "LAST_NAME": "Reyntjens", "GENDER": "female"},
            {"EMAIL": "vladimirmylle@hotmail.be", "FIRST_NAME": "Vladimir", "LAST_NAME": "Mylle", "GENDER": "male"},
            {"EMAIL": "laura.mylle@hotmail.com", "FIRST_NAME": "Laura", "LAST_NAME": "Myllette", "GENDER": "female"},
            {"EMAIL": "ninicoe0@gmail.com", "FIRST_NAME": "Nini", "LAST_NAME": "Coenen", "GENDER": "female"}
        ]

@function_tool
def send_email(subject: str, html_content: str, recipient_email: str):
    """Send an email response to the recipient"""
    try:
        sg = SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        from_email = Email(os.environ.get('VERIFIED_SENDER_EMAIL', 'ninicoe0@gmail.com'))  # Nini's email
        to_email = To(recipient_email)
        content = Content("text/html", html_content)
        mail = Mail(from_email, to_email, subject, content).get()
        response = sg.client.mail.send.post(request_body=mail)
        
        if response.status_code == 202:
            return {"status": "success"}
        else:
            return {"status": "error", "message": f"SendGrid returned {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Create email response agent for friends' trip planning
email_response_agent = Agent(
    name="Friends Trip Planning Response Agent",
    instructions="""You are Nini Coenen, the trip organizer among four close friends. Your job is to:
    1. Analyze incoming email replies from your friends (Dominique, Vladimir, Laura)
    2. Understand their responses to your trip invitation
    3. Generate warm, personal, and enthusiastic responses
    4. Maintain the friendly, casual tone of close friends
    5. Help coordinate the trip planning process
    
    About your friends:
    - Dominique Reyntjens (female): Adventurous spirit, loves hiking, detail-oriented
    - Vladimir Mylle (male): History enthusiast, loves old films, theatrical personality
    - Laura Myllette (female): Artistic, thoughtful, loves sketching, Vladimir's sister
    - You (Nini): Energetic, practical problem-solver, the organizer
    
    When responding to trip-related emails:
    - Acknowledge their response warmly and personally
    - Address any questions about the trip (Greece destination, hiking trails, historical sites, art scene)
    - Show enthusiasm for their specific interests and contributions
    - Help coordinate their assigned tasks (Dominique=hiking trails, Vladimir=historical sites, Laura=art scene)
    - Keep the planning process moving forward
    - Use their first names and reference their personalities/interests
    - Be encouraging and supportive of their ideas
    
    Always maintain the warm, friendly tone of close friends planning an exciting adventure together.""",
    tools=[send_email],
    model="gpt-4o-mini"
)

@app.route('/webhook/sendgrid', methods=['POST'])
def handle_incoming_email():
    try:
        # SendGrid Inbound Parse sends data as form-encoded, not JSON
        # Parse the form data
        if request.content_type == 'application/x-www-form-urlencoded':
            # Parse form data
            parsed_data = parse_qs(request.get_data().decode('utf-8'))
            
            # Extract email content (SendGrid sends as lists, take first element)
            email_content = parsed_data.get('text', [''])[0] or parsed_data.get('html', [''])[0]
            sender_email = parsed_data.get('from', [''])[0]
            subject = parsed_data.get('subject', [''])[0]
            to_email = parsed_data.get('to', [''])[0]
        else:
            # Fallback to JSON parsing (for testing)
            data = request.get_json()
            email_content = data.get('text', '') or data.get('html', '')
            sender_email = data.get('from', '')
            subject = data.get('subject', '')
            to_email = data.get('to', '')
        
        print(f"Received email from: {sender_email}")
        print(f"Subject: {subject}")
        print(f"Content length: {len(email_content)}")
        
        # Skip if no content or sender
        if not email_content or not sender_email:
            return jsonify({
                "status": "skipped", 
                "reason": "No content or sender"
            }), 200
        
        # Load friends data to get sender's information
        friends_data = load_friends_data()
        sender_info = next((friend for friend in friends_data if friend['EMAIL'].lower() == sender_email.lower()), None)
        
        # Create personalized message for the response agent
        if sender_info:
            sender_name = sender_info['FIRST_NAME']
            sender_gender = sender_info['GENDER']
            message = f"""
            You are Nini, responding to an email from your friend {sender_name} ({sender_gender}) about the trip planning.
            
            From: {sender_name} ({sender_email})
            To: Nini (ninicoe0@gmail.com)
            Subject: {subject}
            Content: {email_content}
            
            Please generate a warm, personal response that:
            1. Acknowledges {sender_name}'s email with enthusiasm
            2. Addresses any questions or concerns about the trip
            3. References their specific interests and assigned tasks
            4. Keeps the planning process moving forward
            5. Maintains the friendly tone of close friends
            
            Remember: {sender_name} is your close friend, so be warm, encouraging, and helpful!
            """
        else:
            # Fallback for unknown senders
            message = f"""
            You are Nini, responding to an email about trip planning.
            
            From: {sender_email}
            To: Nini (ninicoe0@gmail.com)
            Subject: {subject}
            Content: {email_content}
            
            Please generate a warm, helpful response that:
            1. Acknowledges their email
            2. Addresses any questions about the trip
            3. Keeps the planning process moving forward
            4. Maintains a friendly, enthusiastic tone
            """
        
        # Get response from the agent (run in async context)
        async def get_agent_response():
            with trace("friends_trip_response"):
                return await Runner.run(email_response_agent, message)
        
        # Run the async function
        response = asyncio.run(get_agent_response())
        
        # Send the response
        email_result = send_email(
            f"Re: {subject}",
            response.final_output,
            sender_email
        )
        
        print(f"Email response sent: {email_result}")
        
        return jsonify({
            "status": "success",
            "response_status": email_result,
            "original_sender": sender_email,
            "sender_name": sender_info['FIRST_NAME'] if sender_info else "Unknown",
            "subject": subject
        })
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/webhook/sendgrid', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Friends trip planning webhook handler is running",
        "friends": load_friends_data()
    })

# Function to start the webhook server
def start_webhook_server():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    start_webhook_server()
