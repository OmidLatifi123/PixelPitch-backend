const express = require('express');
const { Server } = require('socket.io');
const http = require('http');
const axios = require('axios');
const base64 = require('base64-js');
const { OpenAI } = require('openai');
const bodyParser = require('body-parser');
require("dotenv").config()



// Initialize Express App
const app = express();
// fix cors issue
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    next();
});
// access control allow headers json
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Headers', 'Content-Type');
    next();
});


// parse application/json
app.use(bodyParser.json());


const server = http.createServer(app);
const io = new Server(server, {
    pingTimeout: 60000,  // 1 minute (default is 5000 ms)
    pingInterval: 25000,  // 25 seconds (default is 25000 ms)
});




const openai = new OpenAI({ apiKey: process.env.OPENAI_KEY});

// Global variables for the frame and interval
let oldframe = null;
let intervalId = null;  // To track the interval



async function analyzeFrameWithOpenAI(base64Image) {
    try {
        console.log('Calling OpenAI with image data length:', base64Image.length);
        
        const response = await openai.chat.completions.create({
            model: 'gpt-4o-mini',  // Updated model name
            max_tokens: 500,
            messages: [
                {
                    role: 'system',
                    content: `You are an expert pitch coach analyzing presentation performance. 
                    Focus on body language, facial expressions, and apparent confidence level.
                    Provide real-time feedback in a structured JSON format.`
                },
                {
                    role: 'user',
                    content: [
                        {
                            type: 'text',
                            text: 'Analyze this frame of a pitch presentation and provide scores and feedback in JSON format like this: {"confidence": (0-100), "engagement": (0-100), "clarity": (0-100), "feedback": "brief tip", "body_language": "observation", "expression": "observation"}'
                        },
                        {
                            type: 'image_url',
                            image_url: {
                                url: `data:image/jpeg;base64,${base64Image}`
                            }
                        }
                    ]
                }
            ]
        });

        console.log('OpenAI response received:', response);
        const data = await extractJsonFromResponse(response);
        console.log('Extracted data:', data);
        return data;
    } catch (error) {
        console.error('Full error in analyzeFrameWithOpenAI:', error);
        if (error.response) {
            console.log('Error response:', error.response.data);
        }
        return { 
            error: error.message,
            details: error.response?.data || 'No additional details'
        };
    }
}
// // Add new endpoint for animal-specific feedback
// app.post('/animal-feedback', async (req, res) => {
//     const { animal, pitchContent } = req.body;
    
//     const animalPrompts = {
//         leo: `As Leo the Lion, a charismatic leader focused on vision and strategy, analyze this pitch section:
//               ${pitchContent}
              
//               Provide feedback on:
//               1. Clarity of vision
//               2. Leadership potential
//               3. Strategic thinking
              
//               Return as JSON:
//               {
//                 "vision_score": (0-100),
//                 "leadership_score": (0-100),
//                 "strategy_score": (0-100),
//                 "feedback": "key observation",
//                 "strength": "biggest strength",
//                 "improvement": "area to improve"
//               }`,
              
//         owlbert: `As Owlbert the Owl, a technical expert focused on implementation and innovation, analyze this pitch section:
//                   ${pitchContent}
                  
//                   Provide feedback on:
//                   1. Technical clarity
//                   2. Implementation feasibility
//                   3. Innovation level
                  
//                   Return as JSON:
//                   {
//                     "technical_score": (0-100),
//                     "feasibility_score": (0-100),
//                     "innovation_score": (0-100),
//                     "feedback": "key observation",
//                     "strength": "biggest strength",
//                     "improvement": "area to improve"
//                   }`,
                  
//         rocket: `As Rocket the Rabbit, a growth and metrics expert, analyze this pitch section:
//                 ${pitchContent}
                
//                 Provide feedback on:
//                 1. Growth potential
//                 2. Metric clarity
//                 3. Market understanding
                
//                 Return as JSON:
//                 {
//                     "growth_score": (0-100),
//                     "metrics_score": (0-100),
//                     "market_score": (0-100),
//                     "feedback": "key observation",
//                     "strength": "biggest strength",
//                     "improvement": "area to improve"
//                 }`,
                
//         elephant: `As Elle the Elephant, a market research and competition expert, analyze this pitch section:
//                   ${pitchContent}
                  
//                   Provide feedback on:
//                   1. Market analysis
//                   2. Competitive positioning
//                   3. Business model viability
                  
