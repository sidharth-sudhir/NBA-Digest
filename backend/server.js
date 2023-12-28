const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());


// Sample mock data
const mockScores = [
  { id: 1, homeTeam: 'Team A', awayTeam: 'Team B', homeScore: 102, awayScore: 98 },
  { id: 2, homeTeam: 'Team C', awayTeam: 'Team D', homeScore: 115, awayScore: 110 },
  // ...more sample data
];

// Express route to serve mock scores data
app.get('/api/scores', (req, res) => {
  res.json(mockScores);
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});