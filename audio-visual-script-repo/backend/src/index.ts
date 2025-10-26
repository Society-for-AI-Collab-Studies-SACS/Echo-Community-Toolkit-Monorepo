import express from 'express';

const app = express();
const port = process.env.PORT || 4000;

app.use(express.json());

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', message: 'Audio-Visual Script Repository backend scaffold ready.' });
});

app.listen(port, () => {
  console.log(`Backend listening on http://localhost:${port}`);
});
