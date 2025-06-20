import React, { useState } from 'react';
import axios from 'axios';

interface TrainService {
  scheduled_time: string;
  expected_time: string;
  platform?: string;
  operator: string;
  destination: string;
  origin: string;
  service_id: string;
  status?: string;
}

const App: React.FC = () => {
  const [station, setStation] = useState('London Euston');
  const [crs, setCrs] = useState('EUS');
  const [arrivals, setArrivals] = useState<TrainService[]>([]);
  const [departures, setDepartures] = useState<TrainService[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const arr = await axios.get(`/station/${crs}/arrivals`);
      const dep = await axios.get(`/station/${crs}/departures`);
      setArrivals(arr.data);
      setDepartures(dep.data);
    } catch (e: any) {
      setError('Failed to fetch train data');
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 600, margin: 'auto', padding: 20 }}>
      <h1>Train Platform Crawler</h1>
      <input
        value={station}
        onChange={e => setStation(e.target.value)}
        placeholder="Enter station name (e.g. London Euston)"
        style={{ width: '70%', marginRight: 8 }}
      />
      <button onClick={() => { setCrs('EUS'); fetchData(); }}>Search</button>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <h2>Arrivals</h2>
      <ul>
        {arrivals.map((s, i) => (
          <li key={i}>
            {s.scheduled_time} (exp: {s.expected_time}) - {s.origin} → {s.destination} | Platform: {s.platform} | {s.operator} | {s.status}
          </li>
        ))}
      </ul>
      <h2>Departures</h2>
      <ul>
        {departures.map((s, i) => (
          <li key={i}>
            {s.scheduled_time} (exp: {s.expected_time}) - {s.origin} → {s.destination} | Platform: {s.platform} | {s.operator} | {s.status}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default App;
