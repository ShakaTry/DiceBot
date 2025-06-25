export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'POST') {
    try {
      const body = req.body || {};
      
      // Slack slash command format
      if (body.command) {
        return res.status(200).json({
          response_type: "in_channel",
          text: `✅ Command received: ${body.command}`,
          attachments: [{
            color: "good",
            text: `User: ${body.user_name}\nChannel: ${body.channel_name}\nText: ${body.text || 'none'}`
          }]
        });
      }

      return res.status(200).json({
        message: "Node.js Slack endpoint working!",
        received: body,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      return res.status(500).json({
        error: error.message,
        message: "Error processing request"
      });
    }
  }

  return res.status(200).json({
    message: "Slack endpoint ready",
    methods: ["POST"],
    status: "ok"
  });
}
