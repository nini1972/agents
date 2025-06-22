# SendGrid Inbound Parse Webhook Setup Guide - Friends Trip Planning

This guide will help you set up SendGrid's Inbound Parse Webhook to automatically respond to email replies from your friends about the trip planning. The system will act as Nini (the trip organizer) and respond to emails from Dominique, Vladimir, and Laura.

## Context

You have a group of 4 close friends planning a trip to Greece:
- **Nini Coenen** (ninicoe0@gmail.com) - The trip organizer, energetic and practical
- **Dominique Reyntjens** (drey@proximus.be) - Adventurous spirit, loves hiking
- **Vladimir Mylle** (vladimirmylle@hotmail.be) - History enthusiast, loves old films
- **Laura Myllette** (laura.mylle@hotmail.com) - Artistic, loves sketching, Vladimir's sister

The webhook will automatically respond to emails from your friends, maintaining the warm, personal tone of close friends planning an adventure together.

## Prerequisites

1. **SendGrid Account**: You already have this set up
2. **Domain**: You'll need a domain to receive emails (can be a subdomain)
3. **Public URL**: Your Flask app needs to be accessible from the internet

## Step 1: Deploy Your Flask App

### Option A: Deploy to Vercel (Recommended)

1. **Create a Vercel configuration file** (`vercel.json`):
```json
{
  "version": 2,
  "builds": [
    {
      "src": "email_responder.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "email_responder.py"
    }
  ]
}
```

2. **Create a requirements file** (`requirements.txt`):
```
flask==2.3.3
sendgrid==6.10.0
agents==0.1.0
python-dotenv==1.0.0
pandas==2.0.3
```

3. **Ensure you have the friends data file** (`friends_data.csv`):
```csv
EMAIL,FIRST_NAME,LAST_NAME,GENDER,ADDRESS_LINE_2
drey@proximus.be,Dominique,Reyntjens,female,Belgium
vladimirmylle@hotmail.be,Vladimir,Mylle,male,Belgium
laura.mylle@hotmail.com,Laura,Myllette,female,Belgium
ninicoe0@gmail.com,Nini,Coenen,female,Belgium
```

4. **Deploy to Vercel**:
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

5. **Set environment variables** in Vercel dashboard:
   - `SENDGRID_API_KEY` - Your SendGrid API key
   - `VERIFIED_SENDER_EMAIL` - Nini's email (ninicoe0@gmail.com)
   - `OPENAI_API_KEY` - Your OpenAI API key

### Option B: Use ngrok for Local Development

1. **Install ngrok**:
```bash
# Download from https://ngrok.com/
# or install via package manager
```

2. **Run your Flask app**:
```bash
python email_responder.py
```

3. **Expose your local server**:
```bash
ngrok http 5000
```

4. **Note the public URL** (e.g., `https://abc123.ngrok.io`)

## Step 2: Configure SendGrid Inbound Parse

### 2.1 Set Up Domain

1. **Option A: Use a Subdomain** (Recommended)
   - Go to your domain registrar (GoDaddy, Namecheap, etc.)
   - Add a CNAME record:
     - Name: `mail` (or `inbound`)
     - Value: `sendgrid.net`
   - This creates `mail.yourdomain.com` for receiving emails

2. **Option B: Use a Full Domain**
   - Add an MX record pointing to `mx.sendgrid.net`

### 2.2 Configure SendGrid Inbound Parse

1. Log into your SendGrid account
2. Go to **Settings** → **Inbound Parse**
3. Click **Add Host & URL**
4. Fill in the form:
   - **Hostname**: `mail.yourdomain.com` (or your chosen subdomain)
   - **URL**: `https://your-app-url.vercel.app/webhook/sendgrid` (or your ngrok URL)
   - **Check "POST the raw, full MIME message"**
   - **Check "Send Grid"** (optional, for logging)
5. Click **Save**

## Step 3: Update Your Email Sending Code

Update your existing email sending code to use the new domain. In your trip invitation scripts, add a Reply-To header:

```python
@function_tool
def send_html_email(subject: str, html_body: str) -> Dict[str, str]:
    """ Send out an email with the given subject and HTML body """
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("ninicoe0@gmail.com")  # Nini's email
    to_email = To("vladimirmylle@hotmail.be")  # Friend's email
    content = Content("text/html", html_body)
    
    # Create mail object
    mail = Mail(from_email, to_email, subject, content)
    
    # Add Reply-To header to enable replies
    mail.reply_to = "replies@mail.yourdomain.com"  # Your inbound parse domain
    
    # Get the mail object
    mail = mail.get()
    
    response = sg.client.mail.send.post(request_body=mail)
    return {"status": "success"}
```

