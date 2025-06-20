import React from 'react';
import { TrainService } from '../types';

type Props = {
  services: TrainService[];
  title: string;
};

const ServiceList: React.FC<Props> = ({ services, title }) => (
  <div>
    <h2>{title}</h2>
    <ul>
      {services.map((s, i) => (
        <li key={i}>
          {s.scheduled_time} (exp: {s.expected_time}) - {s.origin} → {s.destination} | Platform: {s.platform} | {s.operator} | {s.status}
        </li>
      ))}
    </ul>
  </div>
);

export default ServiceList;