//                   Return as JSON:
//                   {
//                     "market_score": (0-100),
//                     "competition_score": (0-100),
//                     "viability_score": (0-100),
//                     "feedback": "key observation",
//                     "strength": "biggest strength",
//                     "improvement": "area to improve"
//                   }`
//     };

//     try {
//         const response = await openai.chat.completions.create({
//             model: 'gpt-4',
//             messages: [
//                 {
//                     role: 'system',
//                     content: animalPrompts[animal] || 'Provide pitch feedback'
//                 },
//                 {
//                     role: 'user',
//                     content: pitchContent
//                 }
//             ],
//             max_tokens: 500
//         });

//         const result = await extractJsonFromResponse(response);
//         res.json(result);
//     } catch (error) {
//         console.error('Error getting animal feedback:', error.message);
//         res.json({ error: error.message });
//     }
// });
// Function to extract JSON from the response
async function extractJsonFromResponse(response) {
    try {
        console.log('Raw response from OpenAI:', response.choices[0].message.content);
        const message = response.choices[0].message.content;
        
        // First try parsing the message directly as it might already be JSON
        try {
            const directJson = JSON.parse(message);
            console.log('Successfully parsed direct JSON:', directJson);
            return directJson;
        } catch (err) {
            console.log('Direct JSON parse failed, trying to extract JSON from text');
        }

        // Try extracting JSON from markdown code blocks
        let match = message.match(/```json\s*(\{.*?\})\s*```/s);
        if (!match) {
            console.log('No JSON code block found, trying to find raw JSON');
            match = message.match(/(\{.*?\})/s);
        }

        if (match) {
            const jsonStr = match[1];
            console.log('Found JSON string:', jsonStr);
            try {
                const data = JSON.parse(jsonStr);
                console.log('Successfully parsed extracted JSON:', data);
                return data;
            } catch (error) {
                console.error('Error parsing extracted JSON:', error);
                return { error: 'Error decoding JSON' };
            }
        } else {
            console.log('No JSON found in response');
            return { error: 'Could not extract JSON' };
        }
    } catch (error) {
        console.error('Error in extractJsonFromResponse:', error);
        return { error: `Error: ${error.message}` };
    }
}

// WebSocket connection event
const clientIntervals = new Map();
// WebSocket connection event
io.on('connection', (socket) => {
    console.log(`Client connected: ${socket.id}`);

    let oldFrame = null;
    let intervalId = null;

    socket.on('frame', (data) => {
        if (!data) {
            socket.emit('error', { error: 'Frame data required' });
            return;
        }

        // Ensure data is in base64 format
        const base64Image = typeof data === 'string' ? data : base64.fromByteArray(data);
        oldFrame = base64Image;  // Update the old frame with the new one
    });

    socket.on('disconnect', () => {
        console.log(`Client disconnected: ${socket.id}`);

        // Clear the interval for this client when they disconnect
        if (intervalId) {
            clearInterval(intervalId);
            clientIntervals.delete(socket.id);  // Remove the client's interval from the map
        }
    });

    // Start the interval for this client
    if (!clientIntervals.has(socket.id)) {
        intervalId = setInterval(() => {
            if (oldFrame) {
                // Send a message with the last part of the frame and a sample result
                // console.log(oldFrame.slice(-10));
                // const message = {
                //     name: 'Sandwich',
                //     carbs: '40',
                //     proteins: '10',
                //     fats: '15',
                //     'weight-reading': '150'
                // };
                // console.log('Result:', 'message sent');
                // socket.emit('update', { Result: message });

                // Optionally, you can call your AI analysis function here
                analyzeFrameWithOpenAI(oldFrame).then((result) => {
                    console.log('Result:', result);
                    socket.emit('update', { 'Result': result });
                });
            }
        }, 10000);  // Every 2 seconds

        // Store the interval ID for this client
        clientIntervals.set(socket.id, intervalId);
    }
});


// make a get endpoint to get advice from gpt-4 model

app.post('/advice', async (req, res) => {
    text = req.body
    try {
        const response = await openai.chat.completions.create({
            model: 'gpt-4o-mini',
            messages: [
                {
                    role: 'user',
                    content: [
                        {
                            type: 'text',
                            text: `
                            I need some advice on ${JSON.stringify(text)}. Can you provide me with some health advice based on the item I am about to consume.
                            Also get me the list ingredients that is on my plate. Here is how I want the JSON to be structured:
                            {
                                "advice": (1 sentence max),
                                "ingredients": (list) 
                            }
                            `
                        },
                    ],
                },
            ],
            max_tokens: 300,
        });

        const result = await extractJsonFromResponse(response);
        console.log('Response:', result);
        res.json(result);
    } catch (error) {
        console.error('Error getting advice:', error.message);
        res.json({ error: error.message });
    }
}
);

