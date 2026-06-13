import JoyRide from 'react-joyride';

const steps = [
  { target: '.sidebar', content: 'This is the main navigation menu. Use it to switch between pages.' },
  { target: '.predict-form', content: 'Fill in isolate data here to get MDR prediction.' },
  { target: '.result-card', content: 'Results will appear here with SHAP explanation.' },
];

export default function Tour({ run, onFinish }) {
  return <JoyRide steps={steps} continuous run={run} showSkipButton styles={{ options: { zIndex: 10000 } }} callback={(data) => { if (data.status === 'finished' || data.status === 'skipped') onFinish(); }} />;
}
