import axios from 'axios';
import { TrainService } from '../types';

export const fetchArrivals = async (crs: string): Promise<TrainService[]> => {
  const res = await axios.get(`/station/${crs}/arrivals`);
  return res.data;
};

export const fetchDepartures = async (crs: string): Promise<TrainService[]> => {
  const res = await axios.get(`/station/${crs}/departures`);
  return res.data;
};
