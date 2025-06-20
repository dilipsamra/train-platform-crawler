export interface TrainService {
  scheduled_time: string;
  expected_time: string;
  platform?: string;
  operator: string;
  destination: string;
  origin: string;
  service_id: string;
  status?: string;
}
