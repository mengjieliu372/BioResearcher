import React from 'react';

const ReportSection = ({ part, steps }) => {
  return (
    <div>
      <h2>{part}</h2>
      {steps.map((step, index) => (
        <div key={index}>
          <h3>{step.title}</h3>
          <p>{step.details}</p>
          {step.references && (
            <div>
              <strong>Reference Source:</strong>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default ReportSection;
