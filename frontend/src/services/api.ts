import axios from 'axios';
import { TrainService } from '../types';

// Use POST endpoints for better validation and extensibility
export const fetchArrivals = async (crs: string): Promise<TrainService[]> => {
  const res = await axios.post('/station/arrivals', { crs_code: crs });
  return res.data;
};

export const fetchDepartures = async (crs: string): Promise<TrainService[]> => {
  const res = await axios.post('/station/departures', { crs_code: crs });
  return res.data;
};