## Step 4: Test the Setup

### 4.1 Test the Webhook Endpoint

1. **Test health check**:
```bash
curl -X GET https://your-app-url.vercel.app/webhook/sendgrid
```

2. **Test with simulated email from a friend**:
```bash
curl -X POST https://your-app-url.vercel.app/webhook/sendgrid \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "from=drey@proximus.be&to=replies@mail.yourdomain.com&subject=Re: Greece Trip Planning&text=Hi Nini! I'm so excited about the Greece trip! I found some amazing hiking trails in Crete. When do you think we should go?"
```

### 4.2 Test with Real Email

1. Send an email to `test@mail.yourdomain.com` from one of your friends' email addresses
2. Check your app logs for incoming webhook requests
3. Verify that an automated response is sent back from Nini

## Step 5: How the System Works

### 5.1 Personalized Responses

The system will:
- **Recognize each friend** by their email address
- **Use their first name** in responses (Dominique, Vladimir, Laura)
- **Reference their interests**:
  - Dominique: hiking trails, adventure
  - Vladimir: historical sites, old films
  - Laura: art scene, sketching
- **Maintain assigned tasks**:
  - Dominique: find hiking trails
  - Vladimir: look up historical sites
  - Laura: research local art scene

### 5.2 Response Examples

**From Dominique**: "Hi Nini! I found some amazing hiking trails in Crete!"
**Response**: "Hi Dominique! 🏔️ That's fantastic! I knew you'd find the perfect trails. Can you share the details? We're thinking spring would be ideal for hiking..."

**From Vladimir**: "I've been researching ancient ruins in Greece!"
**Response**: "Vladimir! 🏛️ Your historical expertise is exactly what we need! Which sites are you most excited about? Maybe we can plan a day where you lead us on a historical tour..."

**From Laura**: "The local art scene in Athens looks incredible!"
**Response**: "Laura! 🎨 I can't wait to see your sketches from Greece! Which art galleries caught your eye? We should definitely plan some time for you to capture the local culture..."

## Step 6: Monitor and Debug

### 6.1 Check Logs

- **Vercel**: Go to dashboard → Functions → View logs
- **Local with ngrok**: Check your terminal output
- **Other platforms**: Check their respective logging

### 6.2 Common Issues and Solutions

1. **Webhook not receiving emails**:
   - Check DNS settings for your domain
   - Verify SendGrid Inbound Parse configuration
   - Ensure your app URL is accessible

2. **Environment variables not working**:
   - Redeploy after adding environment variables
   - Check variable names match exactly

3. **Email responses not sending**:
   - Verify Nini's email (ninicoe0@gmail.com) is authenticated in SendGrid
   - Check SendGrid API key permissions

## Step 7: Advanced Features

### 7.1 Add Conversation Memory

Consider adding a database to store conversation history:

```python
# Add to your email_responder.py
import sqlite3

def store_conversation(sender_email, subject, content, response):
    conn = sqlite3.connect('trip_conversations.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversations (sender_email, subject, content, response, timestamp)
        VALUES (?, ?, ?, ?, datetime('now'))
    ''', (sender_email, subject, content, response))
    conn.commit()
    conn.close()

def get_conversation_history(sender_email):
    conn = sqlite3.connect('trip_conversations.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM conversations 
        WHERE sender_email = ? 
        ORDER BY timestamp DESC 
        LIMIT 5
    ''', (sender_email,))
    return cursor.fetchall()
```

### 7.2 Trip Planning Coordination

The system can help coordinate:
- **Task assignments** (hiking, history, art research)
- **Date coordination** (spring trip planning)
- **Budget discussions**
- **Accommodation preferences**
- **Activity planning**

## Security Considerations

1. **Validate webhook requests** (optional):
```python
import hmac
import hashlib

def verify_webhook_signature(request_body, signature, timestamp):
    # Implement SendGrid webhook signature verification
    pass
```

2. **Rate limiting** to prevent abuse
3. **Input sanitization** for email content
4. **Error handling** to prevent information leakage

## Next Steps

Once this is working, you can:

1. **Add trip planning coordination** features
2. **Integrate with calendar systems** for date planning
3. **Add budget tracking** for the trip
4. **Implement task management** for assigned responsibilities
5. **Add photo sharing** capabilities for trip planning

This setup will give you an automated trip planning assistant that maintains the warm, personal tone of close friends while helping coordinate your Greece adventure! 🏖️✈️ 