export default function handler(req, res) {
  res.status(200).json({
    message: "Hello from Node.js!",
    status: "working",
    vercel: true,
    method: req.method,
    timestamp: new Date().toISOString()
  });
}
