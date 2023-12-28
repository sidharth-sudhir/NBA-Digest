import React, { useEffect, useState } from 'react';
import axios from 'axios';

function ScoresComponent() {
  const [scores, setScores] = useState([]);

  useEffect(() => {
    axios.get('http://127.0.0.1:5000/api/scores') // Fetch data from backend endpoint
      .then(response => {
        setScores(response.data); // Set fetched data to state
      })
      .catch(error => {
        console.error('Error fetching data:', error);
      });
  }, []);

  return (
    <div>
      <h2>Scores</h2>
      <ul>
        {scores.map(score => (
          <li key={score.id}>
            {score.homeTeam} {score.homeScore} - {score.awayScore} {score.awayTeam}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ScoresComponent;