app.post('/api/tts', async (req, res) => {
    try {
        const { text } = req.body;

        if (!text) {
            return res.status(400).json({ 
                error: "Text is required" 
            });
        }

       const ELEVEN_LABS_API_KEY = process.env.ELEVENLABS_API_KEY
        const VOICE_ID = "D38z5RcWu1voky8WS1ja" // owl sound

        if (!ELEVEN_LABS_API_KEY || !VOICE_ID) {
            return res.status(500).json({ 
                error: "Missing API configuration" 
            });
        }

        const response = await axios({
            method: 'POST',
            url: `https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`,
            headers: {
                'xi-api-key': ELEVEN_LABS_API_KEY,
                'Content-Type': 'application/json',
            },
            data: {
                text,
                voice_settings: {
                    stability: 0.75,
                    similarity_boost: 0.75
                }
            },
            responseType: 'arraybuffer'
        });

        // Convert audio buffer to base64 and properly format it
        const audioBase64 = Buffer.from(response.data).toString('base64');
        
        res.json({ 
            audioContent: audioBase64,
            format: 'audio/mpeg'  // or whatever format Eleven Labs returns
        });

    } catch (error) {
        console.error('TTS Error:', error);
        res.status(500).json({ 
            error: "Failed to generate speech",
            details: error.message 
        });
    }
});

app.post('/api/tts/Tusk', async (req, res) => {
    try {
        const { text } = req.body;

        if (!text) {
            return res.status(400).json({ 
                error: "Text is required" 
            });
        }

       const ELEVEN_LABS_API_KEY = process.env.ELEVENLABS_API_KEY
        const VOICE_ID = "pNInz6obpgDQGcFmaJgB"

        if (!ELEVEN_LABS_API_KEY || !VOICE_ID) {
            return res.status(500).json({ 
                error: "Missing API configuration" 
            });
        }

        const response = await axios({
            method: 'POST',
            url: `https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`,
            headers: {
                'xi-api-key': ELEVEN_LABS_API_KEY,
                'Content-Type': 'application/json',
            },
            data: {
                text,
                voice_settings: {
                    stability: 0.75,
                    similarity_boost: 0.75
                }
            },
            responseType: 'arraybuffer'
        });

        // Convert audio buffer to base64 and properly format it
        const audioBase64 = Buffer.from(response.data).toString('base64');
        
        res.json({ 
            audioContent: audioBase64,
            format: 'audio/mpeg'  // or whatever format Eleven Labs returns
        });

    } catch (error) {
        console.error('TTS Error:', error);
        res.status(500).json({ 
            error: "Failed to generate speech",
            details: error.message 
        });
    }
});

app.post('/api/tts/Lion', async (req, res) => {
    try {
        const { text } = req.body;

        if (!text) {
            return res.status(400).json({ 
                error: "Text is required" 
            });
        }

       const ELEVEN_LABS_API_KEY = process.env.ELEVENLABS_API_KEY
        const VOICE_ID = "pqHfZKP75CvOlQylNhV4"

        if (!ELEVEN_LABS_API_KEY || !VOICE_ID) {
            return res.status(500).json({ 
                error: "Missing API configuration" 
            });
        }

        const response = await axios({
            method: 'POST',
            url: `https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`,
            headers: {
                'xi-api-key': ELEVEN_LABS_API_KEY,
                'Content-Type': 'application/json',
            },
            data: {
                text,
                voice_settings: {
                    stability: 0.75,
                    similarity_boost: 0.75
                }
            },
            responseType: 'arraybuffer'
        });

        // Convert audio buffer to base64 and properly format it
        const audioBase64 = Buffer.from(response.data).toString('base64');
        
        res.json({ 
            audioContent: audioBase64,
            format: 'audio/mpeg'  // or whatever format Eleven Labs returns
        });

    } catch (error) {
        console.error('TTS Error:', error);
        res.status(500).json({ 
            error: "Failed to generate speech",
            details: error.message 
        });
    }
});

// Start the server
const PORT = 3001;
server.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});